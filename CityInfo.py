# Collects city-related info (time + weather) � weather NO cache
import aiohttp, requests
from datetime import datetime, timedelta, timezone

COUNTRY_CODES = {
    "russia": "RU", "russian federation": "RU", "rus": "RU",
    "united states": "US", "usa": "US", "us": "US",
    "united kingdom": "GB", "uk": "GB",
    "south korea": "KR", "korea": "KR", "republic of korea": "KR",
    "japan": "JP", "france": "FR", "germany": "DE",
    "italy": "IT", "spain": "ES", "canada": "CA",
    "australia": "AU", "china": "CN", "india": "IN",
}


class CityInfo:
    def __init__(self, api_key: str):
        self.api_key   = api_key
        self.base_url  = "http://api.openweathermap.org/data/2.5/weather"
        self.time_cache = {}          # only for timezone reuse
        print("[DEBUG] CityInfo ready")

    # ---------------- weather (always HTTP) ----------------
    async def Get_Weather_Info(self, location: str = "Seoul") -> dict:
        city, cc, country_raw = self.split_location(location)

        params = self.params(city, cc)
        async with aiohttp.ClientSession() as sess:
            async with sess.get(self.base_url, params=params) as r:
                data = await r.json()

        pretty = f"{city.title()}{', '+country_raw if country_raw else ''}"

        if data.get("cod") != 200:
            return {
                "speech": f"Sorry, I couldn't find weather for {location}.",
                "ok": False,
                "city": pretty,
                "temp": None,
                "humidity": None,
                "condition": "unknown",
                "description": "",
            }

        weather_entry = data["weather"][0]
        main = data["main"]
        desc = weather_entry.get("description", "")
        temp = main.get("temp")
        hum = main.get("humidity")
        condition = weather_entry.get("main", "unknown")

        speech = f"Weather in {pretty}: {temp:.1f} degrees, humidity {hum}%, {desc}."
        return {
            "speech": speech,
            "ok": True,
            "city": pretty,
            "temp": temp,
            "humidity": hum,
            "condition": condition,
            "description": desc,
        }

    async def Get_Weather(self, location: str = "Seoul") -> str:
        info = await self.Get_Weather_Info(location)
        return info["speech"]

    # ---------------- time (uses cache) --------------------
    def Get_Time_Info(self, location: str = "Seoul") -> dict:
        city, cc, country_raw = self.split_location(location)
        key      = self.cache_key(city, cc)
        data     = self.time_cache.get(key)

        if data is None:                              # fetch once
            try:
                data = requests.get(
                    self.base_url, params=self.params(city, cc), timeout=4
                ).json()
                if data.get("cod") != 200:
                    return {
                        "speech": f"Sorry, I don't know the timezone for {location}.",
                        "ok": False,
                        "city": location,
                        "hour": None,
                        "minute": None,
                    }
                self.time_cache[key] = data
                print("[DEBUG] CityInfo cached new city:", location)
            except requests.RequestException:
                return {
                    "speech": f"Sorry, I don't know the timezone for {location}.",
                    "ok": False,
                    "city": location,
                    "hour": None,
                    "minute": None,
                }

        offset = int(data.get("timezone", 0))
        local  = datetime.now(timezone.utc) + timedelta(seconds=offset)
        pretty = f"{city.title()}{', '+country_raw if country_raw else ''}"
        speech = f"Time in {pretty} is {local.hour} hours, {local.minute} minutes."
        return {
            "speech": speech,
            "ok": True,
            "city": pretty,
            "hour": local.hour,
            "minute": local.minute,
        }

    def Get_Time(self, location: str = "Seoul") -> str:
        info = self.Get_Time_Info(location)
        return info["speech"]

    # ---------- helper: build params ---------------
    def params(self, city: str, cc: str | None):
        q = f"{city},{cc}" if cc else city
        return {"q": q, "appid": self.api_key, "units": "metric"}

    # ---------- helper: cache key ------------------
    @staticmethod
    def cache_key(city: str, cc: str | None):
        return f"{city.lower()}|{(cc or '').lower()}"

    # ---------- helper: split "city[, country]" ----
    def split_location(self, location: str):
        parts = [p.strip() for p in location.split(",")]
        if len(parts) == 2:                # "City, Country"
            city, country_raw = parts
        else:                              # maybe "City Country"
            tokens = location.strip().rsplit(" ", 1)
            if len(tokens) == 2 and tokens[1].lower() in COUNTRY_CODES:
                city, country_raw = tokens
            else:
                return location.strip(), None, None

        cc = COUNTRY_CODES.get(
            country_raw.lower(),
            country_raw.upper() if len(country_raw) == 2 else None
        )
        return city, cc, country_raw.title()
