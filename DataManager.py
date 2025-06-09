# Sensor I/O and averaging are blocking, therefore each public method is executed in a thread
import asyncio, time, board, adafruit_dht
from gpiozero import DigitalInputDevice

class DataManager:
    # GPIO pin mapping and last-read values
    def __init__(self):
        self.temp = None
        self.humidity = None
        self.gas = None
        self._gas_pin = 27
        self._dht_pin = board.D17  # GPIO-17

    async def measure_microclimate(self):
        dht_task = asyncio.create_task(self._read_dht11())
        gas_task = asyncio.create_task(self._read_gas())
        self.temp, self.humidity = await dht_task
        self.gas = await gas_task

    async def _read_gas(self):
        return await asyncio.to_thread(lambda: DigitalInputDevice(self._gas_pin).value)

    async def _read_dht11(self, samples: int = 10):
        def _sync_read():
            dht = adafruit_dht.DHT11(self._dht_pin)
            temps, hums = [], []
            for _ in range(samples):
                try:
                    temps.append(dht.temperature)
                    hums.append(dht.humidity)
                except RuntimeError:
                    time.sleep(1)
                    continue
                time.sleep(1)
            dht.exit()
            avg_t = sum(temps) / len(temps) if temps else None
            avg_h = sum(hums) / len(hums) if hums else None
            return avg_t, avg_h
        return await asyncio.to_thread(_sync_read)
