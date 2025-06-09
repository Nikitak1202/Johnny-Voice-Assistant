# Collects city-related info (time + weather)
import aiohttp
from datetime import datetime
from zoneinfo import ZoneInfo

CITY_TZ = {
    "Seoul": "Asia/Seoul",
    "London": "Europe/London",
    "New York": "America/New_York",
    "Paris": "Europe/Paris",
    "Tokyo": "Asia/Tokyo"
}

class CityInfo:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"


    # async HTTP request for weather
    async def Get_Weather(self, city: str = "Seoul") -> str:
        params = {"q": city, "appid": self.api_key, "units": "metric"}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as resp:
                data = await resp.json()

        if data.get("cod") != 200:
            return f"Sorry, I couldn't find weather for {city}."

        main = data["main"]
        desc = data["weather"][0]["description"]
        temp = main["temp"]
        humidity = main["humidity"]
        return (f"Weather in {city.title()}: {temp:.1f} degrees, "
                f"humidity {humidity}%, {desc}.")


    # sync local-time helper
    def Get_Time(self, city: str = "Seoul") -> str:
        tz = CITY_TZ.get(city.title())
        if not tz:
            return f"Sorry, I don't know the timezone for {city}."
        now = datetime.now(ZoneInfo(tz))
        return f"Time in {city.title()} is {now.hour} hours, {now.minute} minutes."