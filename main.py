import asyncio
from CommandManager import CommandManager


async def main():
    Alice = CommandManager()

    while True:
        phrase = await Alice.Listen_Phrase()
        if not phrase:
            continue

        reply = await Alice.Handle_Phrase(phrase)
        if reply:
            print("───────────────────────────────────────────────────────────\n")
            print(f"[DEBUG] Reply: {reply}")
            await Alice.Speak(reply)


if __name__ == "__main__":
    asyncio.run(main())