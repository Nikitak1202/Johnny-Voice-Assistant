import asyncio
import contextlib
from datetime import datetime
from typing import Callable, Iterable, List, Optional


def _copy_frame(frame: List[List[int]]) -> List[List[int]]:
    return [row[:] for row in frame]


class _MemoryDevice:
    """Simple in-memory framebuffer used when hardware is unavailable."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._last_frame: List[List[int]] = [[0] * width for _ in range(height)]


    def show(self, frame: List[List[int]]) -> None:
        self._last_frame = _copy_frame(frame)


class Disp:
    """MAX7219 display controller with cooperative, cancellable animations."""

    def __init__(
        self,
        device: Optional[object] = None,
        cascaded: int = 4,
        module_size: int = 8,
        contrast: int = 20,
        time_provider: Optional[Callable[[], datetime]] = None,
        clock_interval: float = 1.0,
        blink_interval: float = 0.5,
    ):
        self.device = device or self._create_device(cascaded, module_size, contrast)
        self.width = getattr(self.device, "width", cascaded * module_size)
        self.height = getattr(self.device, "height", module_size)

        self._time_provider = time_provider or datetime.now
        self._clock_interval = clock_interval
        self._blink_interval = blink_interval

        self._render_lock = asyncio.Lock()
        self._override_lock = asyncio.Lock()

        self._base_frame = self._blank_frame()
        self._desired_frame = self._blank_frame()
        self._last_frame = self._blank_frame()

        self._clock_task: Optional[asyncio.Task] = None
        self._blink_task: Optional[asyncio.Task] = None
        self._override = False
        self._blink_bad_air = False
        self._blink_phase = False

        print("------------------------------------------------------------------------")
        print("[DEBUG] Display module initialised")


    # ------------------------------------------------------------------ utils
    def _create_device(self, cascaded: int, module_size: int, contrast: int):
        try:
            from luma.core.interface.serial import noop, spi
            from luma.led_matrix.device import max7219
            from PIL import Image
        except ImportError:
            print("[DEBUG] luma library unavailable – using memory framebuffer")
            return _MemoryDevice(cascaded * module_size, module_size)

        try:
            serial = spi(port=0, device=0, gpio=noop())
            device = max7219(
                serial,
                cascaded = cascaded,
                block_orientation = -90,
                blocks_arranged_in_reverse_order = False,
            )
            device.contrast(contrast)

            class _Adapter:
                def __init__(self, inner):
                    self.inner = inner
                    self.width = inner.width
                    self.height = inner.height
                    self.Image = Image

                def show(self, frame: List[List[int]]) -> None:
                    image = self.Image.new("1", (self.width, self.height))
                    for y, row in enumerate(frame):
                        for x, val in enumerate(row):
                            image.putpixel((x, y), 255 if val else 0)
                    self.inner.display(image)

            return _Adapter(device)
        except Exception as exc:
            print("[DEBUG] Failed to initialise MAX7219:", exc)
            print("[DEBUG] Falling back to memory framebuffer")
            return _MemoryDevice(cascaded * module_size, module_size)


    def _blank_frame(self) -> List[List[int]]:
        return [[0] * self.width for _ in range(self.height)]


    def _glyphs(self) -> dict:
        return {
            "0": [
                " ### ",
                "#   #",
                "#   #",
                "#   #",
                "#   #",
                "#   #",
                " ### ",
            ],
            "1": [
                "  #  ",
                " ##  ",
                "  #  ",
                "  #  ",
                "  #  ",
                "  #  ",
                " ### ",
            ],
            "2": [
                " ### ",
                "#   #",
                "    #",
                "   # ",
                "  #  ",
                " #   ",
                "#####",
            ],
            "3": [
                " ### ",
                "#   #",
                "    #",
                "  ## ",
                "    #",
                "#   #",
                " ### ",
            ],
            "4": [
                "#   #",
                "#   #",
                "#   #",
                "#####",
                "    #",
                "    #",
                "    #",
            ],
            "5": [
                "#####",
                "#    ",
                "#### ",
                "    #",
                "    #",
                "#   #",
                " ### ",
            ],
            "6": [
                " ### ",
                "#    ",
                "#    ",
                "#### ",
                "#   #",
                "#   #",
                " ### ",
            ],
            "7": [
                "#####",
                "    #",
                "   # ",
                "   # ",
                "  #  ",
                "  #  ",
                "  #  ",
            ],
            "8": [
                " ### ",
                "#   #",
                "#   #",
                " ### ",
                "#   #",
                "#   #",
                " ### ",
            ],
            "9": [
                " ### ",
                "#   #",
                "#   #",
                " ####",
                "    #",
                "    #",
                " ### ",
            ],
            ":": [
                "     ",
                "  #  ",
                "  #  ",
                "     ",
                "  #  ",
                "  #  ",
                "     ",
            ],
            "-": [
                "     ",
                "     ",
                "#####",
                "     ",
                "     ",
                "     ",
                "     ",
            ],
            "A": [
                " ### ",
                "#   #",
                "#   #",
                "#####",
                "#   #",
                "#   #",
                "#   #",
            ],
            "C": [
                " ### ",
                "#   #",
                "#    ",
                "#    ",
                "#    ",
                "#   #",
                " ### ",
            ],
            "D": [
                "#### ",
                "#   #",
                "#   #",
                "#   #",
                "#   #",
                "#   #",
                "#### ",
            ],
            "E": [
                "#####",
                "#    ",
                "#    ",
                "#### ",
                "#    ",
                "#    ",
                "#####",
            ],
            "F": [
                "#####",
                "#    ",
                "#    ",
                "#### ",
                "#    ",
                "#    ",
                "#    ",
            ],
            "G": [
                " ### ",
                "#   #",
                "#    ",
                "#    ",
                "#  ##",
                "#   #",
                " ####",
            ],
            "H": [
                "#   #",
                "#   #",
                "#   #",
                "#####",
                "#   #",
                "#   #",
                "#   #",
            ],
            "I": [
                " ### ",
                "  #  ",
                "  #  ",
                "  #  ",
                "  #  ",
                "  #  ",
                " ### ",
            ],
            "L": [
                "#    ",
                "#    ",
                "#    ",
                "#    ",
                "#    ",
                "#    ",
                "#####",
            ],
            "M": [
                "#   #",
                "## ##",
                "# # #",
                "# # #",
                "#   #",
                "#   #",
                "#   #",
            ],
            "N": [
                "#   #",
                "##  #",
                "# # #",
                "#  ##",
                "#   #",
                "#   #",
                "#   #",
            ],
            "O": [
                " ### ",
                "#   #",
                "#   #",
                "#   #",
                "#   #",
                "#   #",
                " ### ",
            ],
            "P": [
                "#### ",
                "#   #",
                "#   #",
                "#### ",
                "#    ",
                "#    ",
                "#    ",
            ],
            "R": [
                "#### ",
                "#   #",
                "#   #",
                "#### ",
                "# #  ",
                "#  # ",
                "#   #",
            ],
            "S": [
                " ####",
                "#    ",
                "#    ",
                " ### ",
                "    #",
                "    #",
                "#### ",
            ],
            "T": [
                "#####",
                "  #  ",
                "  #  ",
                "  #  ",
                "  #  ",
                "  #  ",
                "  #  ",
            ],
            "U": [
                "#   #",
                "#   #",
                "#   #",
                "#   #",
                "#   #",
                "#   #",
                " ### ",
            ],
            "V": [
                "#   #",
                "#   #",
                "#   #",
                "#   #",
                " # # ",
                " # # ",
                "  #  ",
            ],
            "W": [
                "#   #",
                "#   #",
                "# # #",
                "# # #",
                "# # #",
                "## ##",
                "#   #",
            ],
            "Y": [
                "#   #",
                "#   #",
                " # # ",
                "  #  ",
                "  #  ",
                "  #  ",
                "  #  ",
            ],
            "?": [
                " ### ",
                "#   #",
                "    #",
                "   # ",
                "  #  ",
                "     ",
                "  #  ",
            ],
            " ": [
                "     ",
                "     ",
                "     ",
                "     ",
                "     ",
                "     ",
                "     ",
            ],
        }


    def _render_text(self, text: str) -> List[List[int]]:
        glyphs = self._glyphs()
        columns: List[int] = []
        for ch in text.upper():
            pattern = glyphs.get(ch, glyphs["?"])
            width = len(pattern[0])
            for x in range(width):
                col = 0
                for y, row in enumerate(pattern):
                    if row[x] == "#":
                        col |= 1 << y
                columns.append(col)
            columns.append(0)

        frame = self._blank_frame()
        if not columns:
            return frame

        content_width = len(columns)
        x_offset = max((self.width - content_width) // 2, 0)
        y_offset = max((self.height - 7) // 2, 0)

        for x, col in enumerate(columns):
            target_x = x + x_offset
            if 0 <= target_x < self.width:
                for y in range(7):
                    if col & (1 << y):
                        target_y = y + y_offset
                        if 0 <= target_y < self.height:
                            frame[target_y][target_x] = 1

        return frame


    # ---------------------------------------------------------------- animations
    def _pattern_frame(self, pattern: Iterable[str]) -> List[List[int]]:
        rows = list(pattern)
        frame = self._blank_frame()
        if not rows:
            return frame
        height = len(rows)
        width = max(len(row) for row in rows)
        x_offset = max((self.width - width) // 2, 0)
        y_offset = max((self.height - height) // 2, 0)

        for y, row in enumerate(rows):
            padded = row.ljust(width, ".")
            for x, ch in enumerate(padded):
                if ch == "#":
                    tx = x + x_offset
                    ty = y + y_offset
                    if 0 <= tx < self.width and 0 <= ty < self.height:
                        frame[ty][tx] = 1

        return frame


    def _sun_frames(self) -> List[List[List[int]]]:
        patterns = [
            [
                ".......#.......",
                "...##..#..##...",
                "..#..#####..#..",
                ".#...#####...#.",
                ".#...#####...#.",
                "..#..#####..#..",
                "...##..#..##...",
                ".......#.......",
            ],
            [
                "....#.....#....",
                "..#..#...#..#..",
                ".#...#####...#.",
                ".#..#######..#.",
                ".#..#######..#.",
                ".#...#####...#.",
                "..#..#...#..#..",
                "....#.....#....",
            ],
        ]
        return [self._pattern_frame(p) for p in patterns]


    def _cloud_frames(self) -> List[List[List[int]]]:
        patterns = [
            [
                "..#######.......",
                ".#########......",
                "###########.....",
                "############....",
                "############....",
                ".##########.....",
                "..########......",
                "...######.......",
            ],
            [
                "...#######......",
                "..#########.....",
                ".###########....",
                "############....",
                "############....",
                "..##########....",
                "...########.....",
                "....######......",
            ],
        ]
        return [self._pattern_frame(p) for p in patterns]


    def _rain_frames(self) -> List[List[List[int]]]:
        patterns = [
            [
                "..#######.......",
                ".#########......",
                "###########.....",
                "############....",
                "#..#..#..#......",
                "..#..#..#.......",
                "...#..#..#......",
                "....#..#........",
            ],
            [
                "..#######.......",
                ".#########......",
                "###########.....",
                "############....",
                "...#..#..#......",
                "....#..#..#.....",
                ".....#..#..#....",
                "..#.....#.......",
            ],
        ]
        return [self._pattern_frame(p) for p in patterns]


    def _snow_frames(self) -> List[List[List[int]]]:
        patterns = [
            [
                "..#######.......",
                ".#########......",
                "###########.....",
                "############....",
                "#..#..#..#......",
                "..#..#..#.......",
                "#..#..#..#......",
                "..#..#..#.......",
            ],
            [
                "..#######.......",
                ".#########......",
                "###########.....",
                "############....",
                "..#..#..#.......",
                "#..#..#..#......",
                "..#..#..#.......",
                "#..#..#..#......",
            ],
        ]
        return [self._pattern_frame(p) for p in patterns]


    def _fog_frames(self) -> List[List[List[int]]]:
        patterns = [
            [
                "................",
                "..###########...",
                "................",
                "..###########...",
                "................",
                "..###########...",
                "................",
                "..###########...",
            ],
            [
                "................",
                "...###########..",
                "................",
                "...###########..",
                "................",
                "...###########..",
                "................",
                "...###########..",
            ],
        ]
        return [self._pattern_frame(p) for p in patterns]

    def _storm_frames(self) -> List[List[List[int]]]:
        patterns = [
            [
                "..#######.......",
                ".#########......",
                "###########.....",
                "############....",
                "############....",
                "....##..........",
                "...##...........",
                "..##............",
            ],
            [
                "..#######.......",
                ".#########......",
                "###########.....",
                "############....",
                "############....",
                "..##............",
                "...##...........",
                "....##..........",
            ],
        ]
        return [self._pattern_frame(p) for p in patterns]


    def _weather_animation(self, condition: str):
        kind = condition.lower()
        if kind in {"clear"}:
            return self._sun_frames(), 0.4, 6
        if kind in {"clouds"}:
            return self._cloud_frames(), 0.4, 6
        if kind in {"rain", "drizzle"}:
            return self._rain_frames(), 0.35, 8
        if kind in {"snow"}:
            return self._snow_frames(), 0.4, 8
        if kind in {"thunderstorm", "squall", "tornado"}:
            return self._storm_frames(), 0.35, 8
        if kind in {"mist", "fog", "smoke", "haze", "dust", "sand", "ash"}:
            return self._fog_frames(), 0.3, 6
        return [], 0.0, 0


    # ---------------------------------------------------------------- runtime
    async def start(self):
        if self._clock_task and not self._clock_task.done():
            return
        print("------------------------------------------------------------------------")
        print("[DEBUG] Display loop starting")
        self._clock_task = asyncio.create_task(self._clock_loop())
        self._blink_task = asyncio.create_task(self._blink_loop())


    async def stop(self):
        print("------------------------------------------------------------------------")
        print("[DEBUG] Display loop stopping")
        tasks = [t for t in (self._clock_task, self._blink_task) if t]
        for task in tasks:
            task.cancel()
        for task in tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._clock_task = None
        self._blink_task = None
        await self._set_frame(self._blank_frame())


    async def _clock_loop(self):
        try:
            while True:
                now = self._time_provider()
                frame = self.render_time_frame(now.hour, now.minute)
                self._base_frame = frame
                if not self._override:
                    await self._set_frame(frame)
                await asyncio.sleep(self._clock_interval)
        except asyncio.CancelledError:
            raise


    async def _blink_loop(self):
        try:
            while True:
                await asyncio.sleep(self._blink_interval)
                async with self._render_lock:
                    if not self._blink_bad_air:
                        if self._blink_phase:
                            self._blink_phase = False
                            await self._apply_frame_locked()
                        continue
                    self._blink_phase = not self._blink_phase
                    await self._apply_frame_locked()
        except asyncio.CancelledError:
            raise


    async def _set_frame(self, frame: List[List[int]]):
        async with self._render_lock:
            self._desired_frame = _copy_frame(frame)
            await self._apply_frame_locked()


    async def _apply_frame_locked(self):
        frame = self._desired_frame
        if self._blink_bad_air and self._blink_phase:
            frame = self._blank_frame()
        await asyncio.to_thread(self.device.show, frame)
        self._last_frame = _copy_frame(frame)


    # ---------------------------------------------------------------- helpers
    def render_time_frame(self, hour: int, minute: int) -> List[List[int]]:
        return self._render_text(f"{hour:02d}:{minute:02d}")


    def render_text_frame(self, text: str) -> List[List[int]]:
        return self._render_text(text)


    async def update_air_quality(self, gas_value: Optional[int]):
        if gas_value is None:
            return
        is_bad = not bool(gas_value)
        async with self._render_lock:
            self._blink_bad_air = is_bad
            if not is_bad:
                self._blink_phase = False
            await self._apply_frame_locked()


    async def _hold_text(self, text: str, duration: float):
        frame = self._render_text(text)
        await self._set_frame(frame)
        await asyncio.sleep(duration)


    async def _run_animation(self, frames: List[List[List[int]]], delay: float, cycles: int):
        for _ in range(cycles):
            for frame in frames:
                await self._set_frame(frame)
                await asyncio.sleep(delay)


    async def _takeover(self):
        class _Takeover:
            def __init__(self, outer: "Disp"):
                self.outer = outer

            async def __aenter__(self):
                await self.outer._override_lock.acquire()
                self.outer._override = True

            async def __aexit__(self, exc_type, exc, tb):
                self.outer._override = False
                try:
                    await asyncio.shield(self.outer._set_frame(self.outer._base_frame))
                finally:
                    self.outer._override_lock.release()

        return _Takeover(self)


    # ---------------------------------------------------------------- public API
    async def show_weather(self, info: dict):
        condition = info.get("condition", "unknown") or "unknown"
        frames, delay, cycles = self._weather_animation(condition)
        texts: List[str] = []
        if info.get("temp") is not None:
            texts.append(f"{int(round(info['temp'])):02d}C")
        if info.get("humidity") is not None:
            texts.append(f"H{int(round(info['humidity'])):02d}")
        if not frames:
            label = (condition or "?").upper()
            texts = [label[:4]] + texts

        async with await self._takeover():
            if frames:
                await self._run_animation(frames, delay, cycles)
            for text in texts:
                await self._hold_text(text, 1.6)


    async def show_city_time(self, hour: Optional[int], minute: Optional[int]):
        async with await self._takeover():
            if hour is None or minute is None:
                await self._hold_text("TIME", 1.8)
            else:
                frame = self.render_time_frame(hour, minute)
                await self._set_frame(frame)
                await asyncio.sleep(2.2)


    async def show_volume(self, percent: int):
        async with await self._takeover():
            await self._hold_text(f"{percent}", 2.0)


    async def show_sensor(self, temperature: Optional[float], humidity: Optional[float]):
        async with await self._takeover():
            if temperature is None and humidity is None:
                await self._hold_text("SENS", 2.0)
            else:
                if temperature is not None:
                    temp_val = int(round(temperature))
                    label = f"T-{abs(temp_val):02d}" if temp_val < 0 else f"T{temp_val:02d}"
                    await self._hold_text(label, 1.6)
                if humidity is not None:
                    await self._hold_text(f"H{int(round(humidity)):02d}", 1.6)


    def last_frame(self) -> List[List[int]]:
        return _copy_frame(self._last_frame)
