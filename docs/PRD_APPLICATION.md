**\# TerraGalicia DSS — Product Requirements Document (PRD)**

**\*\*Version\*\***: 1.0    
**\*\*Date\*\***: April 2026    
**\*\*Status\*\***: Draft for Technical Review    
**\*\*Target MVP Delivery\*\***: Q3 2026 (12 weeks from start)

**\---**

**\#\# 1\. Overview**

TerraGalicia is an open-source, FIWARE-standardized agricultural decision-support web application designed to democratize precision farming for smallholder farmers and cooperatives in A Coruña and the broader Galician region. The application leverages freely available EU open data (SIGPAC parcel boundaries, Copernicus satellite imagery, AEMET/MeteoGalicia weather, CSIC soil surveys) combined with IoT sensor networks and AI-powered crop suitability modeling to provide transparent, explainable recommendations on planting dates, crop selection, pest risks, and water management—specific to each farmer's parcel and the Galician bioregion. By eliminating vendor lock-in through FIWARE NGSI-LD standards and embedding LLM-generated reasoning into every recommendation, TerraGalicia empowers farmers to make data-driven decisions while maintaining data sovereignty and enabling cooperative-scale resource optimization.

**\---**

**\#\# 2\. User Personas**

**\#\#\# Persona A: João Martins — Small Farmer, Individual Operation**

**\*\*Profile\*\***:  
\- Age: 48, fourth-generation farmer in A Coruña (Oleiros municipality)  
\- Farm size: 8 hectares split across 4 parcels (millo, pataca, wine grapes for local cider production)  
\- Tech comfort: Intermediate (uses WhatsApp, online banking, but not specialized agri-software)  
\- Education: Secondary school; some formal agricultural training 30 years ago  
\- Primary language: Galician (reads Spanish; minimal English)

**\*\*Main Goals\*\***:  
\- Increase millo yield by 10–15% without proportional input cost increase  
\- Reduce late-season pest losses (powdery mildew, common in wet Galician summers)  
\- Make planting decisions by mid-April to align with market timing  
\- Understand soil condition better and optimize fertilizer spend

**\*\*Key Frustrations with Current Tools\*\***:  
\- AEMET website is technical and not farm-oriented; requires manual interpretation  
\- No local recommendation on when/what to plant; relies on neighbors' experience or radio broadcasts  
\- Concerns about proprietary farm apps (e.g., CropX): data privacy, subscription cost (€50–100/month per farm), vendor dependency  
\- Extension agent visits only 1–2 times per season; misses critical decisions

**\*\*Primary Use Cases in TerraGalicia\*\***:  
1\. Each March, log in and select his 4 parcels; see suitability scores for millo, pataca, wine grapes  
2\. Check 7-day weather forecast integrated on the map; decide if current window is good for spraying  
3\. Review historical soil moisture and rainfall charts (past 2 years) to spot patterns  
4\. Click on recommended planting date for millo; read AI explanation: "Sow April 10–25: frost risk drops after April 8, soil temp reaches 12°C \~April 12\. Early sowing (April 10\) risks frost; late sowing (\>May 5\) shortens season in cool Galician climate."  
5\. Log operation (planting date, fertilizer used, seed variety) and export data annually for EU subsidy reports

**\---**

**\#\#\# Persona B: Rosa García Fernández — Cooperative Manager (Sociadade Agraria de Transformación — SAT)**

**\*\*Profile\*\***:  
\- Age: 52, manages 180 hectares across 28 member farms (mix of millo, pataca, kiwi, small wine vineyard collective)  
\- Tech comfort: Advanced (Excel power user, some CRM/ERP experience)  
\- Education: Agronomic diploma; cooperative management course  
\- Primary language: Galician; fluent Spanish; reads English

**\*\*Main Goals\*\***:  
\- Optimize collective crop planning: align member planting dates to share equipment, reduce pest pressure via staggered sowing  
\- Track members' fertilizer inventory and bulk-purchase at cooperative discount  
\- Demonstrate transparency and sustainability for EU subsidy audits and potential organic certification  
\- Reduce advice burden on extension agents by providing evidence-based recommendations

**\*\*Key Frustrations with Current Tools\*\***:  
\- Current approach: email spreadsheets to members, manually aggregate data in Excel, no real-time visibility into who planted what  
\- Data fragmentation: some members use WhatsApp photos of their parcels, others have no records; no standardized format  
\- No easy way to benchmark member performance or identify best practices  
\- Existing web tools (Agworld) too expensive for cooperative model; cost-per-hectare prohibitive for smallholders

**\*\*Primary Use Cases in TerraGalicia\*\***:  
1\. Dashboard showing all 28 member parcels on a single map; filter by suitability recommendation (e.g., "all parcels recommended for millo")  
2\. Export weekly parcel report: crop, suitability score, weather, recommended actions → send to members via email/WhatsApp  
3\. Identify "anchor farms" (best conditions for early planting) and "latecomer farms" (risk of frost/disease); coordinate staggered operations  
4\. Historical portfolio view: overlay past 3 seasons of member operations, yields, pest incidents; identify systemic issues  
5\. Generate compliance report for EU (subsidies, rotation, sustainability): prove diversity, timing, soil management across cooperative

**\---**

**\#\#\# Persona C: Miguel Álvarez García — Extension Agent (Técnico en Extensión Agraria)**

**\*\*Profile\*\***:  
\- Age: 38, works for Xunta de Galicia agricultural extension office serving A Coruña municipalities  
\- Tech comfort: Intermediate-to-Advanced (GIS background, familiar with AgriMap and other regional tools)  
\- Education: Agricultural engineering degree; 8 years in extension service  
\- Primary language: Galician; fluent Spanish; basic English

**\*\*Main Goals\*\***:  
\- Provide timely, evidence-based recommendations to 60+ farmers in his district during critical decision windows  
\- Track outcomes of recommendations (follow-up surveys, yield reports) to improve advisories  
\- Reduce in-person visit burden by offering reliable self-serve tool; reserve visits for complex/problem cases  
\- Demonstrate impact of extension services to Xunta management (quantify farmer uptake, yield improvement)

**\*\*Key Frustrations with Current Tools\*\***:  
\- Current system: Phone calls and field visits; high travel time, limited documentation  
\- No standardized way to track recommendation uptake or outcomes; no feedback loop  
\- Existing tools (DSSAT, regional crop calendar) not web-based; farmers must schedule in-person training  
\- Regional recommendations published once per season; can't adapt to real-time weather shifts or pest outbreaks

