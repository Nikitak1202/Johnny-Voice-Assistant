import re

class NLP:
    # intent detection -----------------------------------------------------
    def Interpret_Command(self, text: str) -> str:
        t = text.lower()
        if "volume" in t or "louder" in t or "quieter" in t or "decrease" in t:
            return "volume"
        if "weather" in t:
            return "weather"
        if any(k in t for k in ("temperature", "humidity", "air")):
            return "sensor"
        if "time" in t:
            return "time"
        if any(op in t for op in "+-*/") or "calculate" in t:
            return "calculate"
        return "unknown"


    # volume parsing -------------------------------------------------------
    def Extract_Volume(self, text: str):
        t = text.lower()
        m = re.search(r"(\d{1,3})\s*%?", t)
        if m and "volume" in t:
            return ("set", int(m.group(1)))
        if any(w in t for w in ("up", "increase", "louder")):
            return ("up", 10)
        if any(w in t for w in ("down", "decrease", "quieter")):
            return ("down", 10)
        return None


    # city parsing ---------------------------------------------------------
    def Extract_City(self, text: str) -> str | None:
        m = re.search(r"(?:weather|time)\s+in\s+([a-zA-Z .]+)", text.lower())
        if not m:
            return None

        city = m.group(1).strip()

        # replace st / st. at word boundaries > saint
        city = re.sub(r"\bst\.?\b", "saint", city)

        return city.title()


    # math expression parsing ---------------------------------------------
    def Extract_Expression(self, text: str) -> str:
        return " ".join(re.findall(r"[\d.]+|[+\-*/]", text))