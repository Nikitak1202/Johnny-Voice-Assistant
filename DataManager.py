# Collects sensor data (DHT11 + gas GPIO)
import asyncio
import time
import board
import adafruit_dht
from gpiozero import DigitalInputDevice


class DataManager:
    def __init__(self):
        self.temp = None
        self.humidity = None
        self.gas = None

        self.DHT11Pin = board.D17          # GPIO-17
        self.GasPin = 27                   # GPIO-27
        print("───────────────────────────────────────────────────────────\n")
        print("[DEBUG] DataManager initialised")


    # Parallel read of DHT11 and gas sensor
    async def Measure_MicroClimate(self):
        print("───────────────────────────────────────────────────────────\n")
        print("[DEBUG] Measuring micro-climate")
        dht_task = asyncio.create_task(self.ReadDHT11())
        gas_task = asyncio.create_task(self.ReadGas())
        self.temp, self.humidity = await dht_task
        self.gas = await gas_task
        print("───────────────────────────────────────────────────────────\n")
        print(f"[DEBUG] Temp={self.temp}  Hum={self.humidity}  Gas={self.gas}")


    # Return digital value from MQ-sensor pin (1 = clean air)
    async def ReadGas(self):
        return await asyncio.to_thread(lambda: DigitalInputDevice(self.GasPin).value)


    # Average DHT11 temperature + humidity over <samples> reads
    async def ReadDHT11(self, samples: int = 10):
        def sync_read():
            dht = adafruit_dht.DHT11(self.DHT11Pin)
            temps, hums = [], []
            for _ in range(samples):
                try:
                    temps.append(dht.temperature)
                    hums.append(dht.humidity)
                except RuntimeError as err:
                    print("───────────────────────────────────────────────────────────\n")
                    print(f"[DEBUG] DHT11 error: {err.args[0]}")
                    time.sleep(1)
                    continue
                time.sleep(1)
            dht.exit()
            avg_t = sum(temps) / len(temps) if temps else None
            avg_h = sum(hums) / len(hums) if hums else None
            return avg_t, avg_h

        return await asyncio.to_thread(sync_read)