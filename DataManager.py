import time
import board
import adafruit_dht
import busio
from digitalio import DigitalInOut
from adafruit_mcp3xxx.mcp3008 import MCP3008
from adafruit_mcp3xxx.analog_in import AnalogIn, P0

class DataManager:
    # Initialization block: set up attributes for temperature, humidity, and gas readings
    def __init__(self):
        self.temp = None
        self.humidity = None
        self.gas = None

    # Measurement block: perform gas reading and DHT11 sensor reading, then store averages
    def Measure_MicroClimate(self):
        gas_data = self.ReadGas()
        dht_data = self.ReadDHT11()
        self.temp = dht_data[0] if dht_data[0] else None
        self.humidity = dht_data[1] if dht_data[1] else None
        self.gas = gas_data[0] if gas_data else None
        
    # Gas reading stub: placeholder method for future gas sensor integration
    def ReadGas(self):
        # SPI connection
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs = DigitalInOut(board.D8)  # CE0

        # Initialize MCP3008
        mcp = MCP3008(spi, cs)
        channel = AnalogIn(mcp, P0)

        return [channel.value, channel.voltage]


    # --- DHT11 Sensor Reading Block ---
    def ReadDHT11(self, samples=10):
        # Initialize DHT11 sensor on specified board pin
        dht = adafruit_dht.DHT11(board.D4)
        temps, hums = [], []
        for _ in range(samples):
            try:
                # Attempt to read temperature and humidity from the sensor
                t = dht.temperature
                h = dht.humidity
                print(f"Temp: {t}°C, Humid: {h}%")
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