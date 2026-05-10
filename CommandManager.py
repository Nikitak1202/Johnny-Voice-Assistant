import asyncio, os, tempfile, speech_recognition as sr, edge_tts
from DataManager import DataManager
from nlp import NLP
from CityInfo import CityInfo
from Disp import Disp


class CommandManager:
    """
    Continuous mode with wake-word (default) or MANUAL mode (keyboard input).
    """

    def __init__(self, wake_word: str = "start", manual: bool = False):
        # helpers / state --------------------------------------------------
        self.WakeWord  = wake_word
        self.Manual    = manual
        self.Volume    = 80
        self.running   = None

        # subsystems -------------------------------------------------------
        self.DataManager = DataManager()
        self.NLP         = NLP()
        self.CityInfo    = CityInfo("486c05914b1d1a5c9ea00ce1568a64d6")
        self.Rec         = sr.Recognizer()
        # do not touch audio hardware in MANUAL mode
        self.Mic         = None if self.Manual else sr.Microphone()
        self.Display     = Disp()

        print("--------------------------------------------------------------")
        print(f"[DEBUG] Command Manager is ready (MANUAL={self.Manual})")


    async def start(self):
        await self.Display.start()


    async def stop(self):
        await self.Display.stop()


    # =============== continuous input loop (mic or keyboard) ====================
    async def Listen_Loop(self):
        if self.Manual:
            # keyboard-driven loop
            while True:
                try:
                    phrase = await asyncio.to_thread(input, "[MANUAL] > ")
                    phrase = (phrase or "").strip()
                    if not phrase:
                        print("--------------------------------------------------------------")
                        print("[DEBUG] Empty input; waiting...")
                        continue
                    print("--------------------------------------------------------------")
                    print(f"[DEBUG] Heard (manual): {phrase}")
                    yield phrase
                except (EOFError, KeyboardInterrupt):
                    print("--------------------------------------------------------------")
                    print("[DEBUG] Manual input terminated")
                    await asyncio.sleep(0.05)
                    break
        else:
            # microphone-driven loop
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


    # =============== Executes one command; may be cancelled at any time =========
    async def Run_Command(self, command_text: str):
        intent = self.NLP.Interpret_Command(command_text)
        print("--------------------------------------------------------------")
        print(f"[DEBUG] Intent: {intent}")

        try:
            display_task = None
            # --- sensor ---------------------------------------------------
            if intent == "sensor":
                await self.DataManager.Measure_MicroClimate()
                await self.Display.update_air_quality(self.DataManager.gas)
                if self.DataManager.temp is None:
                    reply = "Sorry, I couldn't read the sensor data."
                else:
                    air = "good" if self.DataManager.gas else "bad"
                    reply = (f"The average temperature is {self.DataManager.temp:.1f}°C and "
                             f"humidity is {self.DataManager.humidity:.1f}%. Air quality is {air}.")
                display_task = asyncio.create_task(
                    self.Display.show_sensor(self.DataManager.temp, self.DataManager.humidity)
                )

            # --- time -----------------------------------------------------
            elif intent == "time":
                city  = self.NLP.Extract_City(command_text) or "Seoul"
                info  = self.CityInfo.Get_Time_Info(city)
                reply = info["speech"]
                display_task = asyncio.create_task(
                    self.Display.show_city_time(info.get("hour"), info.get("minute"))
                )

            # --- weather --------------------------------------------------
            elif intent == "weather":
                city  = self.NLP.Extract_City(command_text) or "Seoul"
                info  = await self.CityInfo.Get_Weather_Info(city)
                reply = info["speech"]
                display_task = asyncio.create_task(self.Display.show_weather(info))

            # --- volume ---------------------------------------------------
            elif intent == "volume":
                reply = await self.handle_volume(command_text)
                if reply.lower().startswith("volume set"):
                    display_task = asyncio.create_task(self.Display.show_volume(self.Volume))

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
            speak_task = asyncio.create_task(self.Speak(reply))
            if display_task:
                await asyncio.gather(speak_task, display_task)
            else:
                await speak_task

        except asyncio.CancelledError:
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
        finally:
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
        print("--------------------------------------------------------------")
        print(f"[DEBUG] amixer -> {percent}%")
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