**\*\*Primary Use Cases in TerraGalicia\*\***:  
1\. Monitor dashboard showing all farms in his district; trigger alerts when conditions change (e.g., "frost risk weekend; spray fungicide now")  
2\. Generate weekly advisory bulletin for district: "This week: millo sowing window optimal for parcels at altitude \<200m; spray powdery mildew in vineyards tomorrow morning"  
3\. Link each recommendation to justification (weather, soil, pest model) for farmer education and accountability  
4\. Post-season review: compare his recommendations vs. actual farmer choices vs. outcomes; refine model inputs  
5\. Share best practice: identify and highlight top-performing farms; encourage peer learning

**\---**

**\#\# 3\. User Stories**

**\#\#\# MAP & NAVIGATION**  
\- **\*\*US-MAP-001\*\***: As **\*\*João\*\*** (farmer), I want to view all my parcels as interactive polygons on a satellite map so that I can quickly identify which field I want to analyze.  
\- **\*\*US-MAP-002\*\***: As **\*\*Rosa\*\*** (cooperative manager), I want to zoom and pan across a map of all 28 member parcels so that I can see spatial patterns (e.g., all parcels in high-altitude zone at risk from late frost).  
\- **\*\*US-MAP-003\*\***: As **\*\*Miguel\*\*** (extension agent), I want to overlay a pest risk heatmap on the satellite view so that I can visually identify areas needing intervention before farmers call with problems.  
\- **\*\*US-MAP-004\*\***: As **\*\*João\*\***, I want to search for a parcel by municipality name (e.g., "Oleiros") or cadastral ID so that I can find my land without manually scrolling the map.

**\#\#\# PARCEL DETAIL & METADATA**  
\- **\*\*US-PARCEL-001\*\***: As **\*\*João\*\***, I want to click a parcel and see its metadata (size, cadastral ID, municipality, soil type, GPS center) so that I can confirm I've selected the correct field.  
\- **\*\*US-PARCEL-002\*\***: As **\*\*Rosa\*\***, I want to see which cooperative member owns each parcel and their contact info so that I can quickly coordinate operations with them.  
\- **\*\*US-PARCEL-003\*\***: As **\*\*Miguel\*\***, I want to view a parcel's 3-year crop history (what was planted in 2023, 2024, 2025\) so that I can recommend crop rotation and identify compliance issues.  
\- **\*\*US-PARCEL-004\*\***: As **\*\*João\*\***, I want to log a new operation (planting, fertilizing, spraying) with date, product name, and quantity so that I maintain an audit trail for subsidies.

**\#\#\# CROP SUITABILITY & RECOMMENDATION**  
\- **\*\*US-CROP-001\*\***: As **\*\*João\*\***, I want to see a color-coded suitability score (green/yellow/red) for each recommended crop (millo, pataca, grelos, kiwi) for my parcel so that I instantly know which crops are feasible.  
\- **\*\*US-CROP-002\*\***: As **\*\*Rosa\*\***, I want to compare suitability scores across all member parcels and identify which farms should plant millo (for collective discount on seed) vs. pataca so that I optimize cooperative resource allocation.  
\- **\*\*US-CROP-003\*\***: As **\*\*João\*\***, I want to click on a specific crop (e.g., millo) and read an AI-generated explanation ("78% success: soil pH 6.2 is optimal, but expect 15% yield penalty due to late-season waterlogging risk") so that I understand the reasoning, not just a score.  
\- **\*\*US-CROP-004\*\***: As **\*\*Miguel\*\***, I want to adjust crop suitability weights (e.g., prioritize organic certification over yield) and see how recommendations change so that I can tailor advice for organic-converting farmers.

**\#\#\# PLANTING DATE & TIMING**  
\- **\*\*US-TIMING-001\*\***: As **\*\*João\*\***, I want to select a target crop and see the recommended planting window (e.g., "April 10–May 5") with explanations (frost calendar, soil temperature, market timing) so that I know when to schedule equipment and labor.  
\- **\*\*US-TIMING-002\*\***: As **\*\*Rosa\*\***, I want to stagger member planting dates by parcel risk level so that disease pressure is spread and shared equipment isn't overbooked.  
\- **\*\*US-TIMING-003\*\***: As **\*\*João\*\***, I want to input my planned sowing date and receive real-time warnings (e.g., "Late sowing; risk of frost damage and shortened season in cool Galician climate") so that I can adjust before committing resources.

**\#\#\# WEATHER & ENVIRONMENTAL DATA**  
\- **\*\*US-WEATHER-001\*\***: As **\*\*João\*\***, I want to see the current 7-day MeteoGalicia forecast overlaid on my parcel map (temperature, rain, frost risk) so that I decide if today is a good day to spray or irrigate.  
\- **\*\*US-WEATHER-002\*\***: As **\*\*Miguel\*\***, I want to trigger automatic alerts to all farmers when frost is forecast for their altitude so that they can take protective measures (frost management, variety selection).  
\- **\*\*US-WEATHER-003\*\***: As **\*\*João\*\***, I want to see optimal spray windows (low wind, humidity 60–80%, no rain) highlighted so that I can call the contractor at the right time.

**\#\#\# HISTORICAL DATA & ANALYTICS**  
\- **\*\*US-HISTORY-001\*\***: As **\*\*João\*\***, I want to view time-series charts of historical soil moisture, temperature, and rainfall for my parcel (past 2 years) so that I identify dry/wet seasons and adjust irrigation.  
\- **\*\*US-HISTORY-002\*\***: As **\*\*Rosa\*\***, I want to compare cooperative-wide yield trends and identify which members are achieving top performance so that I can facilitate peer learning.  
\- **\*\*US-HISTORY-003\*\***: As **\*\*Miguel\*\***, I want to correlate past weather anomalies (e.g., late frost in 2024\) with member outcomes (yield loss, crop failure) so that I refine future recommendations.

**\#\#\# PEST & DISEASE ALERTS**  
\- **\*\*US-PEST-001\*\***: As **\*\*João\*\***, I want to receive a push notification when weather conditions favor powdery mildew in his vineyard (humidity \>80%, temperature 15–25°C, 3-day duration) so that I schedule preemptive spraying.  
\- **\*\*US-PEST-002\*\***: As **\*\*Miguel\*\***, I want to publish a district-wide pest alert (e.g., "Hessian fly detected in northern parcels; spray immediately") so that neighboring farmers can take preventive action.

