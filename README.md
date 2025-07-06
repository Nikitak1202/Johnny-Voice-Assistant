# Johnny Voice Assistant

**Johnny** is an offline-first, extensible Python voice assistant that runs on Windows, macOS and Linux.  
It combines speech recognition, natural-language parsing and text-to-speech to let you control your PC, query information and automate everyday tasks with simple voice commands.

---

## ✨  Key Features
| Category | Details |
|----------|---------|
| **Speech I/O** | • Offline speech recognition (Vosk) <br> • High-quality TTS via pyttsx3 (cross-platform) |
| **Command Manager** | Central `CommandManager` routes utterances to skills; add new commands with one function |
| **Built-in Skills** | • Weather & city info<br>• System time & date<br>• Jokes / small talk<br>• Application launcher |
| **Extensible** | Drop a new Python file in `./skills` or add a method in `CommandManager` to teach Johnny a new trick |
| **Config-free start** | No cloud keys required for default setup; optional OpenWeatherMap key for richer forecasts |
| **Cross-platform** | Runs wherever Python ≥ 3.8 is available |

---
> Tested on Python 3.11, but any 3.8+ interpreter should work.
