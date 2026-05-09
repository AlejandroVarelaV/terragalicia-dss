from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

ROOT = Path('/home/sarap/XDEI/P2_/terragalicia-dss')
PARCELS = json.loads((ROOT / 'data/seed/seed_parcels.json').read_text())
SOILS = json.loads((ROOT / 'data/seed/seed_soils.json').read_text())
ACORUNA_PARCEL_ID = 'urn:ngsi-ld:AgriParcel:acoruna:farm001:parcel01'
ACORUNA_SOIL_ID = 'urn:ngsi-ld:AgriSoil:acoruna:atlantic-acid:001'

app = FastAPI()


@app.get('/version')
async def version() -> dict[str, str]:
    return {'version': 'mock'}


@app.get('/ngsi-ld/v1/entities')
async def list_entities(type: str | None = None, limit: int | None = None):
    items = []
    if type == 'AgriParcel':
        items = PARCELS + [
            {
                **PARCELS[0],
                'id': ACORUNA_PARCEL_ID,
                'hasAgriSoil': {'type': 'Relationship', 'object': ACORUNA_SOIL_ID},
            }
        ]
    elif type == 'AgriSoil':
        items = SOILS + [
            {
                **SOILS[0],
                'id': ACORUNA_SOIL_ID,
            }
        ]
    return items[: limit or len(items)]


@app.get('/ngsi-ld/v1/entities/{entity_id}')
async def get_entity(entity_id: str, type: str | None = None):
    collection = PARCELS if type == 'AgriParcel' else SOILS if type == 'AgriSoil' else []
    if type == 'AgriParcel' and entity_id == ACORUNA_PARCEL_ID:
        return {
            **PARCELS[0],
            'id': ACORUNA_PARCEL_ID,
            'hasAgriSoil': {'type': 'Relationship', 'object': ACORUNA_SOIL_ID},
        }
    if type == 'AgriSoil' and entity_id == ACORUNA_SOIL_ID:
        return {
            **SOILS[0],
            'id': ACORUNA_SOIL_ID,
        }
    for item in collection:
        if item['id'] == entity_id:
            return item
    raise HTTPException(status_code=404, detail='not found')


@app.post('/ngsi-ld/v1/entities')
async def create_entity(request: Request):
    await request.body()
    return JSONResponse(status_code=201, content={})


@app.patch('/ngsi-ld/v1/entities/{entity_id}/attrs/{attr}')
async def patch_attr(entity_id: str, attr: str, request: Request):
    await request.body()
    return JSONResponse(status_code=204, content=None)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=1026, log_level='warning')
