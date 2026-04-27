# AirCommand

A contactless desktop control system that uses hand gestures and voice commands. No mouse or keyboard required. Built with Python using a webcam and microphone.

This is the implementation described in the paper:
> Jaber, F. (2026). *AirCommand: A Multimodal Contactless Desktop-Control System Using Hand Gestures and Voice Commands.* Independent Researcher. https://github.com/Farah0Jaber/aircommand

---

## What it does

AirCommand runs two input pipelines in parallel:

- **Hand gestures** via webcam for cursor movement, clicking, scrolling, tab switching, volume, and zoom
- **Voice commands** via microphone for copy, paste, select, drag, click, and text entry

See the paper for the full command vocabulary and evaluation results.

---

## Requirements

- Windows (pycaw is Windows-only)
- Python 3.9 or later
- A webcam
- A microphone

---

## Setup

**1. Clone the repository**

```
git clone https://github.com/Farah0Jaber/aircommand.git
cd aircommand
```

**2. Create and activate a virtual environment**

```
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**

```
pip install -r requirements.txt
```

**4. Download the Vosk model**

Download the small US English model from the Vosk website:
https://alphacephei.com/vosk/models

The model used in this project is `vosk-model-small-en-us`. Download and unzip it, then rename the folder to `model` and place it in the root of the project directory so the path looks like:

```
aircommand/
    model/
        am/
        conf/
        graph/
        ivector/
        README
    main.py
    ...
```

---

## Running the system

Make sure your virtual environment is active, then run:

```
python main.py
```

Press `q` in the webcam window to exit.

---

## File overview

| File | Description |
|---|---|
| `main.py` | Entry point. Starts the voice listener thread and hand tracking loop |
| `hand_tracking.py` | Webcam capture, MediaPipe landmark processing, gesture detection, and hand command dispatch |
| `speech_commands.py` | Microphone input, Vosk speech recognition, command parsing, and voice command dispatch |
| `logger_utils.py` | CSV event logger used for evaluation |
| `make_latency_figure.py` | Script used to generate the latency figure and table from the evaluation log |
| `Figures/` | Scripts used to generate the figures and tables in the paper |

---

## Dependencies

- [MediaPipe](https://github.com/google-ai-edge/mediapipe)
- [OpenCV](https://github.com/opencv/opencv-python)
- [Vosk](https://github.com/alphacep/vosk-api)
- [PyAutoGUI](https://github.com/asweigart/pyautogui)
- [sounddevice](https://github.com/spatialaudio/python-sounddevice)
- [pycaw](https://github.com/AndreMiras/pycaw)

---

## Notes

- The system was built and tested on Windows. pycaw is a Windows-only library and the system will not run on macOS or Linux without modification.
- Lighting and background can affect hand tracking performance. A plain background and decent lighting help.
- The voice pipeline uses a constrained keyword set. It will ignore speech that does not match a command.

---

## License

MIT License. See `LICENSE` for details.