from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from api.deps import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_llm_client,
    get_operation_store,
    load_seed,
    parse_refresh_request,
    prop,
)
from config import Settings, get_settings
from models.auth import RefreshRequest, TokenResponse, UserPublic
from services.llm_client import LLMClient

router = APIRouter(tags=["auth", "copilot"])


class ChatRequest(BaseModel):
    message: str
    parcelId: str | None = None
    sessionId: str | None = None
    language: str = "es"


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    settings_obj: Settings = Depends(get_settings),
) -> TokenResponse:
    user = authenticate_user(settings_obj, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token(settings_obj, user.username, user.roles)
    refresh = create_refresh_token(settings_obj, user.username, user.roles)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings_obj.jwt_access_ttl_min * 60,
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    settings_obj: Settings = Depends(get_settings),
    user: UserPublic = Depends(parse_refresh_request),
) -> TokenResponse:
    access = create_access_token(settings_obj, user.username, user.roles)
    refresh = create_refresh_token(settings_obj, user.username, user.roles)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings_obj.jwt_access_ttl_min * 60,
    )


@router.post("/copilot/chat")
async def copilot_chat(
    body: ChatRequest,
    _: UserPublic = Depends(get_current_user),
    llm_client: LLMClient = Depends(get_llm_client),
    operation_store: list[dict[str, Any]] = Depends(get_operation_store),
) -> dict[str, Any]:
    settings_obj = get_settings()
    parcel_context: dict[str, Any] = {}
    weather_context: dict[str, Any] = {}

    if body.parcelId:
        parcel = next((item for item in load_seed(settings_obj, "seed_parcels.json") if item["id"] == body.parcelId), None)
        if parcel is None:
            raise HTTPException(status_code=404, detail="Parcel not found")

        soil_id = prop(parcel, "hasAgriSoil")
        soil = next((item for item in load_seed(settings_obj, "seed_soils.json") if item["id"] == soil_id), None)
        parcel_ops = [item for item in operation_store if prop(item, "refParcel") == body.parcelId]
        parcel_ops.sort(key=lambda item: prop(item, "startedAt") or "", reverse=True)

        weather_seed = load_seed(settings_obj, "seed_weather_observed.json")
        weather_context = weather_seed[-1] if weather_seed else {}

        parcel_context = {
            "parcel": parcel,
            "soil": soil,
            "lastOperations": parcel_ops[:5],
        }

    prompt_payload = {
        "message": body.message,
        "language": body.language,
        "sessionId": body.sessionId,
        "context": {
            "parcel": parcel_context,
            "weather": weather_context,
        },
    }
    llm_result = await llm_client.chat(prompt_payload)

    return {
        "answer": llm_result.get("answer"),
        "references": llm_result.get("references", ["parcel", "weather", "operations"]),
        "followUps": llm_result.get("followUps", []),
    }
