# TerraGalicia DSS — Product Requirements Document (PRD)

**Version**: 1.2
**Date**: May 2026
**Status**: Partial MVP — Core features operational
**Target MVP Delivery**: Q3 2026 (12 weeks from start)

---

## 1. Overview

TerraGalicia is an open-source, FIWARE-standardized agricultural decision-support web application designed to democratize precision farming for smallholder farmers and cooperatives in A Coruña and the broader Galician region. The application leverages freely available EU open data (SIGPAC parcel boundaries, weather forecasts, soil surveys) combined with FIWARE NGSI-LD standards and rule-based crop suitability modeling to provide transparent, explainable recommendations on planting dates, crop selection, and water management—specific to each farmer's parcel and the Galician bioregion.

---

## 2. User Personas

### Persona A: João Martins — Small Farmer, Individual Operation

**Profile**:
- Age: 48, fourth-generation farmer in A Coruña (Oleiros municipality)
- Farm size: 8 hectares split across 4 parcels (millo, pataca, wine grapes for local cider production)
- Tech comfort: Intermediate (uses WhatsApp, online banking, but not specialized agri-software)
- Education: Secondary school; some formal agricultural training 30 years ago
- Primary language: Galician (reads Spanish; minimal English)

**Main Goals**:
- Increase millo yield by 10–15% without proportional input cost increase
- Reduce late-season pest losses (powdery mildew, common in wet Galician summers)
- Make planting decisions by mid-April to align with market timing
- Understand soil condition better and optimize fertilizer spend

**Key Frustrations with Current Tools**:
- AEMET website is technical and not farm-oriented; requires manual interpretation
- No local recommendation on when/what to plant; relies on neighbors' experience or radio broadcasts
- Concerns about proprietary farm apps (e.g., CropX): data privacy, subscription cost (€50–100/month per farm), vendor dependency
- Extension agent visits only 1–2 times per season; misses critical decisions

**Primary Use Cases in TerraGalicia**:
1. Each March, log in and select his 4 parcels; see suitability scores for millo, pataca, wine grapes
2. Check 7-day weather forecast integrated on the map; decide if current window is good for spraying
3. Review historical soil moisture and rainfall charts (past 2 years) to spot patterns
4. Click on recommended planting date for millo; read AI explanation
5. Log operation (planting date, fertilizer used, seed variety) and export data annually for EU subsidy reports

---

### Persona B: Rosa García Fernández — Cooperative Manager

**Profile**:
- Age: 52, manages 180 hectares across 28 member farms (mix of millo, pataca, kiwi, small wine vineyard collective)
- Tech comfort: Advanced (Excel power user, some CRM/ERP experience)
- Education: Agronomic diploma; cooperative management course
- Primary language: Galician; fluent Spanish; reads English

**Main Goals**:
- Optimize collective crop planning: align member planting dates to share equipment, reduce pest pressure via staggered sowing
- Track members' fertilizer inventory and bulk-purchase at cooperative discount
- Demonstrate transparency and sustainability for EU subsidy audits and potential organic certification
- Reduce advice burden on extension agents by providing evidence-based recommendations

**Primary Use Cases in TerraGalicia**:
1. Dashboard showing all 28 member parcels on a single map; filter by suitability recommendation
2. Export weekly parcel report: crop, suitability score, weather, recommended actions
3. Identify "anchor farms" (best conditions for early planting) and coordinate staggered operations
4. Historical portfolio view: overlay past 3 seasons of member operations, yields, pest incidents
5. Generate compliance report for EU subsidies

---

### Persona C: Miguel Álvarez García — Extension Agent

**Profile**:
- Age: 38, works for Xunta de Galicia agricultural extension office serving A Coruña municipalities
- Tech comfort: Intermediate-to-Advanced (GIS background, familiar with AgriMap and other regional tools)
- Education: Agricultural engineering degree; 8 years in extension service
- Primary language: Galician; fluent Spanish; basic English

**Main Goals**:
- Provide timely, evidence-based recommendations to 60+ farmers in his district during critical decision windows
- Track outcomes of recommendations to improve advisories
- Reduce in-person visit burden by offering reliable self-serve tool
- Demonstrate impact of extension services to Xunta management

