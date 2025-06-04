import time
import board
import adafruit_dht

class DataManager:
    def __init__(self):
        self.temp = None
        self.humidity = None
        self.gas = None


    def Measure_MicroClimate(self):
        self.gas = self.ReadGas()
        dht_data = ReadDHT11()
        self.temp = dht_data[0]
        self.humidity = dht_data[1]
        

    def ReadGas(self):
        return None


# --- DHT11 Sensor Reading ---
def ReadDHT11(samples=10):
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
    return [avg_t, avg_h]