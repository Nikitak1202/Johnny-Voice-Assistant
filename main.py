import asyncio
from CommandManager import CommandManager

async def main():
    cm = CommandManager()
    async for phrase in cm.Listen_Loop():
        # wake-word check
        if cm.WakeWord in phrase.lower():
            # stop current command if still running
            if cm.running and not cm.running.done():
                cm.running.cancel()
                try:
                    await cm.running
                except asyncio.CancelledError:
                    pass

            # extract text after wake-word
            cmd_txt = phrase.lower().split(cm.WakeWord, 1)[1].strip()
            if not cmd_txt:
                print("[DEBUG] Wake word only, waiting next phrase")
                continue

            # launch new command task
            cm.running = asyncio.create_task(cm.Run_Command(cmd_txt))

if __name__ == "__main__":
    asyncio.run(main())