from flask import Flask, render_template
import os
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import your existing update_data function(s)
# Make sure update_data.py defines a function like: def update_data()
from update_data import update_data  

app = Flask(__name__)

# -------------------------------
# Config
# -------------------------------
CACHE_DURATION = timedelta(hours=6)
FORECAST_FILE = "cached_forecast.csv"
VALUES_FILE = "cached_values.csv"
SUN_FILE = "cached_sun.csv"

def needs_update(filename):
    if not os.path.exists(filename):
        return True
    last_mod = datetime.fromtimestamp(os.path.getmtime(filename))
    return datetime.now() - last_mod > CACHE_DURATION

# -------------------------------
# Route
# -------------------------------
@app.route("/")
def index():
    # Update data if needed
    if needs_update(FORECAST_FILE) or needs_update(VALUES_FILE):
        update_data()  # This downloads new CSVs

    # Load cached data
    forecast = pd.read_csv(FORECAST_FILE)
    forecast["date"] = pd.to_datetime(forecast["date"])
    values = pd.read_csv(VALUES_FILE)
    values["date"] = pd.to_datetime(values["date"])
    sun = pd.read_csv(SUN_FILE)
    sun["date"] = pd.to_datetime(sun["begin"]).dt.tz_localize(None)

    # -------------------------------
    # Simulation
    # -------------------------------
    def simulate(params, air, radiation, time):
        k_w, k_f, k_s = params
        N = len(air)
        Tin = np.zeros(N)
        Tin[0] = 3
        ground = 15
        
        if len(radiation) < N:
            extrapoled = np.ones(N) * np.mean(radiation[-24*3:])
            extrapoled[:len(radiation)] = radiation
            radiation = extrapoled

        for n in range(N - 1):
            dt = (time[n+1] - time[n]).total_seconds() / 3600
            Tin[n+1] = Tin[n] + dt * (
                k_w * (air[n] - Tin[n]) +
                k_f * (ground - Tin[n]) +
                k_s * radiation[n]
            )
        return Tin

    k_w, k_f, k_s = 0.00875756, 0.0007412, 0.00011976 
    merged = pd.concat([values, forecast], ignore_index=True)
    mask = (sun['date'] >= values['date'].iloc[0]) & (sun['date'] <= values['date'].iloc[-1])
    radiation = sun.loc[mask, 'v'].to_numpy()
    radiation = np.nan_to_num(radiation)
    Tin = simulate([k_w, k_f, k_s], merged["value"], radiation, merged["date"])

    # -------------------------------
    # Plot
    # -------------------------------
    plt.figure(figsize=(8, 4))
    plt.plot(values['date'], values['value'], label="Aussentemperatur", color="dimgrey")
    plt.plot(forecast['date'], forecast['value'], color="lightgrey")
    plt.plot(merged["date"], Tin, label="Bad (erwartet)", color="tab:blue")
    plt.axhline(0, color="gray", linestyle="-")
    plt.ylabel("Temperatur (°C)")
    plt.legend()
    plt.xlim(left=merged['date'].min(), right=merged['date'].max())
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.grid() 

    # Save plot
    if not os.path.exists("static"):
        os.makedirs("static")
    plt.savefig("static/plot.png", dpi=150)
    plt.close()

    return render_template("index.html")

# if __name__ == "__main__":
#     app.run(debug=True, port=5000, use_reloader=False)