import asyncio
import contextlib
from CommandManager import CommandManager

# 
DATA_PUSH_INTERVAL = 60 # seconds between automatic sensor-data pushes          


# Forever: send sensor data, then sleep <interval> seconds
async def periodic_sender(cm: CommandManager, interval: int):
    while True:
        try:
            await cm.send_data()
        except Exception as e:
            print(f"[DEBUG] periodic send failure: {e}")
        await asyncio.sleep(interval)


async def main():
    cm = CommandManager()

    # start background task that streams data every <interval> seconds
    sender_task = asyncio.create_task(periodic_sender(cm, DATA_PUSH_INTERVAL))

    try:
        async for phrase in cm.Listen_Loop():
            if cm.WakeWord in phrase.lower():          # wake-word detected
                # cancel running command if still executing
                if cm.running and not cm.running.done():
                    cm.running.cancel()
                    try:
                        await cm.running
                    except asyncio.CancelledError:
                        pass

                cmd_txt = phrase.lower().split(cm.WakeWord, 1)[1].strip()
                if not cmd_txt:
                    print("[DEBUG] Wake word only, waiting next phrase")
                    continue

                cm.running = asyncio.create_task(cm.Run_Command(cmd_txt))

    finally:
        sender_task.cancel()                           # clean shutdown
        with contextlib.suppress(asyncio.CancelledError):
            await sender_task


if __name__ == "__main__":
    asyncio.run(main())