# Smart Voice Assistant

## Description
This repository contains the Python implementation of a smart voice assistant using asyncio for asynchronous execution. It continuously listens for a wake-word (default "start"), interprets commands, and performs actions such as adjusting system volume, reporting weather and time, calculating mathematical expressions, and streaming sensor data (temperature, humidity, gas detection) through a WebSocket connection.

## Features
- **Voice Command Recognition**: Utilizes Google's Speech Recognition API.
- **Command Interpretation (NLP)**: Parses voice commands into structured intents.
- **Sensor Data Collection**: Measures temperature, humidity (DHT11), and air quality (MQ gas sensor).
- **WebSocket Data Streaming**: Periodically sends collected sensor data to a specified WebSocket server.
- **Text-to-Speech (TTS)**: Provides audio feedback using Edge TTS.

## Project Structure
```
├── CommandManager.py      # Core command handling logic
├── DataManager.py         # Handles sensor data collection
├── NLP.py                 # Natural language processing utilities
├── CityInfo.py            # Retrieves weather and time information
├── main.py                # Main executable script
├── requirements.txt       # Required Python packages
└── README.md              # Project description
```

## Requirements
- Python 3.10 or later
- Packages listed in `requirements.txt`

## Installation
1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage
To run the voice assistant, execute:
```bash
python main.py
```

## Changing the Wake Word
You can modify the wake word by editing the instantiation of `CommandManager` in `main.py`:
```python
cm = CommandManager(wake_word="your_wake_word")
```

## Data Streaming
Sensor data is automatically sent every 60 seconds via WebSocket. You can adjust this interval by modifying `DATA_PUSH_INTERVAL` in `main.py`:
```python
DATA_PUSH_INTERVAL = 60  # Adjust as needed
```

## License
This project is open-source and available under the MIT License.
