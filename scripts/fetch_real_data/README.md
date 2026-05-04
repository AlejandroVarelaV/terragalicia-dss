# Real Data Fetch Scripts (Step 8c)

This package fetches external agronomic data and maps it to TerraGalicia NGSI-LD entities.

## Files

- `fetch_aemet.py`: AEMET OpenData forecast fetcher.
- `fetch_meteogalicia.py`: MeteoGalicia 7-day forecast fetcher.
- `fetch_soilgrids.py`: ISRIC SoilGrids v2 soil properties fetcher.
- `fetch_sigpac.py`: SIGPAC WFS parcel polygons fetcher.
- `load_to_orion.py`: Orion-LD NGSI-LD upsert loader.
- `run_all.sh`: End-to-end orchestration for the 9 seed parcel centroids.

## Prerequisites

- Python 3.11+
- Installed dependencies from `backend/requirements.txt`:
  - `httpx`
  - `tenacity`
- Running Orion-LD endpoint (default: `http://localhost:1026`)
- `AEMET_API_KEY` environment variable for AEMET calls

## Quick Run

```bash
export AEMET_API_KEY="your_key_here"
bash scripts/fetch_real_data/run_all.sh
```

## Individual Commands

```bash
python3 -m scripts.fetch_real_data.fetch_meteogalicia --lat 43.3364 --lon -8.32085 --output data/cache/meteogalicia_entities.json --append
python3 -m scripts.fetch_real_data.fetch_soilgrids --lat 43.3364 --lon -8.32085 --output data/cache/soilgrids_entities.json --append
python3 -m scripts.fetch_real_data.fetch_aemet --lat 43.3623 --lon -8.4115 --output data/cache/aemet_entities.json --append
python3 -m scripts.fetch_real_data.load_to_orion --files data/cache/meteogalicia_entities.json data/cache/soilgrids_entities.json data/cache/aemet_entities.json
```

## Notes

- All fetchers use async `httpx` + `tenacity` (3 retries, exponential backoff).
- On provider/network errors, scripts log warnings and fall back to seed data.
- Raw payloads and generated entity outputs are written under `data/cache/`.
- `run_all.sh` prints: `X entities updated, Y errors` based on loader results.