**Primary Use Cases in TerraGalicia**:
1. Monitor dashboard showing all farms in his district; trigger alerts when conditions change
2. Generate weekly advisory bulletin for district
3. Link each recommendation to justification (weather, soil, pest model) for farmer education
4. Post-season review: compare his recommendations vs. actual farmer choices vs. outcomes
5. Share best practice: identify and highlight top-performing farms

---

## 3. User Stories

### MAP & NAVIGATION
- **US-MAP-001**: As **João** (farmer), I want to view all my parcels as interactive polygons on a satellite map so that I can quickly identify which field I want to analyze.
- **US-MAP-002**: As **Rosa** (cooperative manager), I want to zoom and pan across a map of all 28 member parcels so that I can see spatial patterns (e.g., all parcels in high-altitude zone at risk from late frost).
- **US-MAP-003**: As **Miguel** (extension agent), I want to overlay a pest risk heatmap on the satellite view so that I can visually identify areas needing intervention before farmers call with problems.
- **US-MAP-004**: As **João**, I want to search for a parcel by municipality name or cadastral ID so that I can find my land without manually scrolling the map.

### PARCEL DETAIL & METADATA
- **US-PARCEL-001**: As **João**, I want to click a parcel and see its metadata (size, cadastral ID, municipality, soil type, GPS center) so that I can confirm I've selected the correct field.
- **US-PARCEL-002**: As **Rosa**, I want to see which cooperative member owns each parcel and their contact info so that I can quickly coordinate operations with them.
- **US-PARCEL-003**: As **Miguel**, I want to view a parcel's 3-year crop history so that I can recommend crop rotation and identify compliance issues.
- **US-PARCEL-004**: As **João**, I want to log a new operation (planting, fertilizing, spraying) with date, product name, and quantity so that I maintain an audit trail for subsidies.

### CROP SUITABILITY & RECOMMENDATION
- **US-CROP-001**: As **João**, I want to see a color-coded suitability score (green/yellow/red) for each recommended crop for my parcel so that I instantly know which crops are feasible.
- **US-CROP-002**: As **Rosa**, I want to compare suitability scores across all member parcels and identify which farms should plant millo vs. pataca so that I optimize cooperative resource allocation.
- **US-CROP-003**: As **João**, I want to click on a specific crop and read an explanation so that I understand the reasoning, not just a score.
- **US-CROP-004**: As **Miguel**, I want to adjust crop suitability weights and see how recommendations change so that I can tailor advice for organic-converting farmers.

### PLANTING DATE & TIMING
- **US-TIMING-001**: As **João**, I want to select a target crop and see the recommended planting window with explanations so that I know when to schedule equipment and labor.
- **US-TIMING-002**: As **Rosa**, I want to stagger member planting dates by parcel risk level so that disease pressure is spread and shared equipment isn't overbooked.
- **US-TIMING-003**: As **João**, I want to input my planned sowing date and receive real-time warnings so that I can adjust before committing resources.

### WEATHER & ENVIRONMENTAL DATA
- **US-WEATHER-001**: As **João**, I want to see the current 7-day forecast overlaid on my parcel map so that I decide if today is a good day to spray or irrigate.
- **US-WEATHER-002**: As **Miguel**, I want to trigger automatic alerts to all farmers when frost is forecast for their altitude so that they can take protective measures.
- **US-WEATHER-003**: As **João**, I want to see optimal spray windows highlighted so that I can call the contractor at the right time.

### STATUS, INVENTORY, AND CONVERSATIONAL AI
- **US-STATUS-001**: As **João**, I want to see each parcel's current status as a color-coded overlay on the map so that I can immediately distinguish PLANTED, FALLOW, PREPARED, and HARVESTED parcels.
- **US-AI-001**: As **João**, I want to ask AgroCopilot in Galician or Spanish what I can plant on Parcela Norte so that I get parcel-specific advice instead of a generic answer.
- **US-CROP-005**: As **João**, I want to change sowing date, crop type, and irrigation assumptions in a what-if simulator so that I can compare success probabilities before I commit to planting.

---

## 4. Functional Requirements

### FR-MAP: Geospatial Map Module

