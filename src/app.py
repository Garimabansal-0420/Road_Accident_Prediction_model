from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import json
import requests
from datetime import datetime

app = FastAPI(title="District Road Accident Risk Profiler & Dashboard")

# CORS middleware for frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models at startup
MODEL_PATH = "models/model.pkl"
try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    print(f"Warning: Model could not be loaded at {MODEL_PATH}. Error: {e}")
    model = None

WEATHER_MODEL_PATH = "models/weather_model.pkl"
try:
    weather_model = joblib.load(WEATHER_MODEL_PATH)
except Exception as e:
    print(f"Warning: Weather Model could not be loaded at {WEATHER_MODEL_PATH}. Error: {e}")
    weather_model = None

# Load dataset to serve district info
DATA_PATH = "updated_dataset.csv"
try:
    df_data = pd.read_csv(DATA_PATH)
    # create a lookup dictionary for districts
    districts_info = []
    dashboard_summary = {
        "total_deaths_2020": float(df_data["2020_fatal"].sum()),
        "total_deaths_2021": float(df_data["2021_fatal"].sum()),
        "total_accidents_2020": float(df_data["total__2020"].sum()),
        "total_accidents_2021": float(df_data["total__2021"].sum())
    }
    dashboard_vehicle_stats = {
        "lorries": float(df_data["death_by_lorries__2021"].sum()),
        "buses": float(df_data["death_by_buses2021"].sum()),
        "cars_jeeps": float(df_data["death_by_carsjeeps_2021"].sum()),
        "three_wheelers": float(df_data["death_by_threewheelers__2021"].sum()),
        "two_wheelers": float(df_data["death_by_twowheelers_2021"].sum()),
        "others": float(df_data["death_by_others_2021"].sum())
    }
    dashboard_comparison = []
    for _, row in df_data.iterrows():
        # Clean col names if needed, but we can access by string index
        district_name = row["district"].strip() if isinstance(row["district"], str) else row["district"]
        districts_info.append({
            "district": district_name,
            "total_2020": float(row["total__2020"] if pd.notnull(row["total__2020"]) else 0),
            "fatal_2020": float(row["2020_fatal"] if pd.notnull(row["2020_fatal"]) else 0),
            "latitude": float(row["latitude"] if pd.notnull(row["latitude"]) else 0),
            "longitude": float(row["longitude"] if pd.notnull(row["longitude"]) else 0),
        })
        dashboard_comparison.append({
            "district": district_name,
            "accidents_2020": float(row["total__2020"] if pd.notnull(row["total__2020"]) else 0),
            "accidents_2021": float(row["total__2021"] if pd.notnull(row["total__2021"]) else 0)
        })
    # sort comparison desc by 2021 accidents and take top 10
    dashboard_comparison = sorted(dashboard_comparison, key=lambda x: x["accidents_2021"], reverse=True)[:10]

except Exception as e:
    print(f"Warning: Could not load dataset at {DATA_PATH}. Error: {e}")
    districts_info = []
    dashboard_summary = {}
    dashboard_vehicle_stats = {}
    dashboard_comparison = []

class PredictRequest(BaseModel):
    total_2020: float
    fatal_2020: float
    latitude: float
    longitude: float
    temperature: float
    rainfall: float
    visibility: float

class WeatherContext(BaseModel):
    temperature: float
    rainfall: float
    visibility: float
    hour_of_day: int
    traffic_volume: float

class PredictResponse(BaseModel):
    risk_level: str
    probabilities: dict
    risk_class_id: int
    weather_context: WeatherContext

@app.get("/districts")
def get_districts():
    """Returns the list of districts with their default features."""
    return {"districts": districts_info}

@app.get("/dashboard/summary")
def get_dashboard_summary():
    return dashboard_summary

@app.get("/dashboard/vehicle-stats")
def get_dashboard_vehicle_stats():
    return dashboard_vehicle_stats

@app.get("/dashboard/comparison")
def get_dashboard_comparison():
    return {"comparison": dashboard_comparison}

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    if model is None or weather_model is None:
        raise HTTPException(status_code=500, detail="Models are not fully loaded on the server.")
    
    # Needs to match features: ['total__2020', '2020_fatal', 'latitude', 'longitude']
    data = {
        'total__2020': [request.total_2020],
        '2020_fatal': [request.fatal_2020],
        'latitude': [request.latitude],
        'longitude': [request.longitude]
    }
    df = pd.DataFrame(data)
    
    # Fetch and compute live weather and traffic features
    hour_of_day = datetime.now().hour
    # Estimate live traffic volume based on time of day
    if 7 <= hour_of_day <= 10 or 16 <= hour_of_day <= 19:
        traffic_volume = 85.0  # Peak hours
    elif 22 <= hour_of_day or hour_of_day <= 5:
        traffic_volume = 20.0  # Night / Low traffic
    else:
        traffic_volume = 55.0  # Regular traffic
    
    temperature = request.temperature
    rainfall = request.rainfall
    visibility = request.visibility

    weather_data = {
        'hour_of_day': [hour_of_day],
        'traffic_volume': [traffic_volume],
        'temperature': [temperature],
        'rainfall': [rainfall],
        'visibility': [visibility]
    }
    w_df = pd.DataFrame(weather_data)
    
    try:
        # Predict class and probabilities for district
        probs = model.predict_proba(df)[0]
        
        # Predict class and probabilities for weather
        w_probs = weather_model.predict_proba(w_df)[0]
        
        combo_probs = []
        for i in range(3):
            p1 = float(probs[i]) if len(probs) > i else 0.0
            p2 = float(w_probs[i]) if len(w_probs) > i else 0.0
            combo_probs.append((p1 + p2) / 2.0)
            
        combined_class = combo_probs.index(max(combo_probs))
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")
    
    risk_mapping = {0: "Low", 1: "Medium", 2: "High"}
    
    weather_ctx = WeatherContext(
        temperature=temperature,
        rainfall=rainfall,
        visibility=visibility,
        hour_of_day=hour_of_day,
        traffic_volume=traffic_volume
    )
    
    return PredictResponse(
        risk_level=risk_mapping.get(combined_class, "Unknown"),
        risk_class_id=int(combined_class),
        probabilities={
            "Low": combo_probs[0],
            "Medium": combo_probs[1],
            "High": combo_probs[2]
        },
        weather_context=weather_ctx
    )
