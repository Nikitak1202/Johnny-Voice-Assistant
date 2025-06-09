import re

class NLP:
    # intent detection
    def Interpret_Command(self, text: str) -> str:
        t = text.lower()
        if "weather" in t:
            return "weather"
        if any(k in t for k in ("temperature", "humidity", 'air')):
            return "sensor"
        if "time" in t:
            return "time"
        if any(op in t for op in "+-*/") or "calculate" in t:
            return "calculate"
        return "unknown"


    # city extractor for both "time in" and "weather in"
    def Extract_City(self, text: str) -> str | None:
        m = re.search(r"(?:weather|time)\s+in\s+([a-zA-Z ]+)", text.lower())
        return m.group(1).title() if m else None


    # math expression extractor
    def Extract_Expression(self, text: str) -> str:
        return " ".join(re.findall(r"[\d.]+|[+\-*/]", text))