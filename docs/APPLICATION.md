# TerraGalicia DSS — Application Guide

**Version**: 1.1
**Date**: May 2026
**Status**: Partial MVP — Core features running

---

## 1. What is TerraGalicia?

TerraGalicia is an open-source agricultural decision-support system (DSS) for smallholder farmers and cooperatives in Galicia. It provides an interactive map-based interface over real SIGPAC land-registry parcel data, enriched with crop suitability scoring, weather forecasts, a conversational AI assistant (AgroCopilot), and a what-if scenario simulator.

---

## 2. Running Infrastructure

The application runs via Docker Compose. All services share a private bridge network; only Nginx exposes public ports.

| Service | Image / Build | Port (internal) | Status |
|---|---|---|---|
| `nginx` | `nginx:1.27-alpine` | 80 (public) | Running |
| `frontend` | Custom Vite/React build | 80 | Running |
| `backend` | Custom FastAPI build | 8000 | Running |
| `orion` | `fiware/orion-ld:latest` | 1026 | Running |
| `mongo` | `mongo:5` | 27017 | Running |
| `context-server` | Custom NGSI-LD context server | — | Running |
| `postgres` | `postgis/postgis:15-3.4` | 5433 | Running |
| `timescaledb` | `timescale/timescaledb` | 5432 | Running |
| `redis` | `redis:7-alpine` | 6379 | Running |
| `iot-agent` | `fiware/iotagent-json` | 4041/7896 | Defined, not started |
| `quantumleap` | `orchestracities/quantumleap` | 8668 | Defined, not started |
| `grafana` | `grafana/grafana:11` | 3001 | Defined, not started |
| `ml-service` | Custom inference image | 8010 | Defined, not started |

### Nginx routes

| Path | Upstream |
|---|---|
| `/` | frontend:80 |
| `/api/` | backend:8000 |
| `/grafana/` | grafana:3000 |
| `/orion/` | orion:1026 |

---

## 3. Accessing the Application

Open `http://localhost` in a browser. The application auto-authenticates as the demo user `farmer1` / `farmer123` on load (JWT token obtained from `/api/v1/auth/login` at startup).

---

## 4. Map Interface

The map is centered on the A Coruña / Galicia region (43.2792 N, 8.2100 W) at zoom 13.

### Base layers (toggle via layers button, top-right)
- **Rúas (OpenStreetMap)** — default
- **Ortofoto (PNOA)** — high-resolution aerial photography (IGN)

### SIGPAC parcel viewer
SIGPAC parcels are loaded from a PostGIS database (`recintos_sigpac` table) with a `.gpkg` file fallback for the A Coruña province.

**Controls — top-center cluster:**
- **Amosar SIGPAC / Ocultar SIGPAC** — toggles parcel loading on/off.
- **Refrescar** — visible only when SIGPAC is active; re-fetches parcels for the current viewport without panning. Disabled while a fetch is in progress.
- **Truncation banner** — appears below the controls when >5000 parcelas are in the area (backend HARD_LIMIT). Text: *"Amosando 5000 parcelas. Fai zoom ou usa Refrescar para ver outras."*

**Zoom requirement:** parcels only load at zoom ≥ 15 (frontend gate). Below zoom 15 the badge reads *"Preme Amosar SIGPAC e fai zoom para ver parcelas"*.

**Geometry strategy (backend, zoom-dependent):**
| Zoom | Geometry returned |
|---|---|
| ≤ 14 (backend only, not reached by frontend) | `ST_Centroid` (GeoJSON Point) |
| 15 | `ST_Simplify(geom, 0.0002)` with COALESCE fallback to full geometry |
| 16 | `ST_Simplify(geom, 0.0001)` with COALESCE fallback to full geometry |
| ≥ 17 | Full geometry |

**Rendering:** All parcels are drawn on a single Leaflet canvas renderer (`L.canvas({ padding: 0.5 })`). This avoids thousands of SVG DOM nodes and keeps rendering under 1 second for 5000 parcels.

**Parcel colors (status):**
| Status | Color |
|---|---|
| PLANTED | Amber `#f59e0b` |
| FALLOW | Gray `#9ca3af` |
| PREPARED | Green `#22c55e` |
| HARVESTED | Blue `#3b82f6` |
| Unknown | Slate `#64748b` |

### Parcel popup (click any parcel)
Clicking a parcel opens a popup with:
- Cadastral ID, name, area (ha, click to toggle to m²), municipality, soil type, source
- Current status with color dot
- Crop suitability ranking (top crops with score bars) — fetched asynchronously from `/api/v1/parcels/{id}/suitability`
- Status selector (`<select>`) to update parcel status; changes are PATCHed to the backend
- **Simular** button — opens the WhatIf Simulator for that parcel

