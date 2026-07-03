from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
from pathlib import Path
import os

app = FastAPI(title="Flight Price API")

# --- Chargement du modèle au démarrage ---
MODEL_PATH = Path("artifacts") / "flight_price_model.joblib"
model = None

@app.on_event("startup")
def load_model():
    global model
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Modèle introuvable à : {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    print("✅ Modèle chargé avec succès")

# --- Définition des données d'entrée (Validation) ---
class FlightRequest(BaseModel):
    airline: str
    source_city: str
    destination_city: str
    departure_time: str
    arrival_time: str
    duration: float
    days_left: int
    stops_label: str
    class_label: str

# Mappings (Les mêmes que dans ton streamlit)
STOPS_LABEL_TO_NUM = {"zero": 0, "one": 1, "two_or_more": 2}
CLASS_LABEL_TO_NUM = {"Economy": 0, "Business": 1}

@app.post("/predict")
def predict_price(req: FlightRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    
    # Transformation en DataFrame comme attendu par le modèle
    input_data = pd.DataFrame([{
        "airline": req.airline,
        "source_city": req.source_city,
        "destination_city": req.destination_city,
        "departure_time": req.departure_time,
        "arrival_time": req.arrival_time,
        "duration": req.duration,
        "days_left": req.days_left,
        "stops_num": STOPS_LABEL_TO_NUM.get(req.stops_label, 0),
        "class_num": CLASS_LABEL_TO_NUM.get(req.class_label, 0),
    }])

    try:
        prediction = model.predict(input_data)[0]
        # On renvoie un JSON
        return {"estimated_price": max(0, float(prediction))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    if model is not None:
        return {"status": "healthy"}

    raise HTTPException(status_code=503, detail="Model loading in progress")