**\#\#\# PORTFOLIO & COOPERATIVE MANAGEMENT**  
\- **\*\*US-PORTFOLIO-001\*\***: As **\*\*Rosa\*\***, I want a dashboard showing all member parcels, their suitability recommendations, and current weather so that I generate a weekly bulletin.  
\- **\*\*US-PORTFOLIO-002\*\***: As **\*\*Rosa\*\***, I want to export a compliance report (crop rotation, sustainability metrics, operation dates) so that I demonstrate cooperative's EU subsidy eligibility.

**\#\#\# STATUS, INVENTORY, AND CONVERSATIONAL AI**  
\- **\*\*US-STATUS-001\*\***: As **\*\*João\*\***, I want to see each parcel's current status as a color-coded overlay on the map so that I can immediately distinguish PLANTED, FALLOW, PREPARED, and HARVESTED parcels.  
\- **\*\*US-AI-001\*\***: As **\*\*João\*\***, I want to ask AgroCopilot in Galician or Spanish what I can plant on Parcela Norte so that I get parcel-specific advice instead of a generic answer.  
\- **\*\*US-CROP-005\*\***: As **\*\*João\*\***, I want to change sowing date, crop type, and irrigation assumptions in a what-if simulator so that I can compare success probabilities before I commit to planting.  
\- **\*\*US-FERT-001\*\***: As **\*\*Rosa\*\***, I want to receive an alert when cooperative fertilizer stock is below the recommended threshold so that I can reorder before the next fertilizing window.  
\- **\*\*US-CROP-006\*\***: As **\*\*Miguel\*\***, I want the system to flag rotation non-compliance when a proposed crop repeats the same family too soon so that I can protect subsidy eligibility and advise corrective action.

**\---**

**\#\# 4\. Functional Requirements**

**\#\#\# FR-MAP: Geospatial Map Module**

| ID | Requirement | Details |  
|---|---|---|  
| FR-MAP-001 | Display SIGPAC parcel boundaries | Load from official SIGPAC WFS service or local PostGIS; render as GeoJSON on Leaflet |  
| FR-MAP-002 | Satellite imagery base layer | Integrate Copernicus Sentinel-2 (RGB composite) or OSM satellite; update monthly |  
| FR-MAP-003 | Parcel selection and highlighting | Click parcel to highlight; open detail panel on right side |  
| FR-MAP-004 | Search by municipality and cadastral ID | Full-text search; autocomplete municipality names (A Coruña concellos) |  
| FR-MAP-005 | Map layers toggle | User can show/hide: SIGPAC boundaries, satellite, soil type, pest risk heatmap, weather overlay |  
| FR-MAP-006 | Zoom to user's farms on login | Auto-center and zoom to bounding box of farmer's parcels |  
| FR-MAP-007 | Coordinate display | Show lat/lon and cadastral ID on parcel click |  
| FR-MAP-008 | Mobile-responsive map | Map occupies 70% of screen on mobile; detail panel slides in from right |

**\---**

**\#\#\# FR-PARCEL: Parcel Detail and Management**

| ID | Requirement | Details |  
|---|---|---|  
| FR-PARCEL-001 | Display parcel metadata | Cadastral ID, GPS center, area (ha), municipality, soil type (from CSIC), elevation |  
| FR-PARCEL-002 | Show crop history | Past 3 seasons: crop type, sowing date, harvest date, estimated yield (if recorded) |  
| FR-PARCEL-003 | Link to soil test data | If available (manual upload or linked to regional lab): pH, N-P-K, organic matter, texture |  
| FR-PARCEL-004 | Log operations | User can add operation record: date, type (Sowing, Fertilizing, Spraying, Harvesting), product, quantity, unit |  
| FR-PARCEL-005 | Operation history timeline | Chronological list of all logged operations for the parcel; editable/deletable by owner |  
| FR-PARCEL-006 | Ownership and permissions | Link to AgriFarm entity; cooperative members can see pooled parcels; extension agents see read-only view |  
| FR-PARCEL-007 | Export parcel data | Download parcel metadata \+ operation history as CSV/JSON (NGSI-LD compliant) |  
| FR-PARCEL-008 | Parcel comparison tool | Select 2–3 parcels and compare: size, soil, crop history, current recommendations |

**\---**

**\#\#\# FR-CROP: Crop Suitability and Recommendation Engine**

| ID | Requirement | Details |  
|---|---|---|  
| FR-CROP-001 | Multi-crop suitability matrix | For selected parcel, display suitability score (0–100%) for 12+ crops: millo, pataca, kiwi, Albariño, Mencía, grelos, repolo, trigo, centeo, others |  
| FR-CROP-002 | Color-coded suitability bands | Green: 80–100% (optimal), Yellow: 50–80% (viable with risk), Red: \<50% (unsuitable) |  
| FR-CROP-003 | Score justification | Click a crop to expand explanation: soil pH vs. requirement, rainfall vs. need, frost risk, pest susceptibility, market timing |  
| FR-CROP-004 | AI-generated explanations | For each crop recommendation, LLM generates a 2–3 sentence explanation in Galician/Spanish; include confidence level |  
| FR-CROP-005 | Model transparency | Include link to methodology: "Suitability based on soil (pH, texture, drainage), climate (rainfall, frost calendar, growing degree days), pest pressure (phenology model), and historical yield data from region" |  
| FR-CROP-006 | Scenario builder | User can adjust assumptions (e.g., "apply 50mm irrigation") and see how suitability changes |  
| FR-CROP-007 | Recommended crop ranking | Sort crops by suitability score; highlight top 3 as "Most Likely Success" |  
| FR-CROP-008 | Crop-specific guidance links | Link each crop to regional variety recommendations, subsidy eligibility, market contacts |

**\---**

**\#\#\# FR-WEATHER: Weather Integration Module**