### Legend (bottom-left)
Collapsible panel showing:
- Status color swatches (PREPARED / FALLOW / PLANTED / HARVESTED)
- Live mouse coordinates in decimal degrees

### Data source badge (top-left)
Shows current data source: `Fonte: PostGIS` or `Fonte: GeoPackage local (A Coruña)`, or loading/zoom prompt.

---

## 5. Weather Panel

Button: bottom-right (blue circular button). Shows:
- Current conditions for the map center (temperature, humidity, wind, precipitation)
- 7-day forecast strip
- Refresh and future-day navigation buttons

Data fetched from `/api/v1/weather?lat=...&lon=...`.

---

## 6. AgroCopilot

Button: bottom-right (green circular button). Opens a chat drawer. Accepts questions in Galician or Spanish about parcels, crops, weather, and operations. Each session is pre-loaded with the selected parcel's context.

Endpoint: `POST /api/v1/copilot/chat`

---

## 7. WhatIf Simulator

Triggered from the parcel popup's **Simular** button. Allows adjusting:
- Sowing date (slider)
- Crop type (dropdown)
- Irrigation assumption (toggle)

Recalculates success probability in real time.

Endpoint: `POST /api/v1/simulator/whatif`

---

## 8. Backend API Reference (implemented endpoints)

All endpoints require `Authorization: Bearer <token>` except `/api/v1/auth/login`.

| Endpoint | Methods | Description |
|---|---|---|
| `/api/v1/auth/login` | POST | Obtain JWT access token (form: `username`, `password`, `grant_type`) |
| `/api/v1/sigpac/parcels` | GET | SIGPAC parcels by bbox and zoom. Params: `bbox` (minLon,minLat,maxLon,maxLat), `zoom`, `limit` (default 5000, max 5000) |
| `/api/v1/sigpac/nearby` | GET | SIGPAC parcels near cursor. Params: `lat`, `lon`, `zoom`, `limit` |
| `/api/v1/parcels/{id}` | GET, PATCH | Retrieve or update parcel metadata and status |
| `/api/v1/parcels/{id}/suitability` | GET | Crop suitability score and ranking for a parcel |
| `/api/v1/parcels/{id}/operations` | GET, POST | List or create parcel operations |
| `/api/v1/weather` | GET | Current + 7-day forecast weather for a location |
| `/api/v1/copilot/chat` | POST | AgroCopilot conversational endpoint |
| `/api/v1/simulator/whatif` | POST | What-if scenario simulation |

### SIGPAC API response shape

```json
{
  "type": "FeatureCollection",
  "features": [...],
  "truncated": false,
  "total_estimate": 342,
  "returned": 342
}
```

Each feature carries:
- `properties.id` — SIGPAC cadastral ID
- `properties.source` — `"postgis"` or `"gpkg-local"`
- `properties.geometry_type` — `"centroid"` (zoom ≤ 14) or `"polygon"`
- `properties.status` — parcel status enum
- Standard SIGPAC attributes (provincia, municipio, poligono, parcela, recinto, uso_sigpac, superficie)

---

## 9. SIGPAC Data Pipeline

```
SIGPAC official WFS  ──→  recintos_sigpac (PostGIS table, SRID 4326)
                              │
                              ├─ bbox + zoom query (ST_MakeEnvelope + &&)
                              ├─ count-up-to-5001 (early exit, avoids full COUNT(*))
                              ├─ 15s statement_timeout (SET LOCAL inside transaction)
                              └─ Redis cache (24h TTL, keyed by exact bbox string)
                                      │
                              ├─ On cache miss: PostGIS query
                              ├─ On PostGIS failure: .gpkg file fallback (A Coruña)
                              └─ On .gpkg failure: mock/seed data
```

The backend enforces `HARD_LIMIT = 5000`. The `truncated` flag is set when `total_estimate > 5000`.

---

## 10. Currently Not Implemented (Planned for Phase 2)

- **IoT Agent / QuantumLeap**: Not started. No live sensor ingestion or time-series history.
- **Grafana**: Not started. Operational dashboards pending.
- **ML service**: Suitability scores use a pre-configured stub (no trained model).
- **LLM service**: AgroCopilot uses a backend handler without a local model; responses depend on context-server configuration.
- **MQTT broker**: Not in the current Compose stack.
- **Offline capability**: No service worker or app shell.
- **SMS alerts**: Email/push only (not yet implemented).
- **Pest phenology alerts**: Deferred.
- **Cooperative multi-parcel dashboard**: Deferred.
- **SIGPAC coverage outside A Coruña**: `.gpkg` fallback only covers A Coruña province; PostGIS table coverage depends on ingested data.
