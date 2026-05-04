from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_current_user, get_ml_client, load_seed, prop
from config import get_settings
from models.auth import UserPublic
from services.ml_client import MLClient

router = APIRouter(prefix="/simulator", tags=["simulator"])


class WhatIfScenario(BaseModel):
    cropId: str
    sowingDate: str
    irrigationMm: float


class WhatIfRequest(BaseModel):
    parcelId: str
    scenarios: list[WhatIfScenario]


@router.post("/whatif")
async def run_whatif(
    body: WhatIfRequest,
    _: UserPublic = Depends(get_current_user),
    ml_client: MLClient = Depends(get_ml_client),
) -> dict[str, Any]:
    settings_obj = get_settings()
    parcel = next((item for item in load_seed(settings_obj, "seed_parcels.json") if item["id"] == body.parcelId), None)
    if parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")

    baseline = await ml_client.simulate(
        {
            "parcel": {
                "id": body.parcelId,
                "status": prop(parcel, "parcelStatus"),
                "currentCrop": prop(parcel, "hasAgriCrop"),
            },
            "scenario": {"cropId": prop(parcel, "hasAgriCrop"), "irrigationMm": 0, "sowingDate": None},
        }
    )

    scenario_results = []
    for scenario in body.scenarios:
        prediction = await ml_client.simulate(
            {
                "parcel": {"id": body.parcelId, "status": prop(parcel, "parcelStatus")},
                "scenario": scenario.model_dump(),
            }
        )
        scenario_results.append(
            {
                "scenario": scenario.model_dump(),
                "prediction": prediction,
            }
        )

    best = max(
        scenario_results,
        key=lambda item: item["prediction"].get("yieldIndex", 0),
        default=None,
    )

    recommendation = best["scenario"] if best else None

    return {
        "baseline": baseline,
        "scenarios": scenario_results,
        "recommendation": recommendation,
    }
