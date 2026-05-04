#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CACHE_DIR="${ROOT_DIR}/data/cache"
mkdir -p "${CACHE_DIR}"

if [[ -z "${AEMET_API_KEY:-}" ]]; then
  echo "ERROR: AEMET_API_KEY is not set."
  exit 1
fi

METEO_OUT="${CACHE_DIR}/meteogalicia_entities.json"
SOIL_OUT="${CACHE_DIR}/soilgrids_entities.json"
AEMET_OUT="${CACHE_DIR}/aemet_entities.json"

rm -f "${METEO_OUT}" "${SOIL_OUT}" "${AEMET_OUT}"

PARCEL_IDS=(
  "urn:ngsi-ld:AgriParcel:farm001:parcel01"
  "urn:ngsi-ld:AgriParcel:farm001:parcel02"
  "urn:ngsi-ld:AgriParcel:farm001:parcel03"
  "urn:ngsi-ld:AgriParcel:farm002:parcel01"
  "urn:ngsi-ld:AgriParcel:farm002:parcel02"
  "urn:ngsi-ld:AgriParcel:farm002:parcel03"
  "urn:ngsi-ld:AgriParcel:farm003:parcel01"
  "urn:ngsi-ld:AgriParcel:farm003:parcel02"
  "urn:ngsi-ld:AgriParcel:farm003:parcel03"
)

# Hardcoded parcel centroids from seed_parcels.json (lat,lon)
COORDS=(
  "43.3364,-8.32085"
  "43.3319,-8.3285"
  "43.3297,-8.31265"
  "43.3184,-8.23625"
  "43.3143,-8.22875"
  "43.3122,-8.2402"
  "43.2856,-8.2188"
  "43.2789,-8.21125"
  "43.28265,-8.2082"
)

cd "${ROOT_DIR}"

echo "Running MeteoGalicia fetch for 9 parcel centroids..."
for i in "${!COORDS[@]}"; do
  LAT="${COORDS[$i]%,*}"
  LON="${COORDS[$i]#*,}"
  PARCEL_ID="${PARCEL_IDS[$i]}"

  python3 -m scripts.fetch_real_data.fetch_meteogalicia \
    --lat "${LAT}" \
    --lon "${LON}" \
    --parcel-id "${PARCEL_ID}" \
    --output "${METEO_OUT}" \
    --append

done

echo "Running SoilGrids fetch for 9 parcel centroids..."
for i in "${!COORDS[@]}"; do
  LAT="${COORDS[$i]%,*}"
  LON="${COORDS[$i]#*,}"
  PARCEL_ID="${PARCEL_IDS[$i]}"

  python3 -m scripts.fetch_real_data.fetch_soilgrids \
    --lat "${LAT}" \
    --lon "${LON}" \
    --parcel-id "${PARCEL_ID}" \
    --output "${SOIL_OUT}" \
    --append

done

echo "Running AEMET forecast fetch (A Coruna reference point)..."
python3 -m scripts.fetch_real_data.fetch_aemet \
  --lat "43.3623" \
  --lon "-8.4115" \
  --output "${AEMET_OUT}" \
  --append

echo "Loading fetched entities into Orion..."
set +e
LOAD_OUTPUT=$(python3 -m scripts.fetch_real_data.load_to_orion --files "${METEO_OUT}" "${SOIL_OUT}" "${AEMET_OUT}" 2>&1)
LOAD_EXIT=$?
set -e

echo "${LOAD_OUTPUT}"

SUMMARY_LINE=$(echo "${LOAD_OUTPUT}" | grep "RESULT updated=" | tail -n 1 || true)
UPDATED=$(echo "${SUMMARY_LINE}" | sed -n 's/.*updated=\([0-9][0-9]*\).*/\1/p')
ERRORS=$(echo "${SUMMARY_LINE}" | sed -n 's/.*errors=\([0-9][0-9]*\).*/\1/p')

UPDATED="${UPDATED:-0}"
ERRORS="${ERRORS:-0}"

echo "Run complete: ${UPDATED} entities updated, ${ERRORS} errors."

exit "${LOAD_EXIT}"
