from __future__ import annotations

from datetime import UTC, datetime

from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from api.deps import (
    get_current_user,
    get_orion,
    get_quantumleap,
    get_redis_cache,
    load_seed,
    prop,
)
from config import get_settings
from db.redis_cache import RedisCache
from models.auth import UserPublic
from models.parcel import SuitabilityResponse
from services.ml_client import MLClient
from services.orion import OrionClient
from services.quantumleap import QuantumLeapClient

router = APIRouter(prefix="/parcels", tags=["suitability"])


@router.get("/{parcel_id}/suitability")
async def get_suitability(
    parcel_id: str,
    _: UserPublic = Depends(get_current_user),
    orion: OrionClient = Depends(get_orion),
    ql: QuantumLeapClient = Depends(get_quantumleap),
    cache: RedisCache = Depends(get_redis_cache),
) -> SuitabilityResponse:
    settings_obj = get_settings()
    cache_key = f"suitability:{parcel_id}"
    cached = await cache.get_json(cache_key)
    if cached:
        return SuitabilityResponse(**cached)

    try:
        parcel = await orion.get_entity(parcel_id, "AgriParcel")
    except Exception:
        # Orion not available — fallback to seed data so the demo works without Orion
        seed = load_seed(settings_obj, "seed_parcels.json")
        parcel = next((p for p in seed if p.get("id") == parcel_id), None)
        if parcel is None:
            # As a last-resort fallback (containers sometimes lack seed files), provide
            # a tiny embedded dataset for three demo parcels so we can test scoring.
            FALLBACK = {
                "urn:ngsi-ld:AgriParcel:farm001:parcel01": {
                    "id": "urn:ngsi-ld:AgriParcel:farm001:parcel01",
                    "area": 1.12,
                    "pendiente_media": 20,
                    "altitud": 50,
                    "uso_sigpac": "TI",
                    "coef_regadio": 0,
                },
                "urn:ngsi-ld:AgriParcel:farm001:parcel03": {
                    "id": "urn:ngsi-ld:AgriParcel:farm001:parcel03",
                    "area": 3.96,
                    "pendiente_media": 400,
                    "altitud": 120,
                    "uso_sigpac": "TI",
                    "coef_regadio": 0,
                },
                "urn:ngsi-ld:AgriParcel:urban:zu001": {
                    "id": "urn:ngsi-ld:AgriParcel:urban:zu001",
                    "area": 0.12,
                    "pendiente_media": 5,
                    "altitud": 30,
                    "uso_sigpac": "ZU",
                    "coef_regadio": 0,
                },
            }
            parcel = FALLBACK.get(parcel_id)
            if parcel is None:
                raise HTTPException(status_code=404, detail=f"Parcel {parcel_id} not found. Load data first: ./scripts/load_seed_data.sh")

    # --- Read sigpac-like properties from the parcel entity ---
    pendiente_tenths = prop(parcel, "pendiente_media")
    # pendiente_media stored in tenths of percent per SIGPAC; divide by 10 to get %
    pendiente_pct = None
    try:
        if pendiente_tenths is not None:
            pendiente_pct = float(pendiente_tenths) / 10.0
    except Exception:
        pendiente_pct = None

    dn_surface = prop(parcel, "dn_surface") or prop(parcel, "area")
    uso_sigpac = (prop(parcel, "uso_sigpac") or prop(parcel, "landUse") or "").upper()
    altitud = prop(parcel, "altitud")
    coef_regadio = prop(parcel, "coef_regadio")

    # Exclusion filter: urban / edific / infra / agua / camino (codes provided)
    EXCLUDE_CODES = {"ZU", "ED", "IM", "AG", "CA"}
    if uso_sigpac and uso_sigpac in EXCLUDE_CODES:
        payload = {"parcelId": parcel_id, "generatedAt": datetime.now(UTC).isoformat(), "ranking": [], "excludedReason": "Parcela non apta para cultivo (uso SIGPAC)"}
        await cache.set_json(cache_key, payload, settings_obj.suitability_cache_ttl_seconds)
        return payload

    # --- Define crop rules (explicit constants) ---
    # Each entry: cropId (last segment used for UI), pendiente_max_pct, regadio, meses_siembra (list or None), altitud_max_m
    RULES = [
        {"cropId": "urn:ngsi-ld:AgriCrop:catalog:millo", "pendiente_max": 15.0, "regadio": "recomendable", "months": [4, 5], "alt_max": 600},
        {"cropId": "urn:ngsi-ld:AgriCrop:catalog:pataca", "pendiente_max": 20.0, "regadio": "opcional", "months": [3, 4, 5], "alt_max": 900},
        {"cropId": "urn:ngsi-ld:AgriCrop:catalog:trigo", "pendiente_max": 25.0, "regadio": "no", "months": [10, 11], "alt_max": 800},
        {"cropId": "urn:ngsi-ld:AgriCrop:catalog:centeo", "pendiente_max": 35.0, "regadio": "no", "months": [10, 11], "alt_max": 1000},
        {"cropId": "urn:ngsi-ld:AgriCrop:catalog:prado", "pendiente_max": 45.0, "regadio": "no", "months": None, "alt_max": 1100},
        {"cropId": "urn:ngsi-ld:AgriCrop:catalog:viñedo", "pendiente_max": 30.0, "regadio": "no", "months": None, "alt_max": 700},
        {"cropId": "urn:ngsi-ld:AgriCrop:catalog:castano", "pendiente_max": 50.0, "regadio": "no", "months": None, "alt_max": 1000},
        {"cropId": "urn:ngsi-ld:AgriCrop:catalog:horta", "pendiente_max": 10.0, "regadio": "necesario", "months": [3, 4, 5, 6], "alt_max": 600},
        {"cropId": "urn:ngsi-ld:AgriCrop:catalog:frutales", "pendiente_max": 20.0, "regadio": "recomendable", "months": [1, 2, 3], "alt_max": 700},
        {"cropId": "urn:ngsi-ld:AgriCrop:catalog:pemento", "pendiente_max": 12.0, "regadio": "necesario", "months": [3, 4, 5], "alt_max": 500},
    ]

    # Scoring weights (constants): pendiente 40%, regadio 25%, mes 20%, altitud 15%
    W_PEND = 0.40
    W_REG = 0.25
    W_MES = 0.20
    W_ALT = 0.15

    from datetime import datetime as _dt
    now_month = _dt.now().month

    def clamp01(v: float) -> float:
        return max(0.0, min(1.0, v))

    items: list[dict] = []
    for rule in RULES:
        reasons: dict[str, str] = {}

        # pendiente
        if pendiente_pct is None:
            pend_score = 0.5
            reasons["pendiente"] = "Pendiente descoñecida"
        else:
            maxp = float(rule["pendiente_max"])
            if pendiente_pct <= maxp:
                pend_score = 1.0
                reasons["pendiente"] = f"Pendiente {pendiente_pct:.1f}% <= {maxp}%"
            else:
                # linear decay: at pendiente = maxp -> 1.0, at pendiente = 2*maxp -> 0.0
                pend_score = clamp01(1.0 - (pendiente_pct - maxp) / maxp)
                reasons["pendiente"] = f"Pendiente {pendiente_pct:.1f}% > {maxp}%"

        # regadío
        reg_need = (rule.get("regadio") or "no").lower()
        has_irrig = False
        try:
            has_irrig = (coef_regadio is not None) and (float(coef_regadio) > 0)
        except Exception:
            has_irrig = False

        if reg_need == "necesario":
            if not has_irrig:
                reg_score = 0.0
                reasons["regadio"] = "Riego necesario pero non dispoñible"
            else:
                reg_score = 1.0
                reasons["regadio"] = "Riego dispoñible"
        elif reg_need == "recomendable":
            if not has_irrig:
                reg_score = 0.6
                reasons["regadio"] = "Riego recomendable pero non dispoñible"
            else:
                reg_score = 1.0
                reasons["regadio"] = "Riego dispoñible"
        else:  # no / opcional
            reg_score = 1.0
            reasons["regadio"] = "Riego non necesario"

        # mes de siembra
        months = rule.get("months")
        if months is None:
            mes_score = 1.0
            reasons["mes"] = "Cultivo perenne (sen ventana)"
        else:
            if now_month in months:
                mes_score = 1.0
                reasons["mes"] = f"Mes {now_month} dentro da ventá"
            else:
                mes_score = 0.0
                reasons["mes"] = f"Mes {now_month} fora da ventá"

        # altitud
        if altitud is None:
            alt_score = 0.5
            reasons["altitude"] = "Altitud descoñecida"
        else:
            if float(altitud) <= float(rule.get("alt_max", 99999)):
                alt_score = 1.0
                reasons["altitude"] = f"Altitud {altitud}m <= {rule.get('alt_max')}m"
            else:
                maxa = float(rule.get("alt_max", 99999))
                alt_score = clamp01(1.0 - (float(altitud) - maxa) / maxa)
                reasons["altitude"] = f"Altitud {altitud}m > {maxa}m"

        # final weighted score
        total = (pend_score * W_PEND) + (reg_score * W_REG) + (mes_score * W_MES) + (alt_score * W_ALT)
        score_pct = clamp01(total) * 100.0

        items.append({
            "cropId": rule["cropId"],
            "score": round(score_pct, 1),
            "band": "green" if score_pct >= 70 else ("yellow" if score_pct >= 40 else "red"),
            "breakdown": reasons,
        })

    items_sorted = sorted(items, key=lambda x: x["score"], reverse=True)

    result = SuitabilityResponse(parcelId=parcel_id, generatedAt=datetime.now(UTC).isoformat(), ranking=items_sorted)
    # cache plain model_dump (without excludedReason)
    await cache.set_json(cache_key, result.model_dump(), settings_obj.suitability_cache_ttl_seconds)
    return result
