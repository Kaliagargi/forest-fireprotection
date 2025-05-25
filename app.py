from flask import Flask, render_template, request, redirect, url_for
import pickle
import numpy as np
import requests
from threading import Thread
import time
import datetime
import pandas as pd

app = Flask(__name__)

# Load trained model
with open(r"C:\Users\gargi\Downloads\ees project\ees project\ees project\rf3.pkl", 'rb') as model_file:
    model = pickle.load(model_file)

# Predefined government credentials
GOV_ID = "admin123"
GOV_PASS = "pass123"

# Weather config
API_KEY = "c3e931cae7ada1468c3493ae80437555"  # Your OpenWeatherMap API key
CITY = "Lisbon"

# Global fire alert flag and status

fire_alert = False
latest_fire_prediction = {
    "status": "Fetching...",
    "fire_alert": False,
    "weather": None
}
prediction_history = []

# Function to fetch weather from OpenWeatherMap
def fetch_real_time_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY},PT&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    temp = data['main']['temp']
    humidity = data['main']['humidity']
    wind = data['wind']['speed']
    rain = data.get('rain', {}).get('1h', 0.0)  # default to 0.0 if no rain

    return [temp, humidity, wind, rain]

# Background monitoring thread

def real_time_fire_monitor():
    global latest_fire_prediction, fire_alert, prediction_history
    while True:
        try:
            temp, humidity, wind, rain = fetch_real_time_weather()
            df_features = pd.DataFrame([[temp, humidity, wind, rain]], columns=['temperature', 'humidity', 'wind', 'rain'])
            prediction = model.predict(df_features)[0]
            fire_alert = (prediction == 1)

            weather_info = {
                "temperature": temp,
                "humidity": humidity,
                "wind": wind,
                "rain": rain
            }

            latest_fire_prediction = {
                "status": "🔥 Forest Fire Risk Detected!" if prediction == 1 else "✅ No Forest Fire Risk",
                "fire_alert": fire_alert,
                "weather": weather_info
            }

            prediction_history.append({
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "prediction": latest_fire_prediction["status"],
                "weather": weather_info
            })

        except Exception as e:
            latest_fire_prediction = {
                "status": f"Error: {str(e)}",
                "fire_alert": False,
                "weather": None
            }

        time.sleep(60)


# Routes
@app.route("/")
def home():
    return render_template("signup.html")

@app.route("/user_signup", methods=["POST"])
def user_signup():
    return redirect(url_for("predict_page"))

@app.route("/gov_login", methods=["POST"])
def gov_login():
    gov_id = request.form.get("gov_id")
    password = request.form.get("password")

    if gov_id == GOV_ID and password == GOV_PASS:
        return render_template("gov_dashboard.html",
                               fire_alert=fire_alert,
                               prediction_status=latest_fire_prediction["status"],
                               weather=latest_fire_prediction["weather"],
                               history=prediction_history)
    else:
        return "Invalid government credentials. <a href='/'>Go back</a>", 401

@app.route("/predict", methods=["GET", "POST"])
def predict_page():
    global fire_alert
    if request.method == "POST":
        try:
            temp = float(request.form["temperature"])
            humidity = float(request.form["humidity"])
            wind = float(request.form["wind"])
            rain = float(request.form["rain"])

            df_features = pd.DataFrame([[temp, humidity, wind, rain]], columns=['temperature', 'humidity', 'wind', 'rain'])
            prediction = model.predict(df_features)[0]

            fire_alert = (prediction == 1)

            result = "🔥 Forest Fire Risk Detected!" if prediction == 1 else "✅ No Forest Fire Risk"
            return render_template("predict.html", result=result)
        except ValueError:
            return render_template("predict.html", result="Invalid input. Please enter valid numbers.")
    
    return render_template("predict.html", result=None)

# Start the monitoring thread + run Flask app
if __name__ == "__main__":
    monitor_thread = Thread(target=real_time_fire_monitor)
    monitor_thread.daemon = True
    monitor_thread.start()

    app.run(debug=True)
