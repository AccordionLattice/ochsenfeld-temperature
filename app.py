from flask import Flask, render_template
import requests
import pandas as pd
from io import StringIO
import matplotlib.pyplot as plt
import numpy as np

from wetterdienst import Settings
from wetterdienst.provider.dwd.observation import DwdObservationRequest

app = Flask(__name__)

@app.route("/")
def index():

    # -------------------------------
    # Meteoblue forecast
    # -------------------------------
    url = "https://my.meteoblue.com/packages/basic-1h?apikey=yV0eEcwKxnDWtavX&lat=48.8829&lon=11.2338&asl=408&format=csv&windspeed=ms-1"
    response = requests.get(url)
    forecast = pd.read_csv(StringIO(response.text))

    forecast = forecast.rename(columns={
        "temperature": "value",
        "time": "date"
    })
    forecast["date"] = pd.to_datetime(forecast["date"])

    # -------------------------------
    # DWD data
    # -------------------------------
    settings = Settings(
        ts_shape="long",
        ts_humanize=True,
        ts_convert_units=True
    )

    request = DwdObservationRequest(
        parameters=[("hourly", "temperature_air", "temperature_air_mean_2m")],
        start_date="2025-12-01",
        end_date="2025-12-30",
        settings=settings
    )

    station = request.filter_by_station_id(station_id=(1161,))
    values = station.values.all().df.to_pandas()
    values["date"] = pd.to_datetime(values["date"]).dt.tz_localize(None)

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
    plt.plot(merged["date"], merged["value"], label="Air Temp")
    plt.plot(merged["date"], Tin, label="Simulated")
    plt.axhline(0, color="gray", linestyle="--")
    plt.ylabel("Temperature (°C)")
    plt.legend()
    plt.xticks(rotation=30)
    plt.tight_layout()

    plt.savefig("static/plot.png", dpi=150)
    plt.close()

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)