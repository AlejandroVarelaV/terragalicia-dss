# TerraGalicia DSS Startup Guide

This guide is written for developers running the project manually, without AI assistance. Commands are copy-pasteable and based on the audited repository state.

## 0. System Requirements Check

Run these commands and confirm versions:

```bash
docker --version
docker-compose --version
python3 --version
node --version
git --version
```

Expected minimums:

- Docker installed
- Docker Compose available (`docker-compose` or plugin)
- Python `3.11+`
- Node `20+`

If Node is older than 20, install/update before continuing.

## 1. First Time Setup (Do This Once)

### 1.1 Clone repository

```bash
git clone https://github.com/AlejandroVarelaV/terragalicia-dss.git
cd terragalicia-dss
```

### 1.2 Configure environment variables

```bash
cp infra/.env.example infra/.env
```

Edit `infra/.env` and set required values:

- `JWT_SECRET_KEY`: signs access tokens for backend auth
- `JWT_REFRESH_SECRET_KEY`: signs refresh tokens
- `POSTGRES_PASSWORD`: password for PostGIS container
- `TIMESCALEDB_PASSWORD`: password for TimescaleDB container
- `MONGO_INITDB_ROOT_PASSWORD`: password for MongoDB root user
- `MQTT_PASSWORD`: password for MQTT broker user
- `GRAFANA_ADMIN_PASSWORD`: Grafana admin password
- `AEMET_API_KEY`: enables live AEMET data fetch scripts
- `METEOGALICIA_API_KEY`: enables MeteoGalicia API integration (if required by endpoint)
- `LLM_API_KEY`: required when using remote LLM provider

Recommended to review and keep these aligned with your target environment:

- `ORION_BASE_URL`, `QUANTUMLEAP_BASE_URL`, `IOTA_NORTH_URL`
- `DATABASE_URL_POSTGIS`, `DATABASE_URL_TIMESCALE`, `REDIS_URL`
- `ML_SERVICE_URL`, `LLM_API_BASE`, `LLM_PROVIDER`

### 1.3 Build Docker images

```bash
cd infra
docker-compose build
```

Expected output (summary):

- `Successfully built ...`
- `Successfully tagged infra_backend:latest`
- `Successfully tagged infra_frontend:latest`
- `Successfully tagged infra_ml-service:latest`

## 2. Starting the Application

From `infra/`:

```bash
docker-compose up -d
```

Expected output pattern:

- `Creating infra_mongo_1 ... done`
- `Creating infra_orion_1 ... done`
- `Creating infra_backend_1 ... done`
- `Creating infra_frontend_1 ... done`

Check service status:

```bash
docker-compose ps
```

Expected state:

- Most services should be `Up`
- `orion` may stay in `starting` briefly
- `iot-agent` may appear `unhealthy` in current branch (known issue)

## 3. Verifying Everything Works

Run from any shell.

### 3.1 Orion CB health

```bash
curl -i http://localhost:1026/version
```

Expected (healthy):

- `HTTP/1.1 200 OK`
- JSON containing Orion version

Current audit note: Orion sometimes resets connection while booting. Retry after 10-20 seconds.

### 3.2 QuantumLeap health

```bash
curl -i http://localhost:8668/version
```

Expected:

- `HTTP/1.1 200 OK`
- Body similar to `{"version":"..."}`

### 3.3 IoT Agent health

```bash
curl -i http://localhost:4041/iot/about
```

Expected (healthy):

- `HTTP/1.1 200 OK`
- JSON about IoT Agent service

Current audit note: intermittent connection reset and `unhealthy` container state observed.

### 3.4 Backend health

```bash
curl -i http://localhost:8000/health
```

Expected in current running stack:

- `HTTP/1.1 200 OK`
- JSON with service status and checks (for example: `orion`, `database`, `redis`)

### 3.5 Suitability endpoint with example parcel ID

Example parcel ID:

`urn:ngsi-ld:AgriParcel:farm001:parcel01`

Get token:

```bash
TOKEN=$(curl -sS -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=farmer1&password=farmer123' | python3 -c 'import sys, json; print(json.load(sys.stdin).get("access_token", ""))')
echo "$TOKEN" | head -c 40 && echo
```

Call suitability:

```bash
curl -i "http://localhost:8000/api/v1/parcels/urn:ngsi-ld:AgriParcel:farm001:parcel01/suitability" \
  -H "Authorization: Bearer $TOKEN"
```

Expected when fully wired:

- `HTTP/1.1 200 OK`
- JSON with `parcelId`, `generatedAt`, and `ranking`

Current audit note: behavior depends on running image. In some runs this endpoint returns auth errors or 404 because source/runtime are out of sync.

## 4. Loading Data

### 4.1 Load seed data

From repository root:

```bash
bash scripts/load_seed_data.sh
```

Expected output pattern:

- `Orion is healthy...`
- `Subscription status: 201/204/409 (ok).`
- One line per `seed_*.json` file: `success=X fail=Y`

