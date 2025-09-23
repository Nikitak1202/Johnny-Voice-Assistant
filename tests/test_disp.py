import asyncio
import threading
import unittest
from datetime import datetime

from Disp import Disp


def frame_to_tuple(frame):
    return tuple(tuple(row) for row in frame)


class MockDevice:
    def __init__(self, width: int = 32, height: int = 8):
        self.width = width
        self.height = height
        self.frames: list[tuple[tuple[int, ...], ...]] = []
        self._lock = threading.Lock()
        blank = tuple(tuple(0 for _ in range(width)) for _ in range(height))
        self.last_frame = blank

    def show(self, frame):
        snapshot = frame_to_tuple(frame)
        with self._lock:
            self.frames.append(snapshot)
            self.last_frame = snapshot


class FakeClock:
    def __init__(self, dt: datetime):
        self.current = dt

    def __call__(self):
        return self.current


class DispTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.clock = FakeClock(datetime(2023, 1, 1, 12, 34))
        self.device = MockDevice()
        self.disp = Disp(
            device=self.device,
            time_provider=self.clock,
            clock_interval=0.05,
            blink_interval=0.05,
        )
        await self.disp.start()
        await asyncio.sleep(0.1)

    async def asyncTearDown(self):
        await self.disp.stop()

    async def test_clock_renders_time(self):
        expected = frame_to_tuple(self.disp.render_time_frame(12, 34))
        await asyncio.sleep(0.1)
        self.assertIn(expected, self.device.frames)

    async def test_volume_display(self):
        await self.disp.show_volume(73)
        vol_frame = frame_to_tuple(self.disp.render_text_frame("73"))
        self.assertIn(vol_frame, self.device.frames)
        await asyncio.sleep(0.1)
        base_frame = frame_to_tuple(self.disp.render_time_frame(12, 34))
        self.assertEqual(self.device.last_frame, base_frame)

    async def test_weather_animation(self):
        info = {
            "condition": "Clear",
            "temp": 24.6,
            "humidity": 55,
            "speech": "",
            "ok": True,
            "city": "Test",
            "description": "clear sky",
        }
        await self.disp.show_weather(info)
        temp_frame = frame_to_tuple(self.disp.render_text_frame("25C"))
        hum_frame = frame_to_tuple(self.disp.render_text_frame("H55"))
        self.assertIn(temp_frame, self.device.frames)
        self.assertIn(hum_frame, self.device.frames)

    async def test_city_time_display(self):
        await self.disp.show_city_time(5, 7)
        city_frame = frame_to_tuple(self.disp.render_time_frame(5, 7))
        self.assertIn(city_frame, self.device.frames)
        await asyncio.sleep(0.1)
        base_frame = frame_to_tuple(self.disp.render_time_frame(12, 34))
        self.assertEqual(self.device.last_frame, base_frame)

    async def test_sensor_and_air_quality(self):
        await self.disp.show_sensor(23.4, 47.8)
        temp_frame = frame_to_tuple(self.disp.render_text_frame("T23"))
        hum_frame = frame_to_tuple(self.disp.render_text_frame("H48"))
        self.assertIn(temp_frame, self.device.frames)
        self.assertIn(hum_frame, self.device.frames)

        await self.disp.update_air_quality(0)
        await self.disp.show_volume(80)
        await asyncio.sleep(0.2)
        blank = frame_to_tuple([[0] * self.device.width for _ in range(self.device.height)])
        self.assertIn(blank, self.device.frames)

        await self.disp.update_air_quality(1)
        await asyncio.sleep(0.1)
        self.assertNotEqual(self.device.last_frame, blank)

    async def test_weather_cancellation_resets_clock(self):
        info = {
            "condition": "Rain",
            "temp": 10.0,
            "humidity": 80,
            "speech": "",
            "ok": True,
            "city": "Test",
            "description": "rain",
        }
        task = asyncio.create_task(self.disp.show_weather(info))
        await asyncio.sleep(0.2)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        await asyncio.sleep(0.1)
        base_frame = frame_to_tuple(self.disp.render_time_frame(12, 34))
        self.assertEqual(self.device.last_frame, base_frame)


if __name__ == "__main__":
    unittest.main()
