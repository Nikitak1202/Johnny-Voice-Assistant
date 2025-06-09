# Handles speech I/O, intent parsing, sensor access and TTS
import asyncio, os, re, tempfile, subprocess, speech_recognition as sr, edge_tts
from datetime import datetime
from DataManager import DataManager

class CommandManager:
    # Microphone, recogniser and sensor initialisation
    def __init__(self):
        self.dm = DataManager()
        self.rec = sr.Recognizer()
        self.mic = sr.Microphone()

    # Non-blocking speech recognition using a background thread
    async def recognize_once(self):
        def _sync_rec():
            with self.mic as src:
                self.rec.adjust_for_ambient_noise(src)
                audio = self.rec.listen(src, timeout=5)
            return self.rec.recognize_google(audio, language="en-US")
        try:
            return await asyncio.to_thread(_sync_rec)
        except (sr.UnknownValueError, sr.WaitTimeoutError):
            return ""

    # Intent routing and answer generation
    async def process_command(self, text: str):
        intent = self._interpret(text)
        if intent == "sensor":
            await self.dm.measure_microclimate()
            if self.dm.temp is None:
                return "Sorry, I couldn't read the sensor data."
            air = "good" if self.dm.gas else "bad"
            return (f"The average temperature is {self.dm.temp:.1f}�C and "
                    f"humidity is {self.dm.humidity:.1f}%. Air quality is {air}.")
        if intent == "time":
            now = datetime.now()
            return f"The current time is {now.strftime('%H:%M:%S')}."
        if intent == "calculate":
            expr = self._extract_expression(text)
            try:
                return f"The result of {expr} is {eval(expr)}."
            except Exception:
                return "Sorry, I couldn't understand the expression."
        return "I didn't understand your request."

    # TTS generation and playback
    async def speak(self, text: str):
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
            path = fp.name
        await edge_tts.Communicate(text, voice="en-US-JennyNeural").save(path)
        proc = await asyncio.create_subprocess_exec("mpg123", "-q", path)
        await proc.wait()
        os.remove(path)

    # --- helpers ---
    def _interpret(self, text: str):
        t = text.lower()
        if any(k in t for k in ("temperature", "humidity", "weather")):
            return "sensor"
        if "time" in t:
            return "time"
        if any(op in t for op in "+-*/") or "calculate" in t:
            return "calculate"
        return "unknown"

    def _extract_expression(self, text: str):
        tokens = re.findall(r"[\d.]+|[+\-*/]", text)
        return " ".join(tokens)
