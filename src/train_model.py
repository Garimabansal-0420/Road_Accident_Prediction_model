import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

def main():
    # Load data
    data_path = "updated_dataset.csv"
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"Error: Could not find {data_path}")
        return

    # Clean column names
    df.columns = df.columns.str.strip()

    print("Data loaded. Total rows:", len(df))

    # We map 'total__2021' into 3 categories: 0 (Low), 1 (Medium), 2 (High) risk
    quantiles = df['total__2021'].quantile([0.33, 0.66]).values
    
    def get_risk_level(total):
        if total <= quantiles[0]:
            return 0 # Low
        elif total <= quantiles[1]:
            return 1 # Medium
        else:
            return 2 # High
            
    df['risk_class_id'] = df['total__2021'].apply(get_risk_level)
    
    # Selected features
    features = ['total__2020', '2020_fatal', 'latitude', 'longitude']
    
    X = df[features]
    y = df['risk_class_id']
    
    # Handle possible NaNs
    X = X.fillna(X.mean())

    # We use a simple train test split
    # Note: with 43 rows, we use a small test size and won't be able to stratify perfectly in all cases
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    
    # Train the model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    
    # Save model
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/model.pkl')
    print("Model saved to models/model.pkl")
    
    # ---------------------------------------------
    # Train Environmental / Weather Model
    # ---------------------------------------------
    weather_data_path = "data/accident_data.csv"
    try:
        w_df = pd.read_csv(weather_data_path)
        print("Weather Data loaded. Total rows:", len(w_df))
        
        # Features: hour_of_day, traffic_volume, temperature, rainfall, visibility
        w_features = ['hour_of_day', 'traffic_volume', 'temperature', 'rainfall', 'visibility']
        w_X = w_df[w_features]
        w_y = w_df['accident_severity'] # Target is already 0, 1, 2
        
        w_X = w_X.fillna(w_X.mean())
        
        w_X_train, w_X_test, w_y_train, w_y_test = train_test_split(w_X, w_y, test_size=0.2, random_state=42)
        
        w_model = RandomForestClassifier(n_estimators=100, random_state=42)
        w_model.fit(w_X_train, w_y_train)
        
        w_y_pred = w_model.predict(w_X_test)
        print("Weather Model Accuracy:", accuracy_score(w_y_test, w_y_pred))
        
        joblib.dump(w_model, 'models/weather_model.pkl')
        print("Weather Model saved to models/weather_model.pkl")
        
    except FileNotFoundError:
        print(f"Error: Could not find {weather_data_path}")

if __name__ == '__main__':
    main()