| ID | Requirement | Details |  
|---|---|---|  
| FR-WEATHER-001 | Current weather display | Show MeteoGalicia/AEMET current conditions: temperature, humidity, wind, precipitation for parcel location |  
| FR-WEATHER-002 | 7-day forecast | Daily min/max temperature, precipitation probability, wind speed; update twice daily (6 AM, 3 PM) |  
| FR-WEATHER-003 | Frost risk alerts | If min temperature forecast to drop below 0°C within 72 hours: highlight alert on map and dashboard |  
| FR-WEATHER-004 | Spray window recommendation | Calculate optimal spray window: wind \<3 m/s, humidity 60–80%, no rain 24h before/after; display as green window on forecast |  
| FR-WEATHER-005 | Historical weather data | Time-series chart of daily temperature, rainfall, humidity for past 2 years (from AEMET reanalysis or QuantumLeap) |  
| FR-WEATHER-006 | Weather station proximity | Link to nearest AEMET/MeteoGalicia weather station; display distance and data source |  
| FR-WEATHER-007 | Weather alerts by altitude | For cooperative: differentiate forecast by parcel elevation (e.g., frost warning only for parcels \>200m) |  
| FR-WEATHER-008 | Soil moisture indicator | If available from IoT sensors or satellite-derived: display soil moisture trend; recommend irrigation timing |

**\---**

**\#\#\# FR-HISTORY: Historical Data and Analytics**

| ID | Requirement | Details |  
|---|---|---|  
| FR-HISTORY-001 | Yield historical chart | Plot past 3 seasons: crop type, estimated or recorded yield (t/ha); identify trends and anomalies |  
| FR-HISTORY-002 | Soil condition trends | If soil tests available: pH, EC, N-P-K over time; show if condition improving or declining |  
| FR-HISTORY-003 | Weather-yield correlation | Overlay historical weather (temperature, rainfall) with yield to identify climate stress periods |  
| FR-HISTORY-004 | Operation log export | User can export all logged operations (planting, fertilizing, spraying) with dates and quantities for EU subsidy audit |  
| FR-HISTORY-005 | Cooperative performance benchmark | For Rosa: show cooperative-wide average yield by crop; identify top/bottom performers (anonymized or with consent) |  
| FR-HISTORY-006 | Time-slider on map | User can drag timeline slider (past 2 years) to see how satellite imagery, crop recommendations changed over season |  
| FR-HISTORY-007 | Yield forecast chart | Project expected yield for current season based on historical model and current-year conditions (updated weekly) |

**\---**

**\#\#\# FR-ALERT: Pest and Weather Alerts**

| ID | Requirement | Details |  
|---|---|---|  
| FR-ALERT-001 | Frost alert automation | If forecast min temp \<0°C within 72h: auto-trigger notification to farmer (push notification, email, SMS \[if enabled\]) |  
| FR-ALERT-002 | Pest phenology alert | Calculate days-to-pest-risk based on growing degree days (GDD accumulation); alert when risk window opens (e.g., "Powdery mildew risk active; conditions optimal for next 3 days") |  
| FR-ALERT-003 | Alert thresholds customization | Farmer can set preferences (e.g., "notify only if frost \<-2°C", "disable pest alerts for organic crops") |  
| FR-ALERT-004 | Extension agent bulletin | Miguel can compose and send district-wide bulletin (affects multiple parcels); template with recommended actions |  
| FR-ALERT-005 | Alert history and tracking | Log all alerts sent; track if farmer acted (logged operation, feedback) or ignored |  
| FR-ALERT-006 | Multi-channel notification | Support push notification (web app), email, SMS (future); user configures preference |

**\---**

**\#\#\# FR-PORTFOLIO: Cooperative and Portfolio View**

| ID | Requirement | Details |  
|---|---|---|  
| FR-PORTFOLIO-001 | Cooperative dashboard | Rosa logs in; sees all member parcels, their suitability, current weather, recommended actions; filter by crop/municipality |  
| FR-PORTFOLIO-002 | Parcel ownership display | Each parcel shows member name, contact; clickable to view member's other parcels |  
| FR-PORTFOLIO-003 | Suitability consensus | Show % of cooperative parcels recommended for each crop (e.g., "72% recommended for millo, 20% for pataca, 8% other") |  
| FR-PORTFOLIO-004 | Staggered planting plan | Rosa can view a Gantt-chart-style timeline: member A plants millo week 1, member B plants week 2, etc.; identify equipment bottlenecks |  
| FR-PORTFOLIO-005 | Weekly bulletin generation | Rosa clicks "Generate Bulletin"; system produces a PDF/email-ready summary: recommended actions for each parcel/crop, weather forecast, alerts |  
| FR-PORTFOLIO-006 | Compliance report export | Rosa can export a report for EU subsidy audit: crop diversity, rotation compliance, soil management, operation records across cooperative |  
| FR-PORTFOLIO-007 | Bulk operation logging | Rosa can log an operation (e.g., "Bulk order millo seed: 5 tons") that applies to multiple member parcels; each member confirms receipt |  
| FR-PORTFOLIO-008 | Performance analytics | Comparative yield/quality charts across members; identify best practices to share |

**\---**

**\#\#\# FR-AI: AI Explanation Engine**

| ID | Requirement | Details |  
|---|---|---|  
| FR-AI-001 | Crop suitability explanations | For each crop recommendation, generate a 2–3 sentence Galician/Spanish explanation citing specific data: soil pH vs. optimal range, rainfall vs. requirement, frost risk (probability, dates), market timing, pest susceptibility |  
| FR-AI-002 | Planting date justification | Explain recommended window: frost risk calendar (specific dates), soil temperature progression, market peak, crop phenology |  
| FR-AI-003 | Weather-to-decision link | Connect current/forecast weather to actionable recommendation: "Frost warning Friday night; spray fungicide Thursday evening before cold settles" |  
| FR-AI-004 | Confidence intervals | Include uncertainty quantification: "78% success ± 12% (accounting for weather unpredictability and input variability)" |  
| FR-AI-005 | Farmer Q\&A chatbot | Free-form farmer questions (e.g., "Why not plant kiwi?") → LLM generates contextual response referencing parcel data, soil, weather |  
| FR-AI-006 | Explanation audit trail | Log each explanation generated; track if farmer acted on it and outcome (success, failure, ignored); feed back into model improvement |  
| FR-AI-007 | Localized language generation | All explanations in Galician (with Spanish option); culturally appropriate tone for smallholder farmers (not overly technical) |  
| FR-AI-008 | Model interpretability link | Each explanation includes link to technical documentation: "How we calculated this recommendation" (methodology, data sources) |

**\---**

**\#\#\# NEW MODULE: FR-STATUS: Parcel Status Management**

