from fastapi import FastAPI

app = FastAPI(title="TerraGalicia ML Placeholder")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ml-placeholder"}


@app.post("/predict")
def predict() -> dict[str, str]:
    return {"message": "ML placeholder endpoint"}
