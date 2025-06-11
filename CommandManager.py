import asyncio, os, tempfile, speech_recognition as sr, edge_tts
from DataManager import DataManager
from nlp import NLP
from CityInfo import CityInfo


class CommandManager:
    def __init__(self, wake_word: str = "start"):
        self.DataManager = DataManager()
        self.NLP = NLP()
        self.CityInfo = CityInfo("486c05914b1d1a5c9ea00ce1568a64d6")
        self.SpeechRecognizer = sr.Recognizer()
        self.Microphone = sr.Microphone()
        self.WakeWord = wake_word
        self.Volume = 80
        print("--------------------------------------------------------------")
        print("[DEBUG] CommandManager ready")


    async def Listen_Phrase(self) -> str:
        def sync_listen():
            with self.Microphone as src:
                self.SpeechRecognizer.adjust_for_ambient_noise(src)
                audio = self.SpeechRecognizer.listen(src, timeout=8)
            return self.SpeechRecognizer.recognize_google(audio, language="en-US")

        try:
            phrase = await asyncio.to_thread(sync_listen)
            print("--------------------------------------------------------------")
            print(f"[DEBUG] Heard: {phrase}")
            return phrase
        except (sr.UnknownValueError, sr.WaitTimeoutError):
            print("--------------------------------------------------------------")
            print("[DEBUG] Listen timeout / unintelligible")
            return ""
        except sr.RequestError as e:
            print("--------------------------------------------------------------")
            print(f"[DEBUG] Google STT error: {e}")
            return ""


    # ---------------- intent routing ---------------
    async def Handle_Phrase(self, phrase: str) -> str:
        lower = phrase.lower()
        if self.WakeWord not in lower:
            return ""

        command_text = phrase[lower.find(self.WakeWord) + len(self.WakeWord):].strip()
        if not command_text:
            print("--------------------------------------------------------------")
            print("[DEBUG] Wake word present but command empty")
            return ""

        print("--------------------------------------------------------------")
        print(f"[DEBUG] Command: {command_text}")
        intent = self.NLP.Interpret_Command(command_text)

        if intent == "sensor":
            await self.DataManager.Measure_MicroClimate()
            if self.DataManager.temp is None:
                return "Sorry, I couldn't read the sensor data."
            air = "good" if self.DataManager.gas else "bad"
            return (f"The average temperature is {self.DataManager.temp:.1f}°C and "
                    f"humidity is {self.DataManager.humidity:.1f}%. Air quality is {air}.")

        if intent == "time":
            city = self.NLP.Extract_City(command_text) or "Seoul"
            return self.CityInfo.Get_Time(city)

        if intent == "weather":
            city = self.NLP.Extract_City(command_text) or "Seoul"
            return await self.CityInfo.Get_Weather(city)

        if intent == "volume":
            action = self.NLP.Extract_Volume(command_text)
            if not action:
                return "Sorry, I didn't get the volume level."
            kind, value = action
            if kind == "set":
                self.Volume = max(0, min(100, value))
            elif kind == "up":
                self.Volume = min(100, self.Volume + value)
            elif kind == "down":
                self.Volume = max(0, self.Volume - value)

            await self.Set_System_Volume(self.Volume)
            return f"Volume set to {self.Volume} percent."

        if intent == "calculate":
            expr = self.NLP.Extract_Expression(command_text)
            try:
                return f"The result of {expr} is {eval(expr)}."
            except Exception:
                return "Sorry, I couldn't understand the expression."

        return "I didn't understand your request."


    # ---------------- TTS output -------------------
    async def Speak(self, text: str):
        print("--------------------------------------------------------------")
        print(f"[DEBUG] Speaking: {text}")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
            path = fp.name

        await edge_tts.Communicate(text, voice="en-US-JennyNeural").save(path)
        proc = await asyncio.create_subprocess_exec(
            "mpg123", "-q", "-a", "plughw:3,0", path,   # USB-спикер card3
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        os.remove(path)


    # ---------- helper to change ALSA mixer ----------
    async def Set_System_Volume(self, percent: int):
        print("--------------------------------------------------------------")
        print(f"[DEBUG] amixer > {percent}%")

        # try common control names
        for ctl in ("Master", "PCM", "Speaker", "Headphone"):
            proc = await asyncio.create_subprocess_exec(
                "amixer", "-q", "-c", "3", "set", ctl, f"{percent}%",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            if proc.returncode == 0:
                print(f"[DEBUG] volume control '{ctl}' OK")
                return

        # fallback: pick first available control
        proc = await asyncio.create_subprocess_exec(
            "amixer", "-c", "3", "scontrols",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await proc.communicate()
        first = (
            out.decode().split("'")[1]  # 'Name',0 > ���� Name
            if out else None
        )
        if first:
            await asyncio.create_subprocess_exec(
                "amixer", "-q", "-c", "3", "set", first, f"{percent}%",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            print(f"[DEBUG] volume control '{first}' OK")
        else:
            print("[DEBUG] no mixer control found")