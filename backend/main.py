from fastapi import FastAPI

app = FastAPI(title="TerraGalicia Backend Placeholder")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend-placeholder"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "TerraGalicia backend placeholder is running"}