| ID | Requirement | Details |  
|---|---|---|  
| FR-STATUS-001 | Status overlay on map | Display parcel status as a color-coded overlay distinct from suitability scoring. The status must be visible in the map legend and parcel hover card. |  
| FR-STATUS-002 | Status transition validation | Enforce valid transitions only. For example, a parcel cannot move from FALLOW to PLANTED until the rest period defined by the crop rotation policy is complete. |  
| FR-STATUS-003 | Attached fertilization log | For each parcel status, show the most recent fertilization event: fertilizer name, application date, quantity, and responsible user. |  
| FR-STATUS-004 | Rest period calculator | Automatically calculate the mandatory rest period for FALLOW based on the previous crop type and parcel depletion history. The formula should be configurable by crop family and soil condition. |  
| FR-STATUS-005 | Status history timeline | Maintain a full transition log per parcel, including timestamps, user/system actor, and reason for the transition. |  
| FR-STATUS-006 | Status-based filtering | Allow users to filter the map by status, e.g., show only PREPARED parcels or highlight PLANTED parcels at risk of harvest delay. |

**\*\*Status semantics\*\***:  
\- **\*\*PLANTED\*\***: Active crop in the ground; store crop reference and sow date.  
\- **\*\*FALLOW (barbecho)\*\***: Resting after harvest; the system tracks the mandatory rest period before replanting.  
\- **\*\*PREPARED\*\***: Soil prepared and awaiting sowing.  
\- **\*\*HARVESTED\*\***: Recently harvested; expected to transition to FALLOW or PREPARED.

**\---**

**\#\#\# ADDITIONS TO FR-CROP: Intelligent Rotation and Scenario Analysis**

| ID | Requirement | Details |  
|---|---|---|  
| FR-CROP-009 | Rotation recommendation engine | Based on the last 3 crops planted in the parcel, recommend the next crop family. Prefer legumes after nitrogen-depleting cereals; avoid same-family repetition. |  
| FR-CROP-010 | Nutrient depletion alert | If soil N-P-K records show a depletion trend, flag parcels that need regenerative crops or fallow recovery before the next planting cycle. |  
| FR-CROP-011 | Rotation compliance check | Verify whether the proposed crop follows EU rotation guidelines for subsidy eligibility; alert the user if the proposal is non-compliant. |  
| FR-CROP-012 | Interactive what-if simulator | Let the user adjust sowing date via slider, crop type via dropdown, and irrigation assumption via toggle; recalculate success probability in real time with a response target under 2 seconds. |  
| FR-CROP-013 | Scenario comparison | Allow users to save and compare 2–3 scenarios side by side, such as "Millo April 15 vs Millo May 5 vs Pataca April 20". |

**\---**

**\#\#\# NEW MODULE: FR-FERTILIZER: Inventory and Fertilization Management**

| ID | Requirement | Details |  
|---|---|---|  
| FR-FERTILIZER-001 | Farm stock tracking | Track fertilizer stock per farm, including product name, NPK composition, quantity available, unit, and expiry date. |  
| FR-FERTILIZER-002 | Operation linkage and stock deduction | Link each fertilizing AgriParcelOperation to a specific fertilizer in inventory and deduct stock automatically when the operation is confirmed. |  
| FR-FERTILIZER-003 | Fertilizer recommendation | Recommend fertilizer type and quantity based on soil N-P-K deficit and target crop needs, reusing FR-CROP outputs where relevant. |  
| FR-FERTILIZER-004 | Stock shortage alerts | Alert the user when the recommended fertilizer is not in stock or falls below a minimum threshold needed for upcoming operations. |  
| FR-FERTILIZER-005 | Fertilization history and response | Provide parcel-level fertilization history showing what was applied, when, and the measured soil response using before/after comparison when soil tests are available. |

**\---**

**\#\#\# ADDITIONS TO FR-AI: AgroCopilot Conversational Assistant**

| ID | Requirement | Details |  
|---|---|---|  
| FR-AI-009 | Natural language chat interface | Provide a chat interface where farmers can ask questions in Galician or Spanish and receive answers grounded in their real parcel, weather, soil, and crop records. |  
| FR-AI-010 | Supported example queries | The system must handle questions such as: "¿Qué podo plantar agora na parcela Norte?", "¿Debo preocuparme pola chuvia de onte?", "¿Cando foi a última fertilización desta parcela?", and "¿Que cultivo me recomendas para maximizar ingresos este ano?". |  
| FR-AI-011 | AgroCopilot context window | Each chat session must be pre-loaded with the farmer's current parcels, weather, soil status, and last 5 operations so that answers remain parcel-specific rather than generic. |  
| FR-AI-012 | Proactive suggestions | AgroCopilot may initiate proactive alerts, for example: "Bon día, João. Frost is forecast this Friday. Your millo on Parcela Norte is at risk. Do you want me to show protective measures?" |

**\---**

**\#\#\# NEW MODULE: FR-RISK: Risk Analysis Layer \[Phase 2\]**

| ID | Requirement | Details |  
|---|---|---|  
| FR-RISK-001 | Environmental risk overlay | Display parcel-adjacent environmental risk layers such as proximity to industrial zones, roads, and an air quality index overlay. |  
| FR-RISK-002 | Water quality risk | If WaterQualityObserved shows electrical conductivity or nitrates above the configured threshold, flag the affected parcels as water-risk constrained. |  
| FR-RISK-003 | Extreme weather risk | Overlay heatwave, drought, and flooding probability layers derived from Copernicus or equivalent climate products. |  
| FR-RISK-004 | Legal risk overlay | Flag parcels within 500 m of active wind farms or biomass project planning zones; this requires Xunta de Galicia cadastral overlay data and must be treated as \[VERIFY\]. |

**\*\*Phase 2 note\*\***: FR-RISK is intentionally deferred from the MVP because it depends on additional external datasets, legal interpretation, and policy validation.

**\---**

**\#\# 5\. Non-Functional Requirements**

| Requirement | Specification |  
|---|---|  
| **\*\*Performance\*\*** | Page load \<2s on 4G mobile; map rendering (1000+ parcels) \<5s; API response time \<500ms for 95th percentile |  
| **\*\*Scalability\*\*** | Support 10,000+ concurrent users; 1,000+ parcels refreshing weather/alerts every 30 min; horizontal scaling via Docker/Kubernetes |  
| **\*\*Availability\*\*** | 99.5% uptime SLA; graceful degradation if AEMET/Copernicus APIs are down (cache \+ local model fallback) |  
| **\*\*Security\*\*** | HTTPS/TLS 1.3 minimum; JWT authentication; role-based access control (RBAC: farmer, cooperative manager, extension agent, admin); no plaintext passwords; comply with GDPR and Spanish data protection law (LPDP) |  
| **\*\*Data Privacy\*\*** | Farmer data (operations, yields) never shared without consent; cooperative pooling opt-in; extension agent view read-only and audited; anonymize performance benchmarks (don't reveal which farmer is top performer) |  
| **\*\*Accessibility\*\*** | WCAG 2.1 AA compliance; keyboard navigation; screen reader compatible; high-contrast mode option; Catalan/Spanish interface (Galician primary) |  
| **\*\*Mobile Responsiveness\*\*** | Responsive design; work on iOS/Android browsers; touch-friendly buttons (min 44x44px); landscape and portrait modes |  
| **\*\*Data Portability\*\*** | Full export in NGSI-LD JSON-LD format; CSV for spreadsheet import; compliance with EU open data standards |  
| **\*\*Offline Capability\*\*** | Display cached parcel map and last-known recommendations offline; sync operations when connection restored |  
| **\*\*Localization\*\*** | UI in Galician (primary), Spanish, Portuguese (future); number/date formats local (European); currency in EUR |  
| **\*\*Database\*\*** | PostgreSQL 14+ with PostGIS extension for spatial queries; TimescaleDB or CrateDB for time-series (weather, sensor data); backups daily, retention 90 days |  
| **\*\*API Documentation\*\*** | OpenAPI 3.0 spec; Swagger UI available for developers; rate limiting: 1000 req/day for free tier, 10,000 for registered farmers |  
| **\*\*Compliance\*\*** | EU interoperability standards (NGSI-LD, FIWARE); no proprietary lock-in; open-source license (AGPL 3.0 or Apache 2.0 \[VERIFY\]); audit trail for all data modifications |

**\---**

**\#\# 6\. Data Requirements**

**\#\#\# AgriFarm Entity**

| Aspect | Specification |  
|---|---|  
| **\*\*Source\*\*** | Manual entry (farmer), Xunta de Galicia registry, cooperative membership records |  
| **\*\*Data\*\*** | id, name, location (GeoJSON Point, farm HQ), address, landArea (hectares), ownedBy (person/cooperative), contactPoint (email, phone) |  
| **\*\*Update Frequency\*\*** | Static; updated only if farm expands/contracts or ownership changes (infrequent) |  
| **\*\*Permissions\*\*** | Farm owner (READ/WRITE); cooperative manager (READ if member); extension agent (READ only); other farmers (NO ACCESS) |  
| **\*\*Storage\*\*** | PostgreSQL AgriFarm table \+ FIWARE Orion Context Broker (NGSI-LD entity) |

**\---**

**\#\#\# AgriParcel Entity**

| Aspect | Specification |  
|---|---|  
| **\*\*Source\*\*** | SIGPAC WFS (official EU cadastral data); supplemented by manual geo-drawing if parcel not in SIGPAC |  
| **\*\*Data\*\*** | id (cadastral ID), name, location (GeoJSON Polygon, field boundary), area (hectares), municipio (concello), belongsToFarm, plantedWith (crop reference), agriSoil (reference to AgriSoil), createdAt |  
| **\*\*Update Frequency\*\*** | Static (boundary rarely changes); crop assignment (plantedWith) updated at planting and harvest |  
| **\*\*Permissions\*\*** | Farm owner (READ/WRITE); cooperative manager (READ/WRITE if member parcel); extension agent (READ only); public (READ anonymized data only) |  
| **\*\*Storage\*\*** | PostGIS parcel\_geom table; FIWARE Orion AgriParcel entity |

**\---**

**\#\#\# AgriCrop Entity**

| Aspect | Specification |  
|---|---|  
| **\*\*Source\*\*** | Predefined catalog (millo, pataca, kiwi, Albariño, Mencía, grelos, repolo, trigo, centeo, etc.); regional extension office curated varieties |  
| **\*\*Data\*\*** | id, name, scientificName, variety, agriSoilNeed (pH range, texture, drainage), waterNeed (mm/season), nutrientNeed (N-P-K kg/ha), plantingPeriod (start/end date), modelledYield (t/ha), harvestPeriod |  
| **\*\*Update Frequency\*\*** | Static; updated annually if new varieties introduced or regional models refined |  
| **\*\*Permissions\*\*** | Public READ; admin WRITE (only Xunta/extension office); farmers cannot modify but can suggest improvements |  
| **\*\*Storage\*\*** | PostgreSQL crop\_catalog table; FIWARE Orion AgriCrop entity |

**\---**

**\#\#\# AgriSoil Entity**

| Aspect | Specification |  
|---|---|  
| **\*\*Source\*\*** | CSIC Soil Map (1:1M raster, aggregated by parcel); manual soil test uploads (farmer labs); regional soil survey archives |  
| **\*\*Data\*\*** | id, parcelId, pH, EC (electrical conductivity), texture (clay %, sand %, silt %), organicMatter (%), nitrogen (kg/ha), phosphorus (kg/ha), potassium (kg/ha), drainageClass, sampledAt (date of most recent test) |  
| **\*\*Update Frequency\*\*** | CSIC data static (baseline); manual tests updated as farmers conduct tests (typically 1–2 per parcel per season) |  
| **\*\*Permissions\*\*** | Farm owner (READ/WRITE for manual tests); cooperative manager (READ pooled data); extension agent (READ); public (NO ACCESS — sensitive farm data) |  
| **\*\*Storage\*\*** | PostgreSQL soil table; linked to AgriParcel; versioned (keep history of soil test changes) |

**\---**

**\#\#\# AgriParcelRecord Entity**

| Aspect | Specification |  
|---|---|  
| **\*\*Source\*\*** | IoT sensors (soil moisture, temperature probes \[if deployed in pilot\]), satellite-derived indices (NDVI from Copernicus), weather station data (AEMET), manual farmer observations |  
| **\*\*Data\*\*** | id, parcelId, recordedAt (timestamp), soilMoisture (%), soilTemperature (°C), soilEC (mS/cm), airTemperature (°C), airRelativeHumidity (%), leafWetness (%), rainfall (mm), source (sensor ID, satellite, station), quality (good/fair/poor) |  
| **\*\*Update Frequency\*\*** | IoT sensors: daily (if deployed); satellite: every 5–6 days (Sentinel-2 revisit); weather station: daily; manual: ad hoc |  
| **\*\*Permissions\*\*** | Farmer (READ own data, WRITE manual observations); cooperative manager (READ pooled data); extension agent (READ); public (NO ACCESS) |  
| **\*\*Storage\*\*** | TimescaleDB or CrateDB (time-series optimized); FIWARE QuantumLeap historian; PostgreSQL replicated daily summary |

**\---**

**\#\#\# WeatherObserved Entity**

| Aspect | Specification |  
|---|---|  
| **\*\*Source\*\*** | AEMET/MeteoGalicia weather stations (official government network), OpenWeatherMap (backup), Copernicus climate reanalysis (ERA5) |  
| **\*\*Data\*\*** | id, location (GeoJSON Point, station location), dateObserved (timestamp), temperature (°C), relativeHumidity (%), precipitation (mm), windSpeed (m/s), windDirection (deg), atmosphericPressure (hPa), soilTemperature (°C), visibility (m), source (AEMET, OpenWeatherMap, satellite) |  
| **\*\*Update Frequency\*\*** | Every 3–6 hours from AEMET; daily aggregates computed for analysis |  
| **\*\*Permissions\*\*** | Public READ (weather data is open); farmers can see data for their region; no WRITE access (data-read only from official sources) |  
| **\*\*Storage\*\*** | TimescaleDB; FIWARE QuantumLeap; PostgreSQL daily summary |

**\---**

**\#\#\# WeatherForecast Entity**

| Aspect | Specification |  
|---|---|  
| **\*\*Source\*\*** | MeteoGalicia (regional forecast), AEMET (national), WMO GFS model (global fallback) |  
| **\*\*Data\*\*** | id, location, dateIssued (when forecast generated), validFrom/validTo (forecast period), temperatureMin/Max (°C), precipitationProbability (%), windSpeed (m/s), uvIndex, feelsLike (°C), source (MeteoGalicia, AEMET, GFS) |  
| **\*\*Update Frequency\*\*** | Twice daily (6 AM, 3 PM MeteoGalicia); rolling 7-day forecast |  
| **\*\*Permissions\*\*** | Public READ; farmers view forecasts for their regions; no WRITE |  
| **\*\*Storage\*\*** | PostgreSQL weather\_forecast table; TimescaleDB for historical forecast accuracy tracking; FIWARE Orion entity |

**\---**

**\#\#\# AgriParcelOperation Entity (Optional for MVP, but important for audit)**

| Aspect | Specification |  
|---|---|  
| **\*\*Source\*\*** | Farmer manual entry (via web form or mobile); cooperative bulk operations; future IoT equipment telemetry |  
| **\*\*Data\*\*** | id, parcelId, operationType (Sowing, Fertilizing, Spraying, Harvesting), startDate, endDate, product (fertilizer name, pesticide, seed variety), quantity, unit (kg, liters, seeds/ha), cost (EUR), result (success/partial/failure) |  
| **\*\*Update Frequency\*\*** | Ad hoc (farmer logs operation after completing it) |  
| **\*\*Permissions\*\*** | Farmer WRITE/READ own operations; cooperative manager READ pooled operations; extension agent READ all (anonymized for benchmarking); public NO ACCESS |  
| **\*\*Storage\*\*** | PostgreSQL operations table with audit trigger; FIWARE Orion AgriParcelOperation entity; versioned (keep deletion/modification history) |

**\---**

**\#\# 7\. MVP Scope**

**\#\#\# IN SCOPE (MVP Priority 1–2, deliverable in 12 weeks with 2–3 developers)**

**\*\*Frontend\*\***:  
\- Leaflet map with SIGPAC parcel boundaries and Copernicus Sentinel-2 satellite imagery  
\- Parcel selection and detail panel (metadata, crop history, parcel status)  
\- Parcel status management with color-coded status overlay and status filtering  
\- Crop suitability matrix (color-coded 0–100% for 8 core crops: millo, pataca, kiwi, Albariño, Mencía, grelos, repolo, trigo)  
\- AI-generated crop suitability explanations (basic LLM integration)  
\- AgroCopilot basic chat interface with parcel-specific context  
\- Planting date recommendations with frost calendar reasoning  
\- What-if simulator for sowing date, crop type, and irrigation assumption  
\- 7-day weather forecast (MeteoGalicia API integration)  
\- Simple historical charts (past 2 years rainfall, temperature)  
\- Mobile-responsive design (iOS/Android browsers)  
\- Language: Galician (primary), Spanish (secondary)

**\*\*Backend\*\***:  
\- FastAPI REST API for map, parcel, crop, weather, status, and fertilizer data  
\- PostgreSQL \+ PostGIS for spatial parcel data and static reference data  
\- TimescaleDB for time-series weather/sensor observations  
\- FIWARE Orion CB integration (basic): ingest parcel, crop, weather, status, and fertilizer inventory as NGSI-LD entities  
\- IoT Agent to fetch AEMET/MeteoGalicia data and feed to Orion  
\- QuantumLeap historian for time-series  
\- JWT authentication; basic RBAC (farmer, cooperative manager, extension agent)  
\- CSV export for operation logs

**\*\*Data Integration\*\***:  
\- SIGPAC WFS (parcel boundaries)  
\- AEMET/MeteoGalicia APIs (weather)  
\- CSIC Soil Map WMS (soil type overlay)  
\- Copernicus Sentinel Hub (satellite imagery, via public tiles initially)

**\*\*User Management\*\***:  
\- Registration (email, password, farmer/cooperative/extension agent role)  
\- Login and profile setup  
\- Link farmer to AgriFarm and AgriParcel entities

**\*\*AI/ML\*\***:  
\- Pre-trained crop suitability classifier (logistic regression or tree-based model; trained on historical regional data)  
\- Basic LLM prompting (OpenAI API or open-source LLaMA) for explanation generation and AgroCopilot chat responses  
\- No real-time sensor-based ML; static model retraining (quarterly)

**\*\*Fertilizer inventory basics in MVP\*\***:  
\- Basic stock tracking per farm  
\- Stock deduction on fertilizing operations  
\- Low-stock alerts for recommended products

**\*\*Out-of-scope from the MVP core\*\***:  
\- Offline capability (app shell, service worker)  
\- Pest phenology alerts (complex; defer to Phase 2\)  
\- SMS alerts (email/push notification only in MVP)  
\- Integration with farm equipment IoT (future)  
\- Soil moisture sensor ingestion (if no sensors deployed in pilot; use satellite-derived as fallback)  
\- Multi-language Catalan, Portuguese (future phases)  
\- Advanced analytics (machine learning yield prediction, market integration, etc.)

**\#\#\# OUT OF SCOPE / PHASE 2 (or partner responsibilities)**

\- Risk analysis layer (FR-RISK)  
\- Full cooperative multi-parcel dashboard with cross-farm analytics and benchmarking  
\- Smart contract / blockchain for EU subsidy verification (government integration)  
\- Drone/UAV data integration (partner responsibility)  
\- Equipment telem/automation (John Deere, AGCO API integration)  
\- Organic certification workflow (partner with certification bodies)  
\- Market price integration (partner with commodities exchanges)  
\- Advanced pest modeling (requires entomology expert; MVP uses simplified rules)  
\- Irrigation scheduling (requires soil moisture sensors; MVP shows forecast only)  
\- Precision nutrient recommendations (requires tissue sampling; MVP uses generic CSIC guidelines)

**\#\#\# PHASE 2 ADDITIONS**

\- Cooperative multi-parcel dashboard and comparative analytics across member farms  
\- Risk analysis layer overlays for environmental, water quality, extreme weather, and legal constraints  
\- Expanded alerting and benchmarking workflows for cooperative management

**\---**

**\#\# 8\. Success Metrics**

| KPI | Target (End of Year 1\) | Rationale |  
|---|---|---|  
| **\*\*User Adoption\*\*** | 500+ registered farmers in A Coruña; 50% monthly active users | Indicates farmer trust and utility; baseline for scaling to broader Galicia |  
| **\*\*Planting Decision Accuracy\*\*** | 70%+ of farmers report recommendations aligned with their planting choice; post-season survey | Core value proposition: farmers adopt recommendations |  
| **\*\*Data Quality Score\*\*** | 80%+ of parcels with soil test and operation history logged | Reflects data richness; enables better recommendations; supports EU audits |  
| **\*\*Cooperative Uptake\*\*** | 5+ agricultural cooperatives actively using portfolio dashboard | Validates cooperative value-add; enables bulk purchasing, collective risk management |  
| **\*\*Weather Alert Actionability\*\*** | 60%+ of frost/pest alerts trigger documented farmer response within 48h | Measures whether alerts drive real decisions; not vanity metrics |  
| **\*\*System Performance\*\*** | Map load \<2s on 4G; 99.5% uptime; \<1% data loss incidents | Technical stability; trust and reliability; SLA commitment |  
| **\*\*Cost Per Recommendation\*\*** | \<€0.10/farmer/month operational cost; zero subscription fee | Proves economic sustainability for smallholders (vs. €50–100/month commercial platforms) |  
| **\*\*Extension Agent Efficiency\*\*** | Miguel reduces average advisory visit time from 60 min to 20 min (per farmer, per season); handles 2x farmers with same resources | Demonstrates admin/extension value; ROI for Xunta investment |

**\---**

**\#\# Implementation Roadmap (12 Weeks, MVP Delivery)**

**\*\*Weeks 1–2: Infrastructure & Data Integration\*\***  
\- Set up PostgreSQL \+ PostGIS, TimescaleDB, FIWARE Orion CB, QuantumLeap  
\- Ingest SIGPAC parcel data (A Coruña region, \~50k parcels)  
\- Integrate AEMET/MeteoGalicia APIs; backfill 2 years historical weather

**\*\*Weeks 3–4: Frontend Core\*\***  
\- Leaflet map with SIGPAC boundaries \+ satellite imagery  
\- Parcel selection and detail panel  
\- Mobile-responsive design

**\*\*Weeks 5–6: Crop Suitability & Recommendations\*\***  
\- Integrate ML model (pre-trained); display color-coded suitability  
\- Basic LLM explanation generation  
\- Planting date recommendation engine

**\*\*Weeks 7–8: Backend API & Authentication\*\***  
\- FastAPI CRUD endpoints for parcels, crops, weather  
\- User authentication (JWT) and role-based access  
\- CSV export for operation logs

**\*\*Weeks 9–10: Weather, Alerts, Analytics\*\***  
\- 7-day forecast display  
\- Historical weather/performance charts  
\- Basic frost alert automation

**\*\*Weeks 11–12: Testing, Documentation, Pilot Launch\*\***  
\- User acceptance testing with 3–5 pilot farmers \+ 1 extension agent  
\- Create user guide (Galician) and technical documentation  
\- Deploy to production (cloud: AWS/Azure/Heroku \[VERIFY\])  
\- Launch pilot; gather feedback for Phase 2

**\---**

**\#\# Known Unknowns & Risks \[TBD/VERIFY\]**

1\. **\*\*SIGPAC Data Licensing\*\***: Confirm if SIGPAC WFS is freely accessible for commercial app use; if not, identify alternative cadastral source \[VERIFY\].  
2\. **\*\*Soil Moisture Sensor Deployment\*\***: MVP assumes no IoT sensors deployed; if Xunta or cooperatives provide real sensors, integration effort increases 20% \[VERIFY actual availability\].  
3\. **\*\*LLM Provider & Cost\*\***: Initial assumption is OpenAI API (€0.002/explanation); explore open-source alternatives (LLaMA, Mistral) if cost is concern \[VERIFY pricing/licensing\].  
4\. **\*\*FIWARE Hosting\*\***: Assume self-hosted FIWARE stack; confirm capacity and ops burden; consider FIWARE Lab or commercial FIWARE PaaS \[VERIFY infrastructure readiness\].  
5\. **\*\*Pilot Farmer Recruitment\*\***: Assume Xunta or cooperative provides 5–10 pilot testers; if recruitment is user responsibility, extend timeline 2 weeks \[VERIFY commitment\].  
6\. **\*\*Regulatory Compliance\*\***: Spanish LPDP and GDPR compliance assumed; engage legal review if processing sensitive farm data (subsidy records) \[VERIFY scope\].

**\---**

**\*\*Document Version History\*\***

| Version | Date | Author | Change |  
|---|---|---|---|  
| 1.0 | Apr 2026 | Product Team | Initial PRD; MVP scope defined |

**\*\*Approvals Required\*\***  
\- \[ \] Product Manager  
\- \[ \] Tech Lead (FIWARE/Backend)  
\- \[ \] Frontend Lead  
\- \[ \] Data Officer (Privacy)  
\- \[ \] Xunta de Galicia / Partner Stakeholders  
