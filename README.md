# TerraGalicia DSS

Open-source agricultural decision-support system for smallholder farmers in Galicia, Spain.

![Build](https://img.shields.io/badge/build-pending-lightgrey)
![License](https://img.shields.io/badge/license-AGPL--3.0-blue)

## Overview
TerraGalicia DSS provides parcel-centric recommendations for crop suitability, operations, weather-aware decisions, and explainable AI support using FIWARE NGSI-LD Smart Data Models.

Full project documents are available in [docs/APPLICATION.md](docs/APPLICATION.md), [docs/PRD.md](docs/PRD.md), [docs/data_model.md](docs/data_model.md), and [docs/architecture.md](docs/architecture.md).

## Quick Start
1. Clone the repository.
2. Review the documentation in the `docs/` directory.
3. Configure environment variables for backend, frontend, FIWARE, and AI services.
4. Start services with Docker Compose (when compose files are added in `infra/`).

## Requirements
- Python 3.11+
- Node.js 20+
- Docker + Docker Compose
- FIWARE components (Orion-LD, IoT Agent JSON, QuantumLeap)
- PostgreSQL/PostGIS and TimescaleDB

## Running with Docker Compose
Infrastructure files will live under `infra/`.

Planned startup flow:
1. Build/pull service images.
2. Start FIWARE core and data services.
3. Start backend, frontend, ML, and LLM services.
4. Load seed data from `data/seed/`.

## Project Structure
- `docs/`: Functional and architecture documentation
- `data/seed/`: Synthetic seed datasets
- `backend/`: FastAPI service (to be created)
- `frontend/`: React app (to be created)
- `ml/`: ML service (to be created)
- `fiware/`: Orion/IoT Agent/QuantumLeap configuration
- `infra/`: Docker Compose and Nginx configuration
- `scripts/`: Data loading and utility scripts

## License
AGPL-3.0
