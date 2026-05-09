# Quick Start Guide - Real Data Integration

## Starting the Services

### 1. Backend API (port 8000)
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. ML Scoring Service (port 8010)
```bash
cd ml
python -m uvicorn main:app --host 0.0.0.0 --port 8010
```

### 3. Docker Services (from infra/)
```bash
docker-compose up -d
```

## Testing Real Data Integration

### ML Scorer
```bash
curl -X POST http://localhost:8010/score \
  -H 'Content-Type: application/json' \
  -d '{
    "crop_id":"millo",
    "soil_ph":5.8,
    "soil_texture":"loam",
    "annual_rainfall_mm":1200,
    "frost_days":2,
    "sowing_month":4
  }'
```
Expected: `{"cropId":"millo","score":72,"colorBand":"green","breakdown":{...}}`

### Weather Endpoint
```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=farmer1&password=farmer123&grant_type=password' | jq -r '.access_token')

# Get weather
curl -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8000/api/v1/weather?parcelId=urn:ngsi-ld:AgriParcel:farm001:parcel01'
```
Expected: Current weather + 7-day forecast with temperature, precipitation, humidity

### Crop Suitability Rankings
```bash
curl -H "Authorization: Bearer $TOKEN" \
  'http://localhost:8000/api/v1/parcels/urn:ngsi-ld:AgriParcel:farm001:parcel01/suitability'
```
Expected: 8 crops ranked by suitability score with detailed breakdown

## Configuration

### Environment Variables (.env)
```bash
# Weather APIs
OPEN_METEO_URL=https://api.open-meteo.com/v1/forecast
OPEN_METEO_ARCHIVE_URL=https://archive-api.open-meteo.com/v1/archive
AEMET_API_KEY=optional_key

# SoilGrids (use alias if DNS issues)
SOILGRIDS_URL=https://rest.isric.org

# Backend services
ML_SERVICE_URL=http://localhost:8010
ORION_BASE_URL=http://localhost:1026
QUANTUMLEAP_BASE_URL=http://localhost:8668
REDIS_URL=redis://localhost:6379/0
```

## API Features

### Weather Service
- **fetch_forecast(lat, lon, days=7)** - 7-day forecast
- **fetch_current_weather(lat, lon)** - Current conditions
- **fetch_historical(lat, lon, days=30)** - 30-day history
- **Fallback:** AEMET April 1991-2020 climatology when APIs fail

### ML Scoring
- **8 Galician Crops:** millo, pataca, kiwi, albarino, mencia, grelos, trigo, centeo
- **5 Scoring Factors:** pH, rainfall, frost risk, soil texture, planting window
- **Color Bands:** Green (≥70), Yellow (40-69), Red (<40)
- **Response:** Score (0-100), color band, and detailed factor breakdown

### Crop Suitability
- **Batch Ranking:** All 8 crops scored for a parcel
- **Breakdown Preservation:** Each crop shows all 5 factor calculations
- **Score Format:** 0.0-1.0 scale in rankings (divide by 100)

## Troubleshooting

### Weather returns climatological data
- Normal behavior when Open-Meteo API is unavailable
- Check `dataQuality` field: "live" vs "climatological_average"
- Fallback values: 16.2°C max, 8.4°C min, 2.97mm precip (April average)

### SoilGrids connection fails
- **Issue:** DNS can't resolve rest.soilgrids.org in WSL2
- **Solution:** Use rest.isric.org alias instead
- **In code:** Update SOILGRIDS_URL environment variable

### ML Service returns 503
- ML service is unavailable or crashed
- Check ML service is running on port 8010
- Restart: `cd ml && python -m uvicorn main:app --port 8010`

### Parcel not found errors
- Seed data needs to be loaded first
- Run: `./scripts/load_seed_data.sh`
- Or load real data: `./scripts/load_real_data.sh`

## Key Innovations

1. **Climatological Fallback**
   - When Open-Meteo fails, returns AEMET 1991-2020 April normals for Galicia
   - Ensures weather data is always available

2. **5-Factor Agronomic Scoring**
   - Customized for each crop (8 Galician varieties)
   - Considers soil pH, water availability, frost risk, soil type, planting season
   - Detailed breakdown shows which factors limit suitability

3. **Error Transparency**
   - 502 for infrastructure failures (Orion, persistence)
   - 503 for external service failures (ML scorer)
   - Helpful error messages for data loading

4. **Real vs Mock Data**
   - Integrates Open-Meteo (live weather forecasts)
   - Includes SoilGrids (soil properties)
   - Falls back to seed data when real data unavailable

## Performance Notes

- **Forecast:** ~500ms (Open-Meteo API)
- **Scoring:** <50ms per crop (local computation)
- **Ranking:** ~500ms total (100ms batch + fallback logic)
- **Caching:** Redis for weather (key: `suitability-weather:{parcelId}`)

## Next Steps

1. Load seed/real data: `./scripts/load_seed_data.sh`
2. Start all services
3. Get auth token and test endpoints
4. Monitor API response times and error rates
5. Configure for production deployment
