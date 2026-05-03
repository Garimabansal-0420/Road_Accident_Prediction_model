# Road Accident Prediction System

A full-stack Machine Learning project that predicts the probability and risk level of road accidents based on historical data and real-time weather conditions.

## Project Structure

```
Road_Accident_Prediction/
├── data/
│   └── accident_data.csv        # Synthetic historical accident dataset
├── models/
│   └── model.pkl                # Trained Random Forest pipeline (preprocessor + model)
├── artifacts/
│   ├── feature_importance.png   # Visualization of feature importance
│   └── model_comparison.png     # F1-Scores of evaluated models
├── src/
│   ├── train_model.py           # ML script to generate data, train models, and evaluate
│   └── app.py                   # FastAPI backend server
├── frontend/
│   ├── index.html               # Main UI
│   ├── style.css                # Premium styling and animations
│   └── script.js                # Logic for logic handling, API fetches, geolocation
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

## Features
- **Machine Learning**: Compares Logistic Regression, Decision Tree, and Random Forest. Features advanced data pipelines (StandardScaler, OneHotEncoder).
- **Dynamic Risk Classification**: Predicts Low, Medium, or High risk probabilities.
- **Real-time Weather Integration**: Fetches live temperature, rainfall, and visibility using the free Open-Meteo API.
- **FastAPI Backend**: Robust API serving model predictions with auto-validation (Pydantic models).
- **Premium Frontend UX**: Glassmorphism UI, smooth result transition animations, probability bar charts, and automatic user geolocation handling.

---

## Setup & Deployment Instructions

### 1. Local Development

**Prerequisites:** Python 3.8+

1. **Clone/Navigate to the Directory:**
   Open a terminal in the `Road_Accident_Prediction` folder.

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Train the Model (Optional, model is already provided):**
   ```bash
   python src/train_model.py
   ```
   This will regenerate the dataset, train models, output metrics to terminal, and save the pipeline to `models/model.pkl`.

4. **Start the Backend Server:**
   ```bash
   uvicorn src.app:app --reload
   ```
   The backend will run on `http://localhost:8000`. You can access the API documentation at `http://localhost:8000/docs`.

5. **Start the Frontend:**
   Since it's plain HTML/CSS/JS, you can simply open `frontend/index.html` in any modern web browser.
   *(Alternatively, run a static server: `python -m http.server 3000` in the `frontend` folder and visit `http://localhost:3000`)*

### 2. Cloud Deployment (Render/Heroku/AWS etc.)

To deploy this project to the cloud, follow these general steps:

**Backend Deployment (e.g., Render Web Service):**
1. Ensure your repository is on GitHub.
2. Link the repository to your PaaS provider.
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `uvicorn src.app:app --host 0.0.0.0 --port $PORT`
5. The cloud provider will automatically inject the `$PORT` environment variable and host your API.

**Frontend Deployment (e.g., Vercel, Netlify, Render Static Site):**
1. Create a new static site pointing to the `frontend/` directory of your repository.
2. Ensure you update the `BASE_URL` in `frontend/script.js` to point to the deployed cloud URL of your FastAPI backend instead of `http://localhost:8000`.
3. Deploy!

---

## Technical Details (Model Analysis)
- The best-performing model was **Random Forest** achieving an overall accuracy of **~84%** on our synthetic dataset.
- Real-world deployment would involve utilizing localized authoritative accident datasets and connecting live traffic APIs (like Google Maps API) for maximum predictive capability.