### 4.2 Verify seed load

Check farms:

```bash
curl -sS 'http://localhost:1026/ngsi-ld/v1/entities?type=AgriFarm&limit=5' \
  -H 'Accept: application/ld+json' \
  -H 'Link: <https://uri.fiware.org/ns/data-models>; rel="http://www.w3.org/ns/json-ld#context"'
```

Check parcels:

```bash
curl -sS 'http://localhost:1026/ngsi-ld/v1/entities?type=AgriParcel&limit=5' \
  -H 'Accept: application/ld+json' \
  -H 'Link: <https://uri.fiware.org/ns/data-models>; rel="http://www.w3.org/ns/json-ld#context"'
```

### 4.3 Real data scripts

Available scripts in `scripts/fetch_real_data/`:

- `fetch_aemet.py`
- `fetch_meteogalicia.py`
- `fetch_sigpac.py`
- `fetch_soilgrids.py`
- `load_to_orion.py`
- `run_all.sh`

End-to-end run example:

```bash
export AEMET_API_KEY='eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhbGV4dmFyZWxhZGNAZ21haWwuY29tIiwianRpIjoiZjQ2MTBkNzAtMTMzMC00MDgxLWI4ODAtN2ZhNzkzZDU0NGQwIiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE3NzgxNzMwMDksInVzZXJJZCI6ImY0NjEwZDcwLTEzMzAtNDA4MS1iODgwLTdmYTc5M2Q1NDRkMCIsInJvbGUiOiIifQ.Q1jktMFc2wM2Ye1330fGsV6lJ8qglsO79q44Ld5Fl30'
bash scripts/fetch_real_data/run_all.sh
```

## 5. Accessing the Application

- Map view URL: `http://localhost`
- Expected behavior: Nginx serves frontend container output. In current branch, the Docker frontend is a placeholder page unless you run Vite locally (see section 8).
- Select parcel: in React map mode, click a polygon to open parcel popup with ID, crop, soil, and status.
- View crop suitability: call backend suitability API (section 3.5).
- AgroCopilot: if backend `/api/v1/copilot/chat` is mounted in your running image, use token-authenticated API calls. If not mounted, this feature is not yet available in that runtime.

## 6. Stopping and Restarting

From `infra/`:

Stop stack:

```bash
docker-compose down
```

Stop and delete volumes (nuclear, deletes persisted DB data):

```bash
docker-compose down -v
```

Restart one service only (example backend):

```bash
docker-compose up -d --no-deps backend
```

## 7. Troubleshooting (Common Issues)

### Orion fails to start

- Symptom: `curl http://localhost:1026/version` fails or container loops
- Diagnosis: MongoDB compatibility/version/startup race
- Fix: ensure `mongo` is healthy, then restart Orion:

```bash
cd infra
docker-compose restart mongo orion
docker-compose logs --tail=100 orion
```

### QuantumLeap not receiving data

- Symptom: no history points in QuantumLeap
- Diagnosis: Orion subscription missing or failing
- Fix: rerun seed loader (creates subscription) and validate:

```bash
bash scripts/load_seed_data.sh
curl -sS http://localhost:1026/ngsi-ld/v1/subscriptions
```

### Map does not load

- Symptom: blank/partial map tiles
- Diagnosis: SIGPAC WMS or CORS/network failures
- Fix: use fallback parcels, verify backend SIGPAC endpoint:

```bash
curl -i http://localhost:8000/sigpac/parcels
```

### Suitability returns empty

- Symptom: empty ranking, 404, or auth failure
- Diagnosis: ML service endpoint mismatch or backend routes not mounted in running image
- Fix: verify ML service health and backend route availability:

```bash
curl -i http://localhost:8010/health
curl -i http://localhost:8000/api/v1/docs
```

### Slow map rendering

- Symptom: map interactions lag
- Diagnosis: external tile latency and no local tile cache
- Fix: keep OSM as base layer, reduce heavy overlays, and consider reverse-proxy caching for WMS/TMS.

### Buttons or actions not working

- Symptom: UI actions fail silently or HTTP errors
- Diagnosis: API CORS/config mismatch, auth token issues, or placeholder backend/frontend image
- Fix: inspect browser network tab, backend logs, and CORS settings; ensure frontend points to correct backend URL.

## 8. Development Mode (Without Docker)

Use this for faster iteration.

### 8.1 Backend locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Note: current `backend/requirements.txt` may be incomplete for full route stack; install missing packages as needed if you switch to non-placeholder entrypoint.

### 8.2 Frontend locally (React/Vite)

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Open `http://localhost:5173`.

### 8.3 ML locally

```bash
cd ml
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8010
```

### 8.4 Optional mixed mode

Run FIWARE and databases in Docker, but backend/frontend locally for development speed:

```bash
cd infra
docker-compose up -d mongo orion timescaledb postgres redis quantumleap iot-agent mqtt-broker
```
