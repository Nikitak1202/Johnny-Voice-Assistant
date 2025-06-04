import re
import time
import board
import adafruit_dht
import asyncio
import tempfile
import os
import speech_recognition as sr
import edge_tts
from datetime import datetime
import ILI9225
from pyILI9225 import color565

# --- Speech Recognition ---
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

# --- Text-to-Speech ---
async def speak(text):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
        path = fp.name
    communicate = edge_tts.Communicate(text, voice="en-US-JennyNeural")
    await communicate.save(path)
    os.system(f"mpg123 {path}")
    os.remove(path)

# --- DHT11 Sensor Reading ---
def read_sensor(samples=10):
    dht = adafruit_dht.DHT11(board.D4)
    temps, hums = [], []
    for _ in range(samples):
        try:
            t = dht.temperature
            h = dht.humidity
            print(f"Temp: {t}°C, Humid: {h}%")
            temps.append(t)
            hums.append(h)
        except RuntimeError as err:
            print(f"Sensor error: {err.args[0]}")
            time.sleep(1)
            continue
        time.sleep(1)
    dht.exit()
    avg_t = sum(temps) / len(temps) if temps else None
    avg_h = sum(hums) / len(hums) if hums else None
    return {'temperature': avg_t, 'humidity': avg_h}

# --- Intent Recognition & Entity Extraction ---
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

def extract_expression(text):
    match = re.findall(r'[\d\.]+|[+\-*/]', text)
    return " ".join(match) if match else ""

# --- Main Chat Logic ---
def process_command(command):
    intent = interpret_command(command)

    if intent == "sensor":
        data = read_sensor()
        if data['temperature'] is not None:
            disp.fill_screen(color565(0, 0, 0))
            disp.text(
                    x = 10, y = 10,
                    text = f"Temp: {data['temperature']:.1f}C",
                    size = 2,
                    color = color565(255, 255, 0),
                    background = color565(0, 0, 0)
            )
            disp.text(
                    x = 10, y = 10,
                    text = f"Humid: {data['humidity']:.1f}%",
                    size = 2,
                    color = color565(0, 255, 255),
                    background = color565(0, 0, 0)
            )
            return f"The average temperature is {data['temperature']:.1f}°C and humidity is {data['humidity']:.1f}%."
        else:
            return "Sorry, I couldn't read the sensor data."

    elif intent == "time":
        now = datetime.now()
        return f"The current time is {now.strftime('%H:%M:%S')}."

    elif intent == "calculate":
        expression = extract_expression(command)
        try:
            result = eval(expression)
            return f"The result of {expression} is {result}."
        except:
            return "Sorry, I couldn't understand the expression."

    else:
        return "I didn't understand your request."

def init_display():
    rst_pin = 17
    dc_pin = 27
    cs_pin = 8
    spi_dev = 0

    disp = ILI9225(
            rst = rst_pin,
            dc = dc_pin,
            cs = cs_pin,
            spi_speed_hz = 8000000,
            spi_bus = spi_dev
            )
    return disp

# --- Main Program ---
if __name__ == "__main__":
    print("Voice AI Chatbot Ready!")
    disp = init_display()

    command = recognize_speech()
    if command:
        response = process_command(command)
        print("Response:", response)
        asyncio.run(speak(response))
