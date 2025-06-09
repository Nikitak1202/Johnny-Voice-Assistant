import time
import board
import adafruit_dht
from gpiozero import DigitalInputDevice


class DataManager:
    # Set up attributes for temperature, humidity, and gas readings. GPIO initialization
    def __init__(self):
        self.temp = None
        self.humidity = None
        self.gas = None
        self.GasPin = 27
        self.DHT11Pin = board.D17 # GPIO 17


    # Measurement: perform gas reading and DHT11 sensor reading, then store averages
    def Measure_MicroClimate(self):
        dht_data = self.ReadDHT11()
        self.temp = dht_data[0] if dht_data[0] else None
        self.humidity = dht_data[1] if dht_data[1] else None
        self.gas = self.ReadGas()
    
        
    # Gas reading 
    def ReadGas(self):
        return DigitalInputDevice(self.GasPin).value


    # --- DHT11 Sensor Reading ---
    def ReadDHT11(self, samples=10):
        # Initialize DHT11 sensor on specified board pin
        dht = adafruit_dht.DHT11(self.DHT11Pin)
        temps, hums = [], []
        for _ in range(samples):
            try:
                # Attempt to read temperature and humidity from the sensor
                t = dht.temperature
                h = dht.humidity
                temps.append(t)
                hums.append(h)
            except RuntimeError as err:
                # Handle intermittent read errors by retrying after a short pause
                print(f"Sensor error: {err.args[0]}")
                time.sleep(1)
                continue
            time.sleep(1)
        # Clean up the sensor interface when done
        dht.exit()
        # Calculate average values if any readings succeeded
        avg_t = sum(temps) / len(temps) if temps else None
        avg_h = sum(hums) / len(hums) if hums else None
        return [avg_t, avg_h]