# Event-loop: listen > detect wake word > answer > speak
import asyncio
from CommandManager import CommandManager

WAKE_WORD = "start"

async def main():
    cm = CommandManager()
    while True:
        phrase = await cm.recognize_once()
        if not phrase:
            continue
        low = phrase.lower()
        if WAKE_WORD in low:
            cmd = phrase[low.find(WAKE_WORD) + len(WAKE_WORD):].strip()
            if not cmd:
                continue
            response = await cm.process_command(cmd)
            print("Response:", response)
            await cm.speak(response)

if __name__ == "__main__":
    asyncio.run(main())