| ID | Requirement | Details |
|---|---|---|
| FR-MAP-001 | Display SIGPAC parcel boundaries | Load from PostGIS (`recintos_sigpac`); render as GeoJSON on Leaflet canvas |
| FR-MAP-002 | Base layer toggle | OSM and PNOA (IGN ortofoto) via WMS; control via Leaflet layers button |
| FR-MAP-003 | Parcel selection and highlighting | Click parcel to open detail popup |
| FR-MAP-004 | Search by municipality and cadastral ID | Full-text search; autocomplete municipality names |
| FR-MAP-005 | Map layers toggle | User can show/hide: SIGPAC boundaries, satellite, weather overlay |
| FR-MAP-006 | Coordinate display | Show lat/lon in legend panel; live mouse position |
| FR-MAP-007 | Mobile-responsive map | Map occupies full viewport; panels slide in |

### FR-PARCEL: Parcel Detail and Management

| ID | Requirement | Details |
|---|---|---|
| FR-PARCEL-001 | Display parcel metadata | Cadastral ID, area (ha/m²), municipality, uso_sigpac, elevation, source |
| FR-PARCEL-002 | Show crop history | Past seasons: crop type, sowing date, harvest date (via operations log) |
| FR-PARCEL-004 | Log operations | User can add operation record: date, type (Sowing, Fertilizing, Spraying, Harvesting), product, quantity |
| FR-PARCEL-005 | Operation history | Chronological list of all logged operations for the parcel |
| FR-PARCEL-007 | Export parcel data | Download parcel metadata and operation history as CSV/JSON |

### FR-CROP: Crop Suitability and Recommendation Engine

| ID | Requirement | Details |
|---|---|---|
| FR-CROP-001 | Multi-crop suitability matrix | For selected parcel, display suitability score (0–100%) for 10 crops |
| FR-CROP-002 | Color-coded suitability bands | Green ≥70% (optimal), Yellow 40–70% (viable with risk), Red <40% (unsuitable) |
| FR-CROP-003 | Score justification | Expand each crop to see breakdown: pendiente, riego, mes, altitud scores |
| FR-CROP-007 | Recommended crop ranking | Sort crops by suitability score |
| FR-CROP-012 | Interactive what-if simulator | User adjusts sowing date, crop type, irrigation assumption; recalculate in real time |

### FR-WEATHER: Weather Integration Module

| ID | Requirement | Details |
|---|---|---|
| FR-WEATHER-001 | Current weather display | Show current conditions: temperature, humidity, wind, precipitation |
| FR-WEATHER-002 | 7-day forecast | Daily min/max temperature, precipitation probability, wind speed |
| FR-WEATHER-003 | Frost risk alerts | Visual alert when min temperature forecast drops below 0°C |

### FR-AI: AI Explanation Engine

| ID | Requirement | Details |
|---|---|---|
| FR-AI-009 | Natural language chat interface | Chat where farmers can ask questions in Galician or Spanish |
| FR-AI-011 | AgroCopilot context window | Each session pre-loaded with selected parcel's context |

### FR-STATUS: Parcel Status Management

| ID | Requirement | Details |
|---|---|---|
| FR-STATUS-001 | Status overlay on map | Color-coded overlay (PLANTADA, BARBECHO, PREPARADA, COSECHADA) visible on map |
| FR-STATUS-002 | Status update | User can change parcel status via popup selector; PATCHed to backend |
| FR-STATUS-006 | Status-based filtering | Map legend shows status color swatches; future: filter by status |

**Status semantics**:
- **PLANTED (PLANTADA)**: Active crop in the ground.
- **FALLOW (BARBECHO)**: Resting after harvest.
- **PREPARED (PREPARADA)**: Soil prepared and awaiting sowing.
- **HARVESTED (COSECHADA)**: Recently harvested.

---

## 5. Non-Functional Requirements

| Requirement | Specification |
|---|---|
| **Performance** | Map rendering (5000 parcels) <1 s with canvas renderer (implemented); SIGPAC API response <2 s for dense bboxes |
| **Scalability** | Horizontal scaling via Docker/Kubernetes |
| **Availability** | Graceful degradation if weather API is down (cached results) |
| **Security** | JWT authentication; no plaintext passwords; GDPR and LPDP compliance |
| **Data Privacy** | Farmer data never shared without consent; cooperative pooling opt-in |
| **Localization** | UI in Galician (primary), Spanish; date formats local (European) |
| **Database** | PostgreSQL 15 with PostGIS 3.4 for spatial queries; TimescaleDB in stack for time-series |
| **API Documentation** | OpenAPI 3.0 spec; Swagger UI available at `/api/docs` |
| **Compliance** | EU interoperability standards (NGSI-LD, FIWARE); open-source license (AGPL 3.0) |

---

## 6. Data Requirements

### recintos_sigpac (PostGIS)

Source: SIGPAC official `.gpkg` files (provincia 15, A Coruña). ~3.87 M features. See `docs/data_model.md` for the full column schema.

### FIWARE NGSI-LD Entities

| Entity | Source | Storage |
|---|---|---|
| `AgriFarm` | Manual entry | Orion Context Broker + PostgreSQL |
| `AgriParcel` | SIGPAC cadastral data | PostGIS + Orion |
| `AgriCrop` | Pre-defined catalog | PostgreSQL |
| `AgriParcelOperation` | Farmer manual entry | PostgreSQL + Orion |
| `WeatherObserved` / `WeatherForecast` | Open-Meteo API | Redis cache; future: TimescaleDB via QuantumLeap |

---

## 7. MVP Scope

### Implementado y operativo

**Frontend**:
- Mapa Leaflet con parcelas SIGPAC desde PostGIS; canvas renderer, hasta 5.000 recintos por petición
- Banner de truncado cuando hay >5.000 parcelas en el viewport
- Capas base OSM y ortofoto PNOA (IGN)
- Zoom mínimo 15 para cargar parcelas; aviso informativo por debajo
- Popup de parcela: ID catastral, área (toggle ha/m²), municipio, uso SIGPAC, fuente del dato
- Selector de estado de parcela (PLANTADA / BARBECHO / PREPARADA / COSECHADA); PATCH al backend
- Overlay de color por estado de parcela y leyenda
- Ranking de aptitud de 10 cultivos con barras de puntuación y desglose de factores
- Panel de tiempo: condiciones actuales + previsión 7 días (Open-Meteo)
- AgroCopilot: interfaz de chat con respuestas de fallback cuando no hay LLM configurado
- Simulador what-if: fecha de siembra, tipo de cultivo, disponibilidad de riego

**Backend**:
- FastAPI REST API con endpoints: `/auth/login`, `/sigpac/parcels`, `/sigpac/nearby`, `/parcels/{id}`, `/parcels/{id}/suitability`, `/parcels/{id}/operations`, `/weather`, `/copilot/chat`, `/simulator/whatif`
- PostgreSQL + PostGIS: tabla `recintos_sigpac` (~3,87 M features), índices GiST
- Redis: caché de bbox SIGPAC y suitability (TTL 24 h)
- FIWARE Orion CB activo: almacena entidades `AgriFarm`, `AgriParcel`, operaciones en NGSI-LD
- JWT auth: access token + refresh token
- Cadena de fallback SIGPAC: PostGIS → .gpkg local → mock data (5 parcelas)
- Motor de aptitud de cultivos: 10 cultivos, reglas agronómicas por pendiente/riego/mes/altitud

### Trabajo futuro (Fase 2)

