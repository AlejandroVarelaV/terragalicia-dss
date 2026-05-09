#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEED_DIR="${ROOT_DIR}/data/seed"
ORION_URL="${ORION_URL:-http://localhost:1026}"
QL_URL="${QL_URL:-http://localhost:8668}"
MAX_ATTEMPTS=30

echo "Waiting for Orion Context Broker at ${ORION_URL} ..."
for attempt in $(seq 1 "${MAX_ATTEMPTS}"); do
  if curl -fsS "${ORION_URL}/version" >/dev/null; then
    echo "Orion is healthy (attempt ${attempt}/${MAX_ATTEMPTS})."
    break
  fi

  if [[ "${attempt}" -eq "${MAX_ATTEMPTS}" ]]; then
    echo "ERROR: Orion did not become healthy after ${MAX_ATTEMPTS} attempts."
    exit 1
  fi

  sleep 2
done

SUBSCRIPTION_PAYLOAD='{
  "id": "urn:ngsi-ld:Subscription:terragalicia:quantumleap",
  "type": "Subscription",
  "entities": [
    {"type": "AgriFarm"},
    {"type": "AgriParcel"},
    {"type": "AgriCrop"},
    {"type": "AgriSoil"},
    {"type": "AgriParcelRecord"},
    {"type": "AgriParcelOperation"},
    {"type": "AgriFertilizer"},
    {"type": "WeatherObserved"},
    {"type": "WeatherForecast"},
    {"type": "WaterQualityObserved"}
  ],
  "notification": {
    "format": "normalized",
    "endpoint": {
      "uri": "'"${QL_URL}"'/v2/notify",
      "accept": "application/json"
    }
  },
  "@context": [
    "http://context-server/context.jsonld"
  ]
}'

echo "Creating/updating Orion -> QuantumLeap subscription ..."
SUB_STATUS=$(curl -s -o /tmp/terragalicia_subscription_response.json -w "%{http_code}" \
  -X POST "${ORION_URL}/ngsi-ld/v1/subscriptions" \
  -H "Content-Type: application/ld+json" \
  --data "${SUBSCRIPTION_PAYLOAD}")

if [[ "${SUB_STATUS}" == "201" || "${SUB_STATUS}" == "204" || "${SUB_STATUS}" == "409" ]]; then
  echo "Subscription status: ${SUB_STATUS} (ok)."
else
  echo "WARNING: Subscription creation returned HTTP ${SUB_STATUS}."
  cat /tmp/terragalicia_subscription_response.json || true
fi

load_file() {
  local file_path="$1"
  local success=0
  local fail=0

  while IFS= read -r entity_json; do
    local status
    status=$(curl -s -o /tmp/terragalicia_entity_response.json -w "%{http_code}" \
      -X POST "${ORION_URL}/ngsi-ld/v1/entities" \
      -H "Content-Type: application/ld+json" \
      --data "${entity_json}")

    if [[ "${status}" == "201" || "${status}" == "204" || "${status}" == "409" ]]; then
      success=$((success + 1))
    else
      fail=$((fail + 1))
    fi
  done < <(python3 - <<PY
import json
with open("${file_path}", "r", encoding="utf-8") as f:
    arr = json.load(f)
for item in arr:
    print(json.dumps(item, separators=(",", ":")))
PY
)

  echo "$(basename "${file_path}"): success=${success} fail=${fail}"
}

echo "Loading seed files from ${SEED_DIR} ..."
shopt -s nullglob
for file in "${SEED_DIR}"/seed_*.json; do
  load_file "${file}"
done

echo "Seed loading process completed."
