from flask import Flask, render_template
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

@app.route("/")
def index():
    # -------------------------------
    # Load cached data
    # -------------------------------
    forecast = pd.read_csv("cached_forecast.csv")
    forecast["date"] = pd.to_datetime(forecast["date"])

    values = pd.read_csv("cached_values.csv")
    values["date"] = pd.to_datetime(values["date"])

    # -------------------------------
    # Model
    # -------------------------------
    def simulate(params, air, time):
        k_w, k_f, k_s = params
        N = len(air)
        Tin = np.zeros(N)
        Tin[0] = 3
        ground = 15

        for n in range(N - 1):
            dt = (time[n+1] - time[n]).total_seconds() / 3600
            Tin[n+1] = Tin[n] + dt * (
                k_w * (air[n] - Tin[n]) +
                k_f * (ground - Tin[n])
            )
        return Tin

    k_w, k_f, k_s = 0.00875756, 0.0007412, 0.00011976

    merged = pd.concat([values, forecast], ignore_index=True)
    Tin = simulate([k_w, k_f, k_s], merged["value"], merged["date"])

    # -------------------------------
    # Plot
    # -------------------------------
    plt.figure(figsize=(10, 4))
    plt.plot(values['date'], values['value'], label="Aussentemperatur", color="dimgrey")
    plt.plot(forecast['date'], forecast['value'], color="lightgrey")
    plt.plot(merged["date"], Tin, label="Bad (erwartet)", color="tab:blue")
    plt.axhline(0, color="gray", linestyle="-")
    plt.ylabel("Temperature (°C)")
    plt.legend()
    plt.xlim(left = merged['date'].min(), right = merged['date'].max())
    plt.xticks(rotation=30)
    plt.tight_layout()

    plt.savefig("static/plot.png", dpi=150)
    plt.close()

    return render_template("index.html")