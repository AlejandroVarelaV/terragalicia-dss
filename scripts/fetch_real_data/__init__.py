"""Utilities for TerraGalicia real data fetchers (Step 8c)."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

NGSI_CONTEXT = ["http://context-server/context.jsonld"]


def configure_logging(level: int = logging.INFO) -> None:
    """Configure a consistent log format for all fetch scripts."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def get_repo_root() -> Path:
    """Resolve repository root from scripts/fetch_real_data package path."""
    return Path(__file__).resolve().parents[2]


def get_cache_dir() -> Path:
    cache_dir = get_repo_root() / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def append_json_array(path: Path, payload: Any) -> None:
    """Append payload items to a JSON file storing a single top-level list."""
    path.parent.mkdir(parents=True, exist_ok=True)
    items: list[Any] = []
    if path.exists():
        try:
            existing = load_json(path)
            if isinstance(existing, list):
                items = existing
        except json.JSONDecodeError:
            items = []

    if isinstance(payload, list):
        items.extend(payload)
    else:
        items.append(payload)

    dump_json(path, items)


def fallback_seed_weather_forecast() -> list[dict[str, Any]]:
    seed_path = get_repo_root() / "data" / "seed" / "seed_weather_forecast.json"
    payload = load_json(seed_path)
    return payload if isinstance(payload, list) else []


def fallback_seed_soils() -> list[dict[str, Any]]:
    seed_path = get_repo_root() / "data" / "seed" / "seed_soils.json"
    payload = load_json(seed_path)
    return payload if isinstance(payload, list) else []


def fallback_seed_parcels() -> list[dict[str, Any]]:
    seed_path = get_repo_root() / "data" / "seed" / "seed_parcels.json"
    payload = load_json(seed_path)
    return payload if isinstance(payload, list) else []


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
