import speech_recognition as sr
import re
from datetime import datetime

class DataManager:
    def create_answer(self):
        # Step 1: Recognize speech from the microphone
        command = self.recognize_speech()
        if not command:
            return "Sorry, I didn't catch that."

        # Step 2: Process the recognized command and form a response
        answer = self.process_command(command)
        return answer

    @staticmethod
    def recognize_speech():
        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        with mic as source:
            print("Speak...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio, language='en-US')
            print("Recognized:", text)
            return text
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return ""
        except sr.RequestError as e:
            print(f"API request error: {e}")
            return ""

    @staticmethod
    def interpret_command(text):
        text = text.lower()
        if any(word in text for word in ["temperature", "humidity", "weather"]):
            return "sensor"
        elif "time" in text:
            return "time"
        elif any(op in text for op in ['+', '-', '*', '/']) or "calculate" in text:
            return "calculate"
        else:
            return "unknown"

    @staticmethod
    def extract_expression(text):
        match = re.findall(r'[\d\.]+|[+\-*/]', text)
        return " ".join(match) if match else ""

    @staticmethod
    def read_sensor():
        # This is a placeholder function.
        # Replace this stub with actual sensor reading logic as needed.
        return {'temperature': 25.0, 'humidity': 50.0}

    @staticmethod
    def process_command(command):
        intent = DataManager.interpret_command(command)
        
        if intent == "sensor":
            data = DataManager.read_sensor()
            if data['temperature'] is not None:
                return f"The average temperature is {data['temperature']:.1f}°C and humidity is {data['humidity']:.1f}%."
            else:
                return "Sorry, I couldn't read the sensor data."

        elif intent == "time":
            now = datetime.now()
            return f"The current time is {now.strftime('%H:%M:%S')}."

        elif intent == "calculate":
            expression = DataManager.extract_expression(command)
            try:
                result = eval(expression)
                return f"The result of {expression} is {result}."
            except Exception:
                return "Sorry, I couldn't understand the expression."

        else:
            return "I didn't understand your request."