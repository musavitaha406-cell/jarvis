# J.A.R.V.I.S. — Persian Voice Assistant

An offline Persian voice assistant built with Python.

## Features
- Wake word: "جارویس"
- Offline speech recognition (Vosk)
- Intent classification (TF-IDF + SVM)
- Commands: time, open Chrome, Notepad, Calculator
- Animated HUD interface (tkinter)

## Setup
1. Install dependencies:
   pip install -r requirements.txt
2. Download vosk-model-small-fa-0.42 from https://alphacephei.com/vosk/models,
   extract it, and rename the folder to model next to the script.
3. Run:
   python jarvis.py

## Note
Commands use Windows (start chrome, start notepad, start calc).
