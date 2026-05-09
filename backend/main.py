from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.sigpac import router as sigpac_router
from api.routes.copilot import router as copilot_router
from api.routes.crops import router as crops_router
from api.routes.farms import router as farms_router
from api.routes.operations import router as operations_router
from api.routes.parcels import router as parcels_router
from api.routes.simulator import router as simulator_router
from api.routes.suitability import router as suitability_router
from api.routes.weather import router as weather_router
from config import get_settings
from db.redis_cache import RedisCache
from services.llm_client import LLMClient
from services.ml_client import MLClient
from services.orion import OrionClient
from services.quantumleap import QuantumLeapClient
from services.weather_fetcher import WeatherFetcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Initialize clients
    orion = OrionClient(settings)
    quantumleap = QuantumLeapClient(settings)
    ml_client = MLClient(settings)
    llm_client = LLMClient(settings)
    weather_fetcher = WeatherFetcher(settings)
    redis_cache = RedisCache(settings.redis_url)
    await redis_cache.connect()

    # Store in app state
    app.state.orion = orion
    app.state.quantumleap = quantumleap
    app.state.ml_client = ml_client
    app.state.llm_client = llm_client
    app.state.weather_fetcher = weather_fetcher
    app.state.redis_cache = redis_cache
    app.state.operation_store = []
    app.state.parcel_status_overrides = {}

    yield

    # Cleanup on shutdown
    await orion.close()
    await quantumleap.close()
    await ml_client.close()
    await llm_client.close()
    await weather_fetcher.close()
    await redis_cache.disconnect()


app = FastAPI(
    title="TerraGalicia DSS API",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sigpac_router, prefix="/api/v1", tags=["sigpac"])
app.include_router(copilot_router, prefix="/api/v1", tags=["copilot"])
app.include_router(crops_router, prefix="/api/v1", tags=["crops"])
app.include_router(farms_router, prefix="/api/v1", tags=["farms"])
app.include_router(operations_router, prefix="/api/v1", tags=["operations"])
app.include_router(parcels_router, prefix="/api/v1", tags=["parcels"])
app.include_router(simulator_router, prefix="/api/v1", tags=["simulator"])
app.include_router(suitability_router, prefix="/api/v1", tags=["suitability"])
app.include_router(weather_router, prefix="/api/v1", tags=["weather"])


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "TerraGalicia DSS Backend"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "TerraGalicia DSS API is running"}


# Compatibility endpoint for external health checks (nginx/container probes)
@app.get("/health")
def health_compat() -> dict[str, str]:
    return health()
