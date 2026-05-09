from __future__ import annotations

from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get('/v2/entities/{entity_id}/attrs/{attr}')
async def attrs(entity_id: str, attr: str, lastN: int | None = None, fromDate: str | None = None, toDate: str | None = None):
    return {'attr': {'values': []}}


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8668, log_level='warning')
