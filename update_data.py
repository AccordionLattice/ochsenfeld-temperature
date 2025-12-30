import requests
import pandas as pd
from io import StringIO
from wetterdienst import Settings
from wetterdienst.provider.dwd.observation import DwdObservationRequest
from datetime import datetime, timedelta

def floor_to_hour(dt):
    return dt.replace(minute=0, second=0, microsecond=0)

def update_data():
    # -------------------------------
    # Meteoblue forecast
    # -------------------------------
    METEOBLUE_URL = "https://my.meteoblue.com/packages/basic-1h?apikey=yV0eEcwKxnDWtavX&lat=48.8829&lon=11.2338&asl=408&format=csv&windspeed=ms-1"
    response = requests.get(METEOBLUE_URL)
    
    response.raise_for_status()  # raises error if request failed

    if "temperature" not in response.text:
        raise ValueError("Meteoblue CSV not returned. Check API key and URL.")

    forecast = pd.read_csv(StringIO(response.text))


    forecast = pd.read_csv(StringIO(response.text))
    forecast = forecast.rename(columns={"temperature": "value", "time": "date"})
    forecast["date"] = pd.to_datetime(forecast["date"])
    forecast.to_csv("cached_forecast.csv", index=False)

    # -------------------------------
    # DWD data
    # -------------------------------
    today = datetime.today().strftime('%Y-%m-%d')
    startday = (datetime.today() - timedelta(days = 30)).strftime('%Y-%m-%d')
    settings = Settings(
        ts_shape="long",
        ts_humanize=True,
        ts_convert_units=True
    )
    request = DwdObservationRequest(
        parameters=[("hourly", "temperature_air", "temperature_air_mean_2m")],
        start_date=startday,
        end_date=today,
        settings=settings
    )
    station = request.filter_by_station_id(station_id=(1161,))
    values = station.values.all().df.to_pandas()
    if values.empty:
        raise ValueError("No DWD data returned for station 1161.")

    values["date"] = pd.to_datetime(values["date"]).dt.tz_localize(None)
    values.to_csv("cached_values.csv", index=False)
    
    # -------------------------------
    # Sensoto sun data
    # -------------------------------
    end = datetime.utcnow()
    start = end - timedelta(days=31)

    end = floor_to_hour(end)
    start = floor_to_hour(start)
    
    interval = f"R{365*24}/{start.strftime('%Y-%m-%dT%H:%M:%SZ')}/PT1H"
    url = "https://api.sensoto.io/v1/organizations/open/networks/gkd-bayern/devices/200010/sensors/meteo-globalstrahlung/measurements"

    params = {
        "interval": interval
    }

    r = requests.get(url, params=params)
    r.raise_for_status()
    sun = pd.DataFrame(r.json())
    sun.to_csv("cached_sun.csv", index=False)
