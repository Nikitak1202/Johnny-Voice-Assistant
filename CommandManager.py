import asyncio, os, tempfile, speech_recognition as sr, edge_tts
from DataManager import DataManager
from nlp import NLP
from CityInfo import CityInfo
import websockets


class CommandManager:
    """
    Continuously listens for a wake-word (“start” by default).  
    When the wake-word is heard, the current command task (if any) is cancelled
    and the remainder of the sentence is processed as a new command.
    """

    def __init__(self, wake_word: str = "start"):
        # helpers / state --------------------------------------------------
        self.WakeWord    = wake_word
        self.Volume      = 80
        self.running    = None                 # current Task

        # subsystems -------------------------------------------------------
        self.DataManager = DataManager()
        self.NLP         = NLP()
        self.CityInfo    = CityInfo("486c05914b1d1a5c9ea00ce1568a64d6")
        self.Rec         = sr.Recognizer()
        self.Mic         = sr.Microphone()

        print("--------------------------------------------------------------")
        print("[DEBUG] Command Manager is ready")


    async def send_data(self):
        uri = "ws://192.168.209.250:3000"
        async with websockets.connect(uri) as websocket:
            data = await self.DataManager.Measure_MicroClimate()
            try:
                await websocket.send(data)
            except websockets.ConnectionClosed:
                print("[DEBUG] WebSocket connection closed, retrying...")
                return
            print("[DEBUG] Data sent successfully")
            
            # wait for a while before sending again to avoid flooding the server
            await asyncio.sleep(1)


    # =============== continuous microphone loop ==========================
    async def Listen_Loop(self):
        def sync_listen():
            with self.Mic as src:
                self.Rec.adjust_for_ambient_noise(src)
                audio = self.Rec.listen(src, timeout=30)
            return self.Rec.recognize_google(audio, language="en-US")

        while True:
            try:
                phrase = await asyncio.to_thread(sync_listen)
                print("--------------------------------------------------------------")
                print(f"[DEBUG] Heard: {phrase}")
                yield phrase
            except (sr.UnknownValueError, sr.WaitTimeoutError):
                print("--------------------------------------------------------------")
                print("[DEBUG] Listen timeout / unintelligible")
            except sr.RequestError as e:
                print("--------------------------------------------------------------")
                print(f"[DEBUG] Google STT error: {e}")


    # =============== Executes one command; may be cancelled at any time ======================
    async def Run_Command(self, command_text: str):
        intent = self.NLP.Interpret_Command(command_text)
        print("--------------------------------------------------------------")
        print(f"[DEBUG] Intent: {intent}")

        try:
            # --- sensor ---------------------------------------------------
            if intent == "sensor":
                await self.DataManager.Measure_MicroClimate()
                if self.DataManager.temp is None:
                    reply = "Sorry, I couldn't read the sensor data."
                else:
                    air = "good" if self.DataManager.gas else "bad"
                    reply = (f"The average temperature is {self.DataManager.temp:.1f}°C and "
                             f"humidity is {self.DataManager.humidity:.1f}%. Air quality is {air}.")

            # --- time -----------------------------------------------------
            elif intent == "time":
                city  = self.NLP.Extract_City(command_text) or "Seoul"
                reply = self.CityInfo.Get_Time(city)

            # --- weather --------------------------------------------------
            elif intent == "weather":
                city  = self.NLP.Extract_City(command_text) or "Seoul"
                reply = await self.CityInfo.Get_Weather(city)

            # --- volume ---------------------------------------------------
            elif intent == "volume":
                reply = await self.handle_volume(command_text)

            # --- math -----------------------------------------------------
            elif intent == "calculate":
                expr  = self.NLP.Extract_Expression(command_text)
                try:
                    reply = f"The result of {expr} is {eval(expr)}."
                except Exception:
                    reply = "Sorry, I couldn't understand the expression."

            else:
                reply = "I didn't understand your request."

            print("--------------------------------------------------------------")
            print(f"[DEBUG] Reply: {reply}")
            await self.Speak(reply)

        except asyncio.CancelledError:
            # any long-running work or TTS is aborted instantly
            print("[DEBUG] Command task cancelled")
            raise

    # =============== Generate TTS and speak ======================================
    async def Speak(self, text: str):
        print("--------------------------------------------------------------")
        print(f"[DEBUG] Speaking: {text}")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
            path = fp.name

        await edge_tts.Communicate(text, voice="en-US-JennyNeural").save(path)

        proc = await asyncio.create_subprocess_exec(
            "mpg123", "-q", "-a", "plughw:3,0", path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            await proc.wait()
        finally:                               # ensure cleanup on cancel
            proc.terminate()
            os.remove(path)

    # =============== volume helpers ======================================
    async def handle_volume(self, text: str):
        action = self.NLP.Extract_Volume(text)
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

    async def Set_System_Volume(self, percent: int):
        """Try common mixer controls; pick the first that works."""
        print("--------------------------------------------------------------")
        print(f"[DEBUG] amixer → {percent}%")
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

        # fallback: first available simple control
        proc = await asyncio.create_subprocess_exec(
            "amixer", "-c", "3", "scontrols",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await proc.communicate()
        first = out.decode().split("'")[1] if out else None
        if first:
            await asyncio.create_subprocess_exec(
                "amixer", "-q", "-c", "3", "set", first, f"{percent}%",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            print(f"[DEBUG] volume control '{first}' OK")
        else:
            print("[DEBUG] no mixer control found")