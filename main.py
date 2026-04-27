import threading
import time
from speech_commands import start_voice_listener, stop_event
from hand_tracking import run_hand_tracking
from logger_utils import init_log, log_event

init_log()
log_event("system", "startup", "AirCommand started")
log_event("test", "session_start", "pilot_eval_fixed_conditions")
log_event("test", "condition", "room_setup", "same_room_same_light_same_camera_same_mic")

# Start voice recognition in background
voice_thread = threading.Thread(target=start_voice_listener)
voice_thread.daemon = True
voice_thread.start()
log_event("system", "thread_start", "Voice listener thread started")

# Run hand tracking in main thread (OpenCV needs it)
run_hand_tracking()
log_event("system", "hand_tracking_end", "Hand tracking loop exited")
log_event("test", "session_end", "pilot_eval_fixed_conditions")

# Keep program alive after gesture control exits (optional)
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    stop_event.set()
    log_event("system", "shutdown", "KeyboardInterrupt received")
    log_event("test", "session_end", "pilot_eval_fixed_conditions")
    print("👋 Exiting.")