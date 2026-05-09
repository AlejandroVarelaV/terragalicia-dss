from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="TerraGalicia ML Scorer")


CROP_REQUIREMENTS = {
  "millo": {
    "ph_min": 5.5, "ph_max": 7.0, "ph_optimal": 6.2,
    "temp_min_growth": 10.0, "temp_base": 10.0,
    "gdd_required": 1400,
    "rainfall_min_mm": 450, "rainfall_optimal_mm": 600,
    "soil_textures_ok": ["loam","clay_loam","silt_loam"],
    "frost_sensitive": True, "frost_lethal_temp": -2.0,
    "planting_window": {"start_month": 4, "end_month": 5},
    "yield_potential_tha": 8.5
  },
  "pataca": {
    "ph_min": 4.8, "ph_max": 6.5, "ph_optimal": 5.5,
    "temp_min_growth": 7.0, "temp_base": 5.0,
    "gdd_required": 1200,
    "rainfall_min_mm": 500, "rainfall_optimal_mm": 700,
    "soil_textures_ok": ["sandy_loam","loam","silt_loam"],
    "frost_sensitive": True, "frost_lethal_temp": -1.0,
    "planting_window": {"start_month": 3, "end_month": 5},
    "yield_potential_tha": 25.0
  },
  "kiwi": {
    "ph_min": 5.0, "ph_max": 6.5, "ph_optimal": 6.0,
    "temp_min_growth": 10.0, "temp_base": 10.0,
    "gdd_required": 2200,
    "rainfall_min_mm": 800, "rainfall_optimal_mm": 1200,
    "soil_textures_ok": ["loam","clay_loam"],
    "frost_sensitive": True, "frost_lethal_temp": -1.5,
    "planting_window": {"start_month": 3, "end_month": 4},
    "yield_potential_tha": 20.0
  },
  "albarino": {
    "ph_min": 5.5, "ph_max": 7.5, "ph_optimal": 6.5,
    "temp_min_growth": 10.0, "temp_base": 10.0,
    "gdd_required": 1800,
    "rainfall_min_mm": 600, "rainfall_optimal_mm": 900,
    "soil_textures_ok": ["sandy_loam","loam","granite_grus"],
    "frost_sensitive": True, "frost_lethal_temp": -2.0,
    "planting_window": {"start_month": 3, "end_month": 4},
    "yield_potential_tha": 8.0
  },
  "mencia": {
    "ph_min": 5.5, "ph_max": 7.0, "ph_optimal": 6.3,
    "temp_min_growth": 10.0, "temp_base": 10.0,
    "gdd_required": 1900,
    "rainfall_min_mm": 550, "rainfall_optimal_mm": 800,
    "soil_textures_ok": ["loam","clay_loam","slate"],
    "frost_sensitive": True, "frost_lethal_temp": -2.5,
    "planting_window": {"start_month": 3, "end_month": 4},
    "yield_potential_tha": 7.0
  },
  "grelos": {
    "ph_min": 5.5, "ph_max": 7.5, "ph_optimal": 6.5,
    "temp_min_growth": 5.0, "temp_base": 5.0,
    "gdd_required": 600,
    "rainfall_min_mm": 300, "rainfall_optimal_mm": 500,
    "soil_textures_ok": ["loam","clay_loam","silt_loam"],
    "frost_sensitive": False, "frost_lethal_temp": -8.0,
    "planting_window": {"start_month": 8, "end_month": 10},
    "yield_potential_tha": 15.0
  },
  "trigo": {
    "ph_min": 5.5, "ph_max": 7.5, "ph_optimal": 6.5,
    "temp_min_growth": 3.0, "temp_base": 0.0,
    "gdd_required": 1700,
    "rainfall_min_mm": 350, "rainfall_optimal_mm": 500,
    "soil_textures_ok": ["loam","clay_loam","silt_loam"],
    "frost_sensitive": False, "frost_lethal_temp": -15.0,
    "planting_window": {"start_month": 10, "end_month": 12},
    "yield_potential_tha": 5.0
  },
  "centeo": {
    "ph_min": 4.5, "ph_max": 7.0, "ph_optimal": 5.5,
    "temp_min_growth": 3.0, "temp_base": 0.0,
    "gdd_required": 1500,
    "rainfall_min_mm": 300, "rainfall_optimal_mm": 450,
    "soil_textures_ok": ["sandy_loam","loam","sandy"],
    "frost_sensitive": False, "frost_lethal_temp": -18.0,
    "planting_window": {"start_month": 10, "end_month": 11},
    "yield_potential_tha": 3.5
  }
}


class ScoreRequest(BaseModel):
    crop_id: str
    soil_ph: float
    soil_texture: str
    annual_rainfall_mm: float
    frost_days: int
    sowing_month: int


class ComponentBreakdown(BaseModel):
    score: float
    penalty: float
    measured: Any | None = None
    optimal_range: Any | None = None


class ScoreResponse(BaseModel):
    cropId: str
    score: int
    colorBand: str
    breakdown: Dict[str, Any]
    explanation_data: Dict[str, Any]


class SuitabilityRequest(BaseModel):
    parcel: Dict[str, Any] | None = None
    soil: Dict[str, Any] | None = None
    weather: list[Dict[str, Any]] | None = None
    crop_ids: list[str] | None = None


def _color_band(score: float) -> str:
    if score >= 70:
        return "green"
    if score >= 40:
        return "yellow"
    return "red"


