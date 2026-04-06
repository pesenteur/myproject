from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import PredictRequest, PredictResponse
from app.services.predictor import run_all_predictors

app = FastAPI(title="Protein Enzyme API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://8.130.190.195:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def root():
    return {"message": "Protein Enzyme API is running"}


@app.post("/api/predict", response_model=PredictResponse)
def predict(data: PredictRequest):
    sequence = data.sequence.strip()

    if not sequence:
        raise HTTPException(status_code=400, detail="Empty sequence")

    try:
        return run_all_predictors(sequence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))