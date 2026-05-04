from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any, Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from config import Settings, get_settings
from models.auth import RefreshRequest, Role, UserPublic
from services.llm_client import LLMClient
from services.ml_client import MLClient
from services.orion import OrionClient
from services.quantumleap import QuantumLeapClient
from services.weather_fetcher import WeatherFetcher

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def prop(entity: dict[str, Any], field: str, default: Any = None) -> Any:
    value = entity.get(field, default)
    if isinstance(value, dict):
        if "value" in value:
            return value["value"]
        if "object" in value:
            return value["object"]
    return value


def load_seed(settings_obj: Settings, filename: str) -> list[dict[str, Any]]:
    path = settings_obj.seed_data_dir / filename
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache
def _users_from_settings(raw_json: str) -> dict[str, dict[str, Any]]:
    data = json.loads(raw_json)
    users: dict[str, dict[str, Any]] = {}
    for username, user_data in data.items():
        users[username] = {
            "username": username,
            "password": user_data["password"],
            "roles": user_data.get("roles", []),
        }
    return users


def authenticate_user(settings_obj: Settings, username: str, password: str) -> UserPublic | None:
    users = _users_from_settings(settings_obj.auth_demo_users_json)
    user = users.get(username)
    if user is None:
        return None
    if user["password"] != password:
        return None
    return UserPublic(username=username, roles=user["roles"])


def _create_token(*, settings_obj: Settings, username: str, roles: list[Role], token_type: str, expires_delta: timedelta) -> str:
    expire = datetime.now(UTC) + expires_delta
    payload = {
        "sub": username,
        "roles": roles,
        "token_type": token_type,
        "exp": int(expire.timestamp()),
    }
    secret = settings_obj.jwt_secret_key if token_type == "access" else settings_obj.jwt_refresh_secret_key
    return jwt.encode(payload, secret, algorithm=settings_obj.jwt_algorithm)


def create_access_token(settings_obj: Settings, username: str, roles: list[Role]) -> str:
    return _create_token(
        settings_obj=settings_obj,
        username=username,
        roles=roles,
        token_type="access",
        expires_delta=timedelta(minutes=settings_obj.jwt_access_ttl_min),
    )


def create_refresh_token(settings_obj: Settings, username: str, roles: list[Role]) -> str:
    return _create_token(
        settings_obj=settings_obj,
        username=username,
        roles=roles,
        token_type="refresh",
        expires_delta=timedelta(days=settings_obj.jwt_refresh_ttl_days),
    )


def decode_token(settings_obj: Settings, token: str, expected_token_type: str = "access") -> dict[str, Any]:
    secret = settings_obj.jwt_secret_key if expected_token_type == "access" else settings_obj.jwt_refresh_secret_key
    try:
        payload = jwt.decode(token, secret, algorithms=[settings_obj.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if payload.get("token_type") != expected_token_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    return payload


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    settings_obj: Settings = Depends(get_settings),
) -> UserPublic:
    payload = decode_token(settings_obj, token, expected_token_type="access")
    username = payload.get("sub")
    roles = payload.get("roles", [])
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    return UserPublic(username=username, roles=roles)


def require_roles(allowed_roles: list[Role]) -> Callable[[UserPublic], UserPublic]:
    async def _inner(user: UserPublic = Depends(get_current_user)) -> UserPublic:
        if any(role in allowed_roles for role in user.roles):
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    return _inner


async def parse_refresh_request(body: RefreshRequest, settings_obj: Settings = Depends(get_settings)) -> UserPublic:
    payload = decode_token(settings_obj, body.refresh_token, expected_token_type="refresh")
    return UserPublic(username=payload["sub"], roles=payload.get("roles", []))


def get_orion(request: Request) -> OrionClient:
    return request.app.state.orion


def get_quantumleap(request: Request) -> QuantumLeapClient:
    return request.app.state.quantumleap


def get_postgis(request: Request) -> Any:
    return request.app.state.postgis


def get_redis_cache(request: Request) -> Any:
    return request.app.state.redis_cache


def get_ml_client(request: Request) -> MLClient:
    return request.app.state.ml_client


def get_llm_client(request: Request) -> LLMClient:
    return request.app.state.llm_client


def get_weather_fetcher(request: Request) -> WeatherFetcher:
    return request.app.state.weather_fetcher


def get_operation_store(request: Request) -> list[dict[str, Any]]:
    return request.app.state.operation_store


def get_parcel_status_overrides(request: Request) -> dict[str, str]:
    return request.app.state.parcel_status_overrides
