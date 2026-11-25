"""Live Weather & Forecast Module for The Daily Broadsheet.
Uses free Open-Meteo API (no key required) with automatic fallback.
"""

import requests
from typing import Dict

WMO_WEATHER_CODES = {
    0: ("Clear Skies", "☀️", "Golden sunshine over the province"),
    1: ("Mainly Clear", "🌤️", "Fair skies with gentle breeze"),
    2: ("Partly Cloudy", "⛅", "Intermittent sun and pleasant drifting cloud"),
    3: ("Overcast", "☁️", "Mantle of grey clouds across the horizon"),
    45: ("Foggy", "🌫️", "Dense fog shrouding the morning avenues"),
    48: ("Rime Fog", "🌫️", "Chilly mist clinging to stone and spire"),
    51: ("Light Drizzle", "🌦️", "Fine misting drizzle dampens the cobblestones"),
    53: ("Moderate Drizzle", "🌧️", "Steady drizzle pattering against the window panes"),
    55: ("Dense Drizzle", "🌧️", "Persistent drizzle hanging in the air"),
    61: ("Slight Rain", "🌦️", "Scattered showers passing across town"),
    63: ("Moderate Rain", "🌧️", "Steady rainfall washing the thoroughfares"),
    65: ("Heavy Rain", "🌧️", "Torrential rainfall driving through the district"),
    71: ("Slight Snow", "🌨️", "Gentle snowflakes drifting softly downward"),
    73: ("Moderate Snow", "❄️", "Brisk snowfall blanketing rooftops"),
    75: ("Heavy Snow", "❄️", "Heavy blizzard conditions across the province"),
    80: ("Brief Showers", "🌦️", "Passing rain showers with sudden clearing"),
    81: ("Moderate Showers", "🌧️", "Brisk rain squalls across the harbour"),
    82: ("Violent Showers", "⛈️", "Violent downpours accompanied by gusting winds"),
    95: ("Thunderstorm", "⚡", "Distant thunder rumbles across the hills"),
    96: ("Thunderstorm with Hail", "⛈️", "Electric storm with scattered hailstones"),
}

CITY_CACHE = {
    "bengaluru": (12.9719, 77.5937, "Bengaluru, India"),
    "bangalore": (12.9719, 77.5937, "Bengaluru, India"),
    "new delhi": (28.6139, 77.2090, "New Delhi, India"),
    "delhi": (28.6139, 77.2090, "New Delhi, India"),
    "mumbai": (19.0760, 72.8777, "Mumbai, India"),
    "chennai": (13.0827, 80.2707, "Chennai, India"),
    "kolkata": (22.5726, 88.3639, "Kolkata, India"),
    "hyderabad": (17.3850, 78.4867, "Hyderabad, India"),
    "london": (51.5074, -0.1278, "London, UK"),
    "new york": (40.7128, -74.0060, "New York, USA"),
    "san francisco": (37.7749, -122.4194, "San Francisco, USA"),
    "singapore": (1.3521, 103.8198, "Singapore"),
    "tokyo": (35.6762, 139.6503, "Tokyo, Japan"),
}


def geocode_city(city_name: str) -> tuple:
    """Finds lat, lon, and full name for a city."""
    normalized = city_name.strip().lower()
    # Check alias
    for k, v in CITY_CACHE.items():
        if k in normalized:
            return v

    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        resp = requests.get(url, params={"name": city_name, "count": 1, "format": "json"}, timeout=4)
        if resp.ok:
            data = resp.json()
            if data.get("results"):
                res = data["results"][0]
                return (
                    res["latitude"],
                    res["longitude"],
                    f"{res.get('name')}, {res.get('country', '')}",
                )
    except Exception:
        pass

    # Default to Bengaluru
    return (12.9719, 77.5937, "Bengaluru, India")


def get_live_weather(city_query: str = "Bengaluru") -> Dict:
    """Fetches real-time weather from Open-Meteo or provides graceful default."""
    lat, lon, resolved_name = geocode_city(city_query)

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "auto",
        }
        resp = requests.get(url, params=params, timeout=5)
        if resp.ok:
            data = resp.json()
            curr = data.get("current", {})
            daily = data.get("daily", {})

            temp_c = curr.get("temperature_2m", 25.0)
            temp_f = (temp_c * 9 / 5) + 32
            humidity = curr.get("relative_humidity_2m", 60)
            wind_kmh = curr.get("wind_speed_10m", 10.0)
            wcode = curr.get("weather_code", 0)

            high_c = daily.get("temperature_2m_max", [temp_c + 3])[0]
            low_c = daily.get("temperature_2m_min", [temp_c - 4])[0]

            cond_title, icon, poetic = WMO_WEATHER_CODES.get(
                wcode, ("Fair Weather", "☀️", "Pleasant conditions prevailing")
            )

            broadsheet_ear = f"{cond_title}, {temp_c:.0f}°C ({temp_f:.0f}°F) — {poetic}. High: {high_c:.0f}°C, Low: {low_c:.0f}°C."

            return {
                "city": resolved_name,
                "temp_c": round(temp_c, 1),
                "temp_f": round(temp_f, 1),
                "condition": cond_title,
                "icon": icon,
                "poetic": poetic,
                "humidity": f"{humidity}%",
                "wind": f"{wind_kmh:.0f} km/h",
                "high_c": round(high_c, 1),
                "low_c": round(low_c, 1),
                "broadsheet_ear": broadsheet_ear,
                "is_live": True,
            }
    except Exception as e:
        print(f"Weather lookup fallback: {e}")

    # Fallback realistic weather (e.g. for Bengaluru / India)
    return {
        "city": resolved_name,
        "temp_c": 26.5,
        "temp_f": 79.7,
        "condition": "Mainly Clear",
        "icon": "🌤️",
        "poetic": "Fair skies with gentle breeze across the avenues",
        "humidity": "58%",
        "wind": "11 km/h",
        "high_c": 29.0,
        "low_c": 19.5,
        "broadsheet_ear": "Mainly Clear, 27°C (80°F) — Fair skies with gentle breeze across the avenues. High: 29°C, Low: 20°C.",
        "is_live": False,
    }