def _score_crop(crop_id: str, soil_ph: float, soil_texture: str, annual_rainfall_mm: float, frost_days: int, sowing_month: int) -> dict[str, Any]:
    if crop_id not in CROP_REQUIREMENTS:
        raise HTTPException(status_code=400, detail="Unknown crop_id")
    rules = CROP_REQUIREMENTS[crop_id]

    penalties: dict[str, float] = {}

    ph_min = rules["ph_min"]
    ph_max = rules["ph_max"]
    ph_opt = rules["ph_optimal"]
    if soil_ph < ph_min or soil_ph > ph_max:
        ph_penalty = 25.0
    else:
        max_dev = max(ph_opt - ph_min, ph_max - ph_opt)
        dev = abs(soil_ph - ph_opt)
        ph_penalty = (dev / max_dev) * 15.0 if max_dev > 0 else 0.0
    penalties["ph"] = min(25.0, ph_penalty)

    rain_min = rules["rainfall_min_mm"]
    rain_opt = rules["rainfall_optimal_mm"]
    if annual_rainfall_mm < rain_min:
        rain_penalty = (1.0 - (annual_rainfall_mm / rain_min)) * 25.0
    else:
        rain_penalty = 0.0
    penalties["rainfall"] = min(25.0, rain_penalty)

    frost_sensitive = bool(rules.get("frost_sensitive", False))
    if frost_sensitive and frost_days > 0:
        frost_penalty = min(30.0, frost_days * 10.0)
    elif frost_days > 3:
        frost_penalty = min(30.0, frost_days * 5.0)
    else:
        frost_penalty = 0.0
    penalties["frost_risk"] = frost_penalty

    texture_ok = rules.get("soil_textures_ok", [])
    penalties["soil_texture"] = 0.0 if soil_texture in texture_ok else 10.0

    pw = rules.get("planting_window", {})
    start_m = int(pw.get("start_month", 1))
    end_m = int(pw.get("end_month", 12))
    sow = int(sowing_month)
    if start_m <= end_m:
        in_window = start_m <= sow <= end_m
    else:
        in_window = sow >= start_m or sow <= end_m
    if in_window:
        pw_penalty = 0.0
    else:
        if sow < start_m:
            months_off = start_m - sow
        elif sow > end_m:
            months_off = sow - end_m
        else:
            months_off = 0
        pw_penalty = min(10.0, months_off * 3.0)
    penalties["planting_window"] = pw_penalty

    total_penalty = sum(penalties.values())
    final_score = max(0.0, min(100.0, 100.0 - total_penalty))

    breakdown = {
        "ph": {
            "score": round(25.0 - penalties["ph"], 2),
            "penalty": round(penalties["ph"], 2),
            "measured": soil_ph,
            "optimal_range": [ph_min, ph_max],
        },
        "rainfall": {
            "score": round(25.0 - penalties["rainfall"], 2),
            "penalty": round(penalties["rainfall"], 2),
            "measured": annual_rainfall_mm,
            "optimal_range": [rain_min, rain_opt],
        },
        "frost_risk": {
            "score": round(30.0 - penalties["frost_risk"], 2),
            "penalty": round(penalties["frost_risk"], 2),
            "frost_days": frost_days,
        },
        "soil_texture": {
            "score": round(10.0 - penalties["soil_texture"], 2),
            "penalty": round(penalties["soil_texture"], 2),
            "measured": soil_texture,
            "allowed": texture_ok,
        },
        "planting_window": {
            "score": round(10.0 - penalties["planting_window"], 2),
            "penalty": round(penalties["planting_window"], 2),
            "sowing_month": sow,
            "window": [start_m, end_m],
        },
    }

    return {
        "cropId": crop_id,
        "score": int(round(final_score)),
        "colorBand": _color_band(final_score),
        "breakdown": breakdown,
        "explanation_data": {
            "key_factor": max(penalties.items(), key=lambda kv: kv[1])[0],
            "soil_ph_measured": soil_ph,
            "annual_rainfall_mm": annual_rainfall_mm,
            "frost_days": frost_days,
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ml-scorer"}


@app.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest) -> ScoreResponse:
    data = _score_crop(
        req.crop_id,
        req.soil_ph,
        req.soil_texture,
        req.annual_rainfall_mm,
        req.frost_days,
        req.sowing_month,
    )
    return ScoreResponse(**data)


@app.post("/suitability")
def suitability(req: SuitabilityRequest) -> dict[str, Any]:
    soil = req.soil or {}
    weather = req.weather or []
    crop_ids = req.crop_ids or list(CROP_REQUIREMENTS.keys())

    soil_ph = float(soil.get("pH", 5.8) or 5.8)
    soil_texture = str(soil.get("texture", "loam") or "loam")
    annual_rainfall_mm = 600.0
    if weather:
        rain_values = [float(item.get("precipitation", 0) or 0) for item in weather]
        annual_rainfall_mm = max(sum(rain_values), annual_rainfall_mm)
    frost_days = sum(1 for item in weather if float(item.get("temperature", 10) or 10) < 0)
    sowing_month = datetime.now().month

    scores = []
    for crop_id in crop_ids:
        scored = _score_crop(crop_id, soil_ph, soil_texture, annual_rainfall_mm, frost_days, sowing_month)
        scores.append({
            "cropId": scored["cropId"],
            "score": scored["score"] / 100.0,
            "band": scored["colorBand"],
            "breakdown": scored["breakdown"],
        })

    scores.sort(key=lambda item: item["score"], reverse=True)
    return {"scores": scores}
