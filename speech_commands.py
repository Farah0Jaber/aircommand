from vosk import Model, KaldiRecognizer
import sounddevice as sd
import pyautogui
import json
import time
import re
from threading import Event

# Load Vosk model
model = Model("model")  # Replace with your model folder if different
rec = KaldiRecognizer(model, 16000)
stop_event = Event()  # For graceful shutdown

# Flag to track selection state
selecting = False

def callback(indata, frames, time_info, status):
    global selecting
    if status:
        print("Mic status:", status)
    if rec.AcceptWaveform(bytes(indata)):
        result = json.loads(rec.Result())
        text = result.get("text", "").lower()
        print("You said:", text)

        if "type" in text and "done" in text:
            try:
                match = re.search(r"type[: ]+(.*?)done", text)
                if match:
                    typed = match.group(1).strip()
                    print(f"⌨ Typing: {typed}")
                    time.sleep(0.3)
                    pyautogui.click()
                    time.sleep(0.2)
                    pyautogui.write(typed)
                    pyautogui.press('enter')
                else:
                    print("❌ No valid text to type found.")
            except Exception as e:
                print("❌ Could not parse type command:", e)

        elif "click" in text:
            print("🖱 Click triggered")
            pyautogui.click()

        elif "drag" in text:
            print("👉 Dragging for 2 seconds...")
            pyautogui.mouseDown()
            time.sleep(2)
            pyautogui.mouseUp()
            print("✅ Drag released.")

        elif "select" in text:
            print("✏️ Select started")
            pyautogui.mouseDown()
            selecting = True

        elif "stop" in text:
            if selecting:
                pyautogui.mouseUp()
                selecting = False
                print("🛑 Selection stopped")

        elif "copy" in text:
            print("📋 Copying")
            pyautogui.hotkey('ctrl', 'c')

        elif "paste" in text:
            print("📄 Pasting")
            pyautogui.hotkey('ctrl', 'v')

def start_voice_listener():
    print("🎤 Say 'click', 'drag', 'select', 'stop', 'copy', 'paste', or 'type ... done'")
    with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype='int16',
                           channels=1, callback=callback):
        while not stop_event.is_set():
            time.sleep(0.1)
