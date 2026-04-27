from vosk import Model, KaldiRecognizer
import sounddevice as sd
import pyautogui
import json
import time
import re
from threading import Event
from logger_utils import log_event

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
        text = result.get("text", "").lower().strip()

        if not text:
            return

        print("You said:", text)
        
        if "type" in text and "done" in text:
            log_event("voice", "command_recognized", "type", text)
            try:
                match = re.search(r"type[: ]+(.*?)done", text)
                if match:
                    typed = match.group(1).strip()
                    if typed:
                        print(f"⌨ Typing: {typed}")
                        log_event("voice", "action", "type_command", typed)
                        time.sleep(0.3)
                        pyautogui.click()
                        time.sleep(0.2)
                        pyautogui.write(typed)
                        pyautogui.press('enter')
                    else:
                        print("❌ Type command was empty.")
                        log_event("voice", "error", "type_command_empty", text)
                else:
                    print("❌ No valid text to type found.")
                    log_event("voice", "error", "type_command_parse_failed", text)
            except Exception as e:
                print("❌ Could not parse type command:", e)
                log_event("voice", "error", "type_command_exception", str(e))
                                
        elif "click" in text:
            log_event("voice", "command_recognized", "click", text)
            print("🖱 Click triggered")
            log_event("voice", "action", "click")
            pyautogui.click()
                        
        elif "drag" in text:
            log_event("voice", "command_recognized", "drag", text)
            print("👉 Dragging for 2 seconds...")
            log_event("voice", "action", "drag_start")
            pyautogui.mouseDown()
            time.sleep(2)
            pyautogui.mouseUp()
            log_event("voice", "action", "drag_end")
            print("✅ Drag released.")
                        
        elif "select" in text:
            log_event("voice", "command_recognized", "select", text)
            print("✏️ Select started")
            log_event("voice", "action", "select_start")
            pyautogui.mouseDown()
            selecting = True
                        
        elif "stop" in text:
            log_event("voice", "command_recognized", "stop", text)
            if selecting:
                pyautogui.mouseUp()
                selecting = False
                log_event("voice", "action", "select_stop")
                print("🛑 Selection stopped")
            else:
                log_event("voice", "ignored", "stop_without_select")
                                
        elif "copy" in text:
            log_event("voice", "command_recognized", "copy", text)
            print("📋 Copying")
            log_event("voice", "action", "copy")
            pyautogui.hotkey('ctrl', 'c')
                        
        elif "paste" in text:
            log_event("voice", "command_recognized", "paste", text)
            print("📄 Pasting")
            log_event("voice", "action", "paste")
            pyautogui.hotkey('ctrl', 'v')
            
        else:
            log_event("voice", "command_ignored", "non_command_speech", text)
                        
def start_voice_listener():
    print("🎤 Say 'click', 'drag', 'select', 'stop', 'copy', 'paste', or 'type ... done'")
    log_event("voice", "listener_started", "voice listener active")
    with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype='int16',
                           channels=1, callback=callback):
        while not stop_event.is_set():
            time.sleep(0.1)
