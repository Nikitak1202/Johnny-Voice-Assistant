# Collects sensor data (DHT11 + gas GPIO)
import asyncio
import time
import json
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

        # Create devices once
        self._dht = adafruit_dht.DHT11(self.DHT11Pin)
        self._gas = DigitalInputDevice(self.GasPin)

        print("------------------------------------------------------------------------\n")
        print("[DEBUG] DataManager initialised")

    # Parallel read of DHT11 and gas sensor
    async def Measure_MicroClimate(self):
        print("------------------------------------------------------------------------\n")
        print("[DEBUG] Measuring micro-climate")

        dht_task = asyncio.create_task(self.ReadDHT11(attempts=6, interval=2.2))
        gas_task = asyncio.create_task(self.ReadGas())

        # Don't let exceptions kill the caller; fold them into None-values
        dht_res, gas_res = await asyncio.gather(dht_task, gas_task, return_exceptions=True)

        if isinstance(dht_res, Exception):
            print("------------------------------------------------------------------------\n")
            print(f"[DEBUG] DHT11 fatal error: {dht_res!r}")
            self.temp, self.humidity = None, None
        else:
            self.temp, self.humidity = dht_res

        if isinstance(gas_res, Exception):
            print("------------------------------------------------------------------------\n")
            print(f"[DEBUG] GAS read error: {gas_res!r}")
            self.gas = None
        else:
            self.gas = gas_res

        print("------------------------------------------------------------------------\n")
        print(f"[DEBUG] Temp={self.temp}  Hum={self.humidity}  Gas={self.gas}")

        return json.dumps({
            "temperature": self.temp,
            "humidity": self.humidity,
            "gas": self.gas
        })

    # Return digital value from MQ-sensor pin (1 = clean air)
    async def ReadGas(self):
        return await asyncio.to_thread(lambda: self._gas.value)

    # Average DHT11 temperature + humidity over several attempts
    async def ReadDHT11(self, attempts: int = 6, interval: float = 2.2):
        def sync_read():
            temps, hums = [], []
            for _ in range(int(attempts)):
                try:
                    t = self._dht.temperature
                    h = self._dht.humidity
                    if (t is not None) and (h is not None):
                        temps.append(float(t))
                        hums.append(float(h))
                except RuntimeError as err:
                    print("------------------------------------------------------------------------\n")
                    print(f"[DEBUG] DHT11 warn: {err.args[0]}")
                time.sleep(max(2.0, float(interval)))  # DHT must not be polled faster than ~2s
            avg_t = (sum(temps) / len(temps)) if temps else None
            avg_h = (sum(hums) / len(hums)) if hums else None
            return avg_t, avg_h

        return await asyncio.to_thread(sync_read)
