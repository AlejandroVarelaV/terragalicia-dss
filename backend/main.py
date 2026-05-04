from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.sigpac import router as sigpac_router

app = FastAPI(title="TerraGalicia Backend Placeholder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sigpac_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend-placeholder"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "TerraGalicia backend placeholder is running"}
