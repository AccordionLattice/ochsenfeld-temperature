import requests
import pandas as pd
from io import StringIO
from wetterdienst import Settings
from wetterdienst.provider.dwd.observation import DwdObservationRequest

def update_data():
    # -------------------------------
    # Meteoblue forecast
    # -------------------------------
    METEOBLUE_URL = "https://my.meteoblue.com/packages/basic-1h?apikey=yV0eEcwKxnDWtavX&lat=48.8829&lon=11.2338&asl=408&format=csv&windspeed=ms-1"
    response = requests.get(METEOBLUE_URL)
    forecast = pd.read_csv(StringIO(response.text))
    forecast = forecast.rename(columns={"temperature": "value", "time": "date"})
    forecast["date"] = pd.to_datetime(forecast["date"])
    forecast.to_csv("cached_forecast.csv", index=False)

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
    values.to_csv("cached_values.csv", index=False)
