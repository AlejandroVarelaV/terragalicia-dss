#!/usr/bin/env bash
set -euo pipefail

# Load real data (SoilGrids, SIGPAC for A Coruña, last-30-days weather) and upsert to Orion

ROOT_DIR="$(dirname "${BASH_SOURCE[0]}")/.."
REAL_DIR="$ROOT_DIR/data/real"
mkdir -p "$REAL_DIR"

if [ -z "${AEMET_API_KEY:-}" ]; then
  echo "WARN: AEMET_API_KEY not set — using Open-Meteo as fallback (no key required)"
fi

echo "1) Fetching soils via scripts/fetch_real_data/fetch_soilgrids.py"
python3 "$ROOT_DIR/scripts/fetch_real_data/fetch_soilgrids.py" --out "$REAL_DIR/soils_real.json" || echo "Failed to fetch soils"

echo "2) Fetching SIGPAC parcels for A Coruña via scripts/fetch_real_data/fetch_sigpac_acoruna.py"
python3 "$ROOT_DIR/scripts/fetch_real_data/fetch_sigpac_acoruna.py" --out "$REAL_DIR/parcelas_acoruna.geojson" || echo "Failed to fetch SIGPAC parcels"

echo "3) Fetching last 30 days weather from Open-Meteo for A Coruña (-8.4115, 43.3623)"
END_DATE=$(date -I)
START_DATE=$(date -I -d "${END_DATE} -29 days")
OPEN_METEO_ARCHIVE_URL=${OPEN_METEO_ARCHIVE_URL:-https://archive-api.open-meteo.com/v1/archive}
curl -s -G "$OPEN_METEO_ARCHIVE_URL" \
  --data-urlencode "latitude=43.3623" \
  --data-urlencode "longitude=-8.4115" \
  --data-urlencode "start_date=$START_DATE" \
  --data-urlencode "end_date=$END_DATE" \
  --data-urlencode "daily=temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_max,relative_humidity_2m_min,windspeed_10m_max" \
  --data-urlencode "timezone=Europe/Madrid" \
  -o "$REAL_DIR/weather_acoruna_last30.json" || echo "Failed to fetch weather"

# 4) Upsert to Orion CB (best-effort)
ORION_BASE_URL=${ORION_BASE_URL:-http://localhost:1026}
ORION_SERVICE=${ORION_SERVICE:-terragalicia}
ORION_SERVICEPATH=${ORION_SERVICEPATH:-/}

echo "4) Upserting results to Orion Context Broker (best-effort)"
PACKED=0
PARCELS=0
SOILS=0
WEATHER=0

if [ -f "$REAL_DIR/parcelas_acoruna.geojson" ]; then
  PARCELS=$(jq '.features | length' "$REAL_DIR/parcelas_acoruna.geojson" || echo 0)
  # iterate features and create minimal AgriParcel entities
  jq -c '.features[]' "$REAL_DIR/parcelas_acoruna.geojson" | while read -r feat; do
    id=$(echo "$feat" | jq -r '.properties.id // .properties.REF // .id // empty')
    if [ -z "$id" ]; then
      id="urn:ngsi-ld:AgriParcel:random:$(uuidgen)"
    fi
    body=$(jq -n --arg id "$id" --argjson feat "$feat" '{id: $id, type: "AgriParcel", location: ($feat.geometry // {}), properties: ($feat.properties // {})}')
    curl -s -X POST "$ORION_BASE_URL/ngsi-ld/v1/entities" \
      -H "Content-Type: application/ld+json" \
      -H "fiware-service: $ORION_SERVICE" -H "fiware-servicepath: $ORION_SERVICEPATH" \
      --data-binary "$body" || true
    PACKED=$((PACKED+1))
  done
fi

if [ -f "$REAL_DIR/soils_real.json" ]; then
  SOILS=$(jq '. | length' "$REAL_DIR/soils_real.json" || echo 0)
  # upsert soils file as single entity array if possible
  jq -c '.[]' "$REAL_DIR/soils_real.json" | while read -r s; do
    sid=$(echo "$s" | jq -r '.id // empty')
    if [ -z "$sid" ]; then sid="urn:ngsi-ld:AgriSoil:$(uuidgen)"; fi
    body=$(jq -n --arg id "$sid" --argjson s "$s" '{id: $id, type: "AgriSoil", properties: $s}')
    curl -s -X POST "$ORION_BASE_URL/ngsi-ld/v1/entities" \
      -H "Content-Type: application/ld+json" \
      -H "fiware-service: $ORION_SERVICE" -H "fiware-servicepath: $ORION_SERVICEPATH" \
      --data-binary "$body" || true
    PACKED=$((PACKED+1))
  done
fi

if [ -f "$REAL_DIR/weather_acoruna_last30.json" ]; then
  # Open-Meteo returns a daily block; store as one WeatherForecast entity
  WEATHER_JSON="$REAL_DIR/weather_acoruna_last30.json"
  wid="urn:ngsi-ld:WeatherForecast:acoruna:$(date +%Y%m%d)"
  body=$(jq -n --arg id "$wid" --rawfile payload "$WEATHER_JSON" '{id: $id, type: "WeatherForecast", payload: $payload}')
  curl -s -X POST "$ORION_BASE_URL/ngsi-ld/v1/entities" \
    -H "Content-Type: application/ld+json" \
    -H "fiware-service: $ORION_SERVICE" -H "fiware-servicepath: $ORION_SERVICEPATH" \
    --data-binary "$body" || true
  WEATHER=1
  PACKED=$((PACKED+1))
fi

echo "Loaded: parcels=$PARCELS, soils=$SOILS, weather_observations=$WEATHER"