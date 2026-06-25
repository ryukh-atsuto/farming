# app/services/weather_service.py
import logging
import requests
from typing import List, Dict, Any
from app.config.settings import Config
from app.models.weather import Weather

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self):
        pass


    def get_weather_by_district(self, district: str) -> Weather:
        """
        Fetches current weather and forecast for given district name.
        """
        from app.services.location_service import LocationService
        loc_service = LocationService()
        coords = loc_service.get_coords_for_district(district)
        return self.get_weather_by_coords(coords["lat"], coords["lon"])

    def get_weather_by_coords(self, lat: float, lon: float) -> Weather:
        """
        Fetches current weather and forecast for given coordinates.
        Attempts Open-Meteo first (free/no key), then falls back to simulated data.
        """
        try:
            logger.info(f"Fetching weather via Open-Meteo for ({lat}, {lon})")
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}&"
                f"current=temperature_2m,relative_humidity_2m,rain,wind_speed_10m,weather_code&"
                f"daily=weather_code,temperature_2m_max,temperature_2m_min,rain_sum&"
                f"timezone=auto"
            )
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                current = data.get("current", {})
                daily = data.get("daily", {})
                
                temp = current.get("temperature_2m", 28.0)
                humidity = current.get("relative_humidity_2m", 80)
                rainfall = current.get("rain", 0.0)
                wind_speed = current.get("wind_speed_10m", 0.0)
                wmo_code = current.get("weather_code", 0)
                description = self._interpret_wmo_code(wmo_code)
                
                # Parse daily forecast
                forecast = []
                times = daily.get("time", [])
                max_temps = daily.get("temperature_2m_max", [])
                min_temps = daily.get("temperature_2m_min", [])
                rain_sums = daily.get("rain_sum", [])
                
                for i in range(min(3, len(times))):
                    forecast.append(
                        f"Day {i+1} ({times[i]}): {min_temps[i]}C to {max_temps[i]}C, Rain: {rain_sums[i]}mm"
                    )
                
                logger.info("Successfully fetched weather from Open-Meteo.")
                return Weather(
                    temp=temp,
                    humidity=humidity,
                    rainfall=rainfall,
                    wind_speed=wind_speed,
                    description=description,
                    forecast=forecast,
                    raw_data=data
                )
        except Exception as e:
            logger.error(f"Open-Meteo fetch failed: {e}. Falling back to simulation.")

        # Fallback to Localized Simulation
        logger.info("Utilizing simulated offline weather dataset.")
        return self._generate_simulated_weather(lat, lon)


    def _interpret_wmo_code(self, code: int) -> str:
        """Translates WMO weather codes to user-friendly descriptions."""
        wmo_map = {
            0: "Clear sky",
            1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
            80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
        }
        return wmo_map.get(code, "Partly Cloudy")

    def _generate_simulated_weather(self, lat: float, lon: float) -> Weather:
        """Generates mock weather suited for Bangladesh districts."""
        # Simple coordinate bounding to assign districts
        # Dhaka: (23.8103, 90.4125)
        # Rajshahi: (24.3745, 88.6042)
        # Sylhet: (24.8949, 91.8687)
        
        district = "Mymensingh"
        temp = 29.5
        humidity = 82
        rainfall = 1.5
        wind_speed = 3.2
        desc = "Partly Cloudy with light showers"
        forecast = [
            "Day 1: 30.0C - Light rain",
            "Day 2: 29.2C - Moderate showers",
            "Day 3: 31.5C - Clear and warm"
        ]

        if lon < 89.5:
            district = "Rajshahi"
            temp = 34.2
            humidity = 60
            rainfall = 0.0
            desc = "Hot and dry"
            forecast = [
                "Day 1: 35.0C - Sunny",
                "Day 2: 36.1C - Heat wave",
                "Day 3: 33.5C - Partly cloudy"
            ]
        elif lon > 91.2:
            district = "Sylhet"
            temp = 26.8
            humidity = 92
            rainfall = 7.8
            desc = "Heavy rain showers"
            forecast = [
                "Day 1: 26.0C - Downpour",
                "Day 2: 27.2C - Thunderstorms",
                "Day 3: 28.0C - Rain showers"
            ]

        logger.info(f"Simulated weather generated for {district} ({lat}, {lon})")
        return Weather(
            temp=temp,
            humidity=humidity,
            rainfall=rainfall,
            wind_speed=wind_speed,
            description=f"{desc} (Simulated for {district})",
            forecast=forecast,
            raw_data={"simulated": True, "district": district}
        )
