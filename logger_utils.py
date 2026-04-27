import csv
import os
from datetime import datetime
from threading import Lock

LOG_FILE = "aircommand_log.csv"
_log_lock = Lock()

def init_log():
    file_exists = os.path.exists(LOG_FILE)
    if not file_exists:
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "source", "event_type", "detail", "value"])

def log_event(source, event_type, detail, value=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with _log_lock:
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, source, event_type, detail, value])