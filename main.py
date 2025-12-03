import asyncio
import contextlib
from CommandManager import CommandManager


async def main():
    cm = CommandManager(manual=False)
    await cm.start()

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
        await cm.stop()


if __name__ == "__main__":
    asyncio.run(main())