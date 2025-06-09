import speech_recognition as sr
import tempfile
import edge_tts
import os
import re
from datetime import datetime
from DataManager import DataManager

class CommandManager:
    # Initialization block: set up DataManager instance and speech recognition components
    def __init__(self):
        self.DataManager = DataManager()
        self.SpeechRecognizer = sr.Recognizer()
        self.Microphone = sr.Microphone()


    def Start_Word_Detection(self):
        # Start listening for the wake word (start) in a loop
        with self.Microphone as source:
            print("Listening for wake word...")
            self.SpeechRecognizer.adjust_for_ambient_noise(source)
            while True:
                try:
                    audio = self.SpeechRecognizer.listen(source, timeout=1)
                    command = self.SpeechRecognizer.recognize_google(audio, language='en-US')
                    if "start" in command.lower():
                        print("Wake word detected!")
                        return True
                    
                except sr.UnknownValueError:
                    print("Could not understand you.")
                    return False
                except sr.RequestError as e:
                    print(f"API request error: {e}")
                    return False
                except sr.WaitTimeoutError:
                    print("Listening timed out while waiting for phrase to start.")
                    return False


    # Main entry point for generating a response: recognize speech, process command, and return answer
    def Create_Answer(self):
        # Step 1: Recognize speech from the microphone
        command = self.Recognize_Speech()
        if not command:
            return "Sorry, I didn't catch what you have said."

        # Step 2: Process the recognized command and form a response
        answer = self.Process_Command(command)
        return answer

    
    # Speech recognition block: listen on the microphone and convert audio to text
    def Recognize_Speech(self):
        with self.Microphone as source:
            print("Speak...")
            self.SpeechRecognizer.adjust_for_ambient_noise(source)
            audio = self.SpeechRecognizer.listen(source)

        try:
            text = self.SpeechRecognizer.recognize_google(audio, language='en-US')
            print("Recognized:", text)
            return text
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return ""
        except sr.RequestError as e:
            print(f"API request error: {e}")
            return ""

    
    # Intent interpretation block: determine user intent based on keywords in the recognized text
    def Interpret_Command(self, text):
        text = text.lower()

        if any(word in text for word in ["temperature", "humidity", "weather"]):
            return "sensor"
        elif "time" in text:
            return "time"
        elif any(op in text for op in ['+', '-', '*', '/']) or "calculate" in text:
            return "calculate"
        else:
            return "unknown"

    
    # Expression extraction block: isolate numbers and operators from the text for calculation
    def Extract_Expression(self, text):
        match = re.findall(r'[\d\.]+|[+\-*/]', text)
        return " ".join(match) if match else ""

    
    # Command processing block: route to appropriate functionality based on detected intent
    def Process_Command(self, command):
        intent = self.Interpret_Command(command)
        
        if intent == "sensor":
            # Sensor reading block: perform measurement and build response string
            self.DataManager.Measure_MicroClimate()

            if self.DataManager.temp is not None:
                print(f"The average temperature is {self.DataManager.temp:.1f}°C and humidity is {self.DataManager.humidity:.1f}%.")
                if not self.DataManager.gas:
                    print("Air quality is bad")
                else:
                    print("Air quality is good")
                return f"The average temperature is {self.DataManager.temp:.1f}°C and humidity is {self.DataManager.humidity:.1f}%."
            else:
                return "Sorry, I couldn't read the sensor data."

        elif intent == "time":
            # Time reporting block: retrieve current system time and format it
            now = datetime.now()
            return f"The current time is {now.strftime('%H:%M:%S')}."

        elif intent == "calculate":
            # Calculation block: extract numeric expression, evaluate, and return result
            expression = self.Extract_Expression(command)
            try:
                result = eval(expression)
                return f"The result of {expression} is {result}."
            except Exception:
                return "Sorry, I couldn't understand the expression."

        else:
            # Fallback block: handle unrecognized intents
            return "I didn't understand your request."
        

    # --- Text-to-Speech ---
    def Speak(self, text):
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
            path = fp.name
        communicate = edge_tts.Communicate(text, voice="en-US-JennyNeural")
        communicate.save(path)
        os.system(f"mpg123 {path}")
        os.remove(path)