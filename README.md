# TerraGalicia DSS

Sistema de apoyo a la decisión agrícola para explotaciones gallegas. Mapa interactivo con parcelas SIGPAC, scoring de aptitud de cultivos, previsión meteorológica, AgroCopilot y simulador what-if.

**Repositorio**: `[URL DEL REPO GITHUB]`

---

## Requisitos previos

Solo necesitas **Docker** (versión 24+) con Docker Compose incluido. No hace falta instalar Python, Node ni ninguna otra dependencia en el host.

---

## Arranque

### 1. Clonar el repositorio

```bash
git clone [URL DEL REPO GITHUB]
cd practica_2
```

### 2. Configurar variables de entorno

```bash
cp infra/.env.example infra/.env
```

Para un entorno local de desarrollo los valores por defecto del `.env.example` funcionan sin cambios. Solo es necesario editar si quieres habilitar funcionalidades opcionales:

| Variable | Para qué sirve |
|---|---|
| `LLM_API_KEY` / `LLM_API_BASE` | AgroCopilot con LLM real (sin esto usa respuestas de fallback) |
| `AEMET_API_KEY` | Fuente meteorológica alternativa a Open-Meteo |

### 3. Obtener los datos SIGPAC

Los ficheros `.gpkg` de los ~3,87 M recintos de A Coruña no están en el repositorio por su tamaño (~2 GB). Hay dos opciones:

**Opción A — Drive público del proyecto (recomendado)**

Descargar todos los ficheros desde:
> https://drive.google.com/drive/folders/1xlpSNj61GI-Oe2BClK3AkMArwVim31VZ?usp=sharing

Guardarlos en la carpeta `Recintos_Corunha/` en la raíz del proyecto:

```
practica_2/
  Recintos_Corunha/
    municipio_001.gpkg
    municipio_002.gpkg
    ...
```

**Opción B — Descarga manual vía QGIS**

Seguir el tutorial: https://mappinggis.com/2020/03/como-descargar-capas-del-sigpac-en-qgis/

Conectar el WFS del SIGPAC en QGIS, filtrar por provincia 15 (A Coruña), exportar cada municipio como `.gpkg` y guardarlo en `Recintos_Corunha/`.

> **Sin datos SIGPAC**: la aplicación arranca y funciona, pero el visor de parcelas solo mostrará 5 parcelas de demostración (datos mock). El resto de funcionalidades (tiempo, copiloto, simulador) funcionan igual.

### 4. Arrancar los servicios

```bash
docker compose -f infra/docker-compose.yml up --build -d
```

El primer arranque tarda unos minutos mientras se construyen las imágenes. Una vez levantado, abrir **http://localhost** en el navegador.

### 5. Cargar los datos SIGPAC en PostGIS

Solo necesario si tienes los ficheros `.gpkg` del paso 3. Requiere `ogr2ogr` y `sqlite3` instalados en el host (`sudo apt install gdal-bin sqlite3` en Ubuntu/Debian):

```bash
PGHOST=localhost \
PGPORT=5433 \
PGUSER=terragalicia \
PGPASSWORD=terragalicia \
PGDATABASE=terragalicia \
bash scripts/load_recintos_corunha_to_postgis.sh
```

La carga de los ~3,87 M recintos tarda entre 15 y 40 minutos dependiendo del hardware.

### 6. Cargar los datos semilla (Orion)

```bash
bash scripts/load_seed_data.sh
```

Este script crea las entidades NGSI-LD de demostración en Orion (granjas, parcelas, operaciones) y configura la suscripción de Orion hacia QuantumLeap.

---

## Acceso

| URL | Servicio |
|---|---|
| http://localhost | Aplicación web (frontend + backend) |
| http://localhost/api/docs | Documentación interactiva de la API (Swagger UI) |
| http://localhost:3001 | Grafana (sin dashboards configurados) |
| http://localhost:1026/ngsi-ld/v1/entities | Orion Context Broker directo |

El login es automático al cargar la app con el usuario demo **`farmer1`** / **`farmer123`**.

---

## Modo de desarrollo (sin Docker)

Si prefieres ejecutar el backend y el frontend directamente en el host para desarrollo:

**Backend**:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

En este modo necesitas tener PostgreSQL y Redis corriendo (puedes levantar solo esos contenedores con `docker compose -f infra/docker-compose.yml up postgres redis orion mongo -d`).

---

## Estructura del proyecto

```
practica_2/
├── backend/          FastAPI — lógica de negocio, API REST, scoring
├── frontend/         React 18 + Vite + Leaflet — SPA
├── infra/            Docker Compose, Nginx, configuración de servicios
├── scripts/          Carga de datos (SIGPAC, seed)
├── data/seed/        Entidades NGSI-LD de demostración
├── docs/             Documentación técnica
│   ├── architecture.md   Stack completo y diagrama de servicios
│   ├── data_model.md     Esquema recintos_sigpac y reglas de scoring
│   ├── PRD.md            Requisitos del producto
│   └── APPLICATION.md    Guía de la aplicación
└── FUTURE_IMPLEMENTATIONS.md
```

---

## Licencia

AGPL-3.0
