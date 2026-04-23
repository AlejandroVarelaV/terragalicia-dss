# TerraGalicia Synthetic Seed Data

This folder contains synthetic NGSI-LD JSON-LD seed datasets for MVP demo and development in A Coruna, Galicia, Spain.

## Files included

- `seed_farms.json`
  - 3 `AgriFarm` entities in Oleiros, Bergondo, and Betanzos.
  - Includes one farm with `cooperativeCode`.

- `seed_parcels.json`
  - 9 `AgriParcel` entities (3 per farm).
  - Real-looking small rural polygons near each municipality.
  - Parcel areas from 0.78 to 7.42 ha.
  - Status mix includes `PLANTED`, `FALLOW`, `PREPARED`.
  - `hasAgriCrop` assigned for planted parcels.

- `seed_crops.json`
  - 8 `AgriCrop` catalog entities: millo, pataca, kiwi, Albarino, Mencia, grelos, trigo, centeo.
  - Includes planting and harvest ranges, water need, modelled yield, and recommended pH ranges.

- `seed_soils.json`
  - 4 `AgriSoil` profiles representative of Galicia:
    - Atlantic acid
    - Alluvial valley
    - Coastal sandy
    - Hillside clay-loam

- `seed_weather_observed.json`
  - 30 daily `WeatherObserved` entities for A Coruna station (-8.4115, 43.3623).
  - Last 30 days (2026-03-23 to 2026-04-21).
  - Realistic April Galicia ranges for temperature, humidity, precipitation, wind.

- `seed_weather_forecast.json`
  - 7 `WeatherForecast` entities for next 7 days (2026-04-22 to 2026-04-28).
  - Includes one frost-risk day, one heavy-rain day, and two spray-window days.

- `seed_fertilizers.json`
  - 4 `AgriFertilizer` entities:
    - NPK 15-15-15
    - Urea 46-0-0
    - Ammonium Nitrate 27-0-0
    - Organic compost 3-2-2

- `seed_operations.json`
  - 12 `AgriParcelOperation` entities:
    - 4 sowing
    - 4 fertilizing (linked to `AgriFertilizer`)
    - 2 spraying
    - 2 harvesting (Sep-Oct 2025)

- `seed_parcel_records.json`
  - 60 `AgriParcelRecord` entities.
  - 2 records per day over last 30 days for `urn:ngsi-ld:AgriParcel:farm001:parcel01`.
  - Soil moisture values are correlated with rainfall from `seed_weather_observed.json`.

## NGSI-LD format notes

- All files use:
  - `@context`: `https://uri.fiware.org/ns/data-models`, `https://schema.org`
  - URN identifiers with `urn:ngsi-ld:` prefix
- Numeric measurements include `unitCode` where applicable.

## Extension attributes used

JSON comments are not valid JSON, so extension markers are documented here.

The following attributes are extensions in these seed files:

- `AgriFarm`: `cooperativeCode`
- `AgriParcel`: `parcelStatus`
- `AgriCrop`: `plantingDateRange`, `expectedHarvestDateRange`, `waterNeed`, `modelledYield`, `recommendedSoilPHMin`, `recommendedSoilPHMax`
- `AgriSoil`: `waterRetentionClass`
- `WeatherForecast`: `issuedAt`, `validFrom`, `validTo`, `relativeHumidity`, `windSpeed`, `precipitation`, `sprayWindow`, `frostRisk`
- `AgriParcelOperation`: `refCrop`, `quantityApplied`, `unitCode`, `notes`
- `AgriFertilizer`: `formulationType`, `stockQuantity`, `supplierName`, `organicCertified`
- `AgriParcelRecord`: `soilMoistureVwc`, `soilTemperature`, `airTemperature`, `batteryLevel`, `signalStrength`

## Loading data into Orion Context Broker

Example (Orion-LD, one file at a time):

```bash
curl -iX POST \
  'http://localhost:1026/ngsi-ld/v1/entityOperations/upsert' \
  -H 'Content-Type: application/ld+json' \
  -H 'Link: <https://uri.fiware.org/ns/data-models>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"' \
  --data-binary @seed_farms.json
```

Repeat for each `seed_*.json` file.

## Loading into PostgreSQL/PostGIS via script

Recommended approach:

1. Parse each JSON array with a loader script (Python/Node).
2. Map NGSI-LD entities to relational projection tables, for example:
   - `agri_farm_projection`
   - `agri_parcel_projection`
   - `weather_observed_projection`
   - `parcel_record_projection`
3. Upsert by `id` and keep `dateObserved` indexed for time-series queries.

## IoT sensor simulation coverage

Simulated IoT telemetry is provided for:

- Parcel: `urn:ngsi-ld:AgriParcel:farm001:parcel01`
- Source tag: `iot:soil-probe:oleiros-node-01`
- Files involved:
  - `seed_parcel_records.json`
  - `seed_weather_observed.json` (for moisture-rainfall correlation)

## Known simplifications vs real data

- Weather and sensor values are synthetic but realistic, not real station feeds.
- Parcel polygons are realistic approximations for demos, not cadastral-legal boundaries.
- Crop catalog entries are simplified as `AgriCrop` entities and not full season lifecycle instances.
- Forecast values are deterministic and scenario-oriented (frost/rain/spray demonstrations).
- No live API rate-limit behavior or sensor dropout/noise model is included.