- **Persistencia del estado de parcela en BD**: actualmente el estado se guarda en memoria y se pierde al recargar. La estructura de la BD y el endpoint PATCH están implementados; falta conectar el flujo completo con PostgreSQL u Orion.
- **LLM real para AgroCopilot**: el cliente (`LLMClient`) está implementado y listo para conectar a Ollama o cualquier API OpenAI-compatible. Solo falta configurar `LLM_API_KEY` y `LLM_API_BASE`.
- **Tiles vectoriales MVT**: con el canvas renderer actual hay un límite de 5.000 recintos por petición. La solución correcta es generar tiles vectoriales (MVT) desde PostGIS con `pg_tileserv` para servir parcelas a cualquier nivel de zoom.
- **Integración activa IoT Agent + QuantumLeap**: el stack FIWARE completo arranca con `docker-compose up -d` pero no hay flujos de datos pasando por el IoT Agent ni suscripciones activas en QuantumLeap. El objetivo es ingestar datos meteorológicos a través del IoT Agent para historizar en TimescaleDB.
- **Dashboards Grafana**: Grafana está en el stack y accesible en `http://localhost:3001`, pero sin paneles configurados. Se crearían dashboards con históricos de tiempo, distribución de usos del suelo y métricas de la aplicación.
- **Alertas de heladas y plagas**: requiere sistema de notificaciones y modelos fenológicos para plagas. Depende de tener la integración meteorológica completada.
- **Dashboard cooperativo multi-parcela**: la persona de Rosa (gestora de cooperativa) requiere una vista consolidada de todas las parcelas de los miembros. El modelo de datos lo soporta; falta la interfaz de gestión multi-usuario.
- **Capacidad offline**: service worker para funcionamiento sin conexión con los últimos datos descargados.
- **Toggle de tema claro/oscuro**: el CSS ya usa variables de color; requiere trabajo en los estilos Leaflet y componentes React.
- **Radar de precipitación animado**: capa de tiles meteorológicos animados sobre el mapa (RainViewer u Open-Meteo radar).

---

## 8. Success Metrics

| KPI | Target (End of Year 1) | Rationale |
|---|---|---|
| **User Adoption** | 500+ registered farmers in A Coruña; 50% monthly active users | Core adoption signal |
| **Planting Decision Accuracy** | 70%+ of farmers report recommendations aligned with their planting choice | Core value proposition |
| **Data Quality Score** | 80%+ of parcels with operation history logged | Enables better recommendations; supports EU audits |
| **Cooperative Uptake** | 5+ agricultural cooperatives actively using portfolio dashboard | Validates cooperative value-add |
| **System Performance** | Map load <2 s on 4G; 99.5% uptime; <1% data loss incidents | Technical reliability |
| **Cost Per Recommendation** | <€0.10/farmer/month operational cost | Proves economic sustainability for smallholders |

---

## 9. Implementation Roadmap

**Weeks 1–2: Infrastructure & Data Integration**
- Set up PostgreSQL + PostGIS, TimescaleDB, FIWARE Orion CB, Redis
- Ingest SIGPAC parcel data (A Coruña, ~3.87 M parcels via QGIS/Drive)
- Integrate Open-Meteo weather API

**Weeks 3–4: Frontend Core**
- Leaflet map with SIGPAC boundaries via PostGIS
- Parcel selection and detail popup
- Canvas renderer for performance

**Weeks 5–6: Crop Suitability & Recommendations**
- Rule-based suitability engine (10 crops, 4 factors)
- Score display with color bands and breakdown

**Weeks 7–8: Backend API & Authentication**
- FastAPI CRUD endpoints for parcels, crops, weather, operations
- JWT authentication
- Redis caching layer

**Weeks 9–10: Weather, AgroCopilot, WhatIf Simulator**
- 7-day forecast panel
- AgroCopilot chat interface
- What-if simulator endpoint

**Weeks 11–12: Testing, Documentation, Packaging**
- Integration testing
- Documentation update
- Docker Compose packaging and delivery

---

## Known Unknowns & Risks

1. **SIGPAC Data Licensing**: The `.gpkg` files are free to use for academic projects. Confirm licensing before commercial deployment.
2. **LLM Provider & Cost**: Current implementation uses fallback responses. Connecting to OpenAI API or a local Ollama instance is straightforward but requires configuration and may incur cost.
3. **FIWARE IoT Agent**: Full sensor integration requires deploying physical IoT sensors or connecting real weather station APIs—out of scope for the academic MVP.
4. **Parcel Status Persistence**: The PATCH endpoint exists, but backend storage in PostgreSQL vs. Orion needs to be decided and implemented before shipping to production.

---

## Document Version History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | Apr 2026 | Product Team | Initial PRD; MVP scope defined |
| 1.1 | May 2026 | Engineering Team | Partial MVP implemented: SIGPAC viewer (PostGIS + canvas renderer), parcel popup with suitability, weather panel, AgroCopilot, WhatIf simulator, JWT auth |
| 1.2 | May 2026 | Engineering Team | Fixed escaped markdown; Section 7 updated to reflect real implementation state vs. work planned for Phase 2 |
