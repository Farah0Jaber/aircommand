import threading
import time
from speech_commands import start_voice_listener, stop_event
from hand_tracking import run_hand_tracking

# Start voice recognition in background
voice_thread = threading.Thread(target=start_voice_listener)
voice_thread.daemon = True
voice_thread.start()

# Run hand tracking in main thread (OpenCV needs it)
run_hand_tracking()

# Keep program alive after gesture control exits (optional)
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    stop_event.set()
    print("👋 Exiting.")
