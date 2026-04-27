import csv
from datetime import datetime
from collections import defaultdict
from statistics import mean
from pathlib import Path

import matplotlib.pyplot as plt


# -----------------------------
# Input / output files
# -----------------------------
LOG_FILE = Path("aircommand_log.csv")

FIGURE_OUT = Path("figure4_latency_by_command.png")
TABLE_OUT = Path("table6_latency_by_command.csv")


# -----------------------------
# Latency calculation setup
# -----------------------------
TIME_FMT = "%Y-%m-%d %H:%M:%S.%f"

voice_pending = {}
hand_pending = {}
latencies = defaultdict(list)


# -----------------------------
# Read log and calculate latency
# -----------------------------
with open(LOG_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        ts = datetime.strptime(row["timestamp"], TIME_FMT)
        source = row["source"]
        event_type = row["event_type"]
        detail = row["detail"]

        # Voice: command_recognized -> action
        if source == "voice":
            if event_type == "command_recognized":
                voice_pending[detail] = ts

            elif event_type == "action":
                if detail == "click" and "click" in voice_pending:
                    latencies["voice_click"].append(
                        (ts - voice_pending.pop("click")).total_seconds() * 1000
                    )

                elif detail == "copy" and "copy" in voice_pending:
                    latencies["voice_copy"].append(
                        (ts - voice_pending.pop("copy")).total_seconds() * 1000
                    )

                elif detail == "paste" and "paste" in voice_pending:
                    latencies["voice_paste"].append(
                        (ts - voice_pending.pop("paste")).total_seconds() * 1000
                    )

                elif detail == "select_start" and "select" in voice_pending:
                    latencies["voice_select"].append(
                        (ts - voice_pending.pop("select")).total_seconds() * 1000
                    )

                elif detail == "select_stop" and "stop" in voice_pending:
                    latencies["voice_stop"].append(
                        (ts - voice_pending.pop("stop")).total_seconds() * 1000
                    )

                elif detail == "drag_start" and "drag" in voice_pending:
                    latencies["voice_drag"].append(
                        (ts - voice_pending.pop("drag")).total_seconds() * 1000
                    )

                elif detail == "type_command" and "type" in voice_pending:
                    latencies["voice_type_done"].append(
                        (ts - voice_pending.pop("type")).total_seconds() * 1000
                    )

        # Hand: gesture_recognized -> action
        elif source == "hand":
            if event_type == "gesture_recognized":
                hand_pending[detail] = ts

            elif event_type == "action" and detail in hand_pending:
                latencies[f"hand_{detail}"].append(
                    (ts - hand_pending.pop(detail)).total_seconds() * 1000
                )


# -----------------------------
# Display order
# -----------------------------
order = [
    ("hand_click", "Hand", "Click"),
    ("hand_scroll_up_start", "Hand", "Scroll Up"),
    ("hand_scroll_down_start", "Hand", "Scroll Down"),
    ("hand_flick_left_tab_switch", "Hand", "Flick Left / Tab Switch"),
    ("hand_volume_up", "Hand", "Volume Up"),
    ("hand_volume_down", "Hand", "Volume Down"),
    ("hand_zoom_in", "Hand", "Zoom In"),
    ("hand_zoom_out", "Hand", "Zoom Out"),
    ("voice_click", "Voice", "Click"),
    ("voice_drag", "Voice", "Drag"),
    ("voice_select", "Voice", "Select"),
    ("voice_stop", "Voice", "Stop"),
    ("voice_copy", "Voice", "Copy"),
    ("voice_paste", "Voice", "Paste"),
    ("voice_type_done", "Voice", "Type ... Done"),
]


# -----------------------------
# Build latency rows
# -----------------------------
rows = []

for key, modality, command in order:
    values = latencies.get(key, [])

    if values:
        rows.append(
            {
                "modality": modality,
                "command": command,
                "n": len(values),
                "avg": round(mean(values), 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "label": f"{modality} - {command}",
            }
        )

if not rows:
    raise ValueError("No latency values were found. Check that aircommand_log.csv is in the same folder.")


# -----------------------------
# Save Table 6 as CSV
# -----------------------------
with open(TABLE_OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Modality", "Command", "N", "Average Latency (ms)", "Min (ms)", "Max (ms)"])

    for row in rows:
        writer.writerow([
            row["modality"],
            row["command"],
            row["n"],
            row["avg"],
            row["min"],
            row["max"],
        ])


# -----------------------------
# Create Figure 4
# -----------------------------
labels = [row["label"] for row in rows]
avg_latencies = [row["avg"] for row in rows]

plt.figure(figsize=(13, 7))
plt.bar(labels, avg_latencies)

plt.title("Figure 4. Average Software Dispatch Latency by Command")
plt.xlabel("Command")
plt.ylabel("Average Software Dispatch Latency (ms)")
plt.xticks(rotation=55, ha="right")

plt.tight_layout()
plt.savefig(FIGURE_OUT, dpi=300, bbox_inches="tight")
plt.show()


# -----------------------------
# Console output
# -----------------------------
print(f"Saved figure: {FIGURE_OUT}")
print(f"Saved table: {TABLE_OUT}")
print()

print("Table 6. Latency by Command")
print("-" * 85)
print(f"{'Modality':<10} {'Command':<28} {'N':<5} {'Avg (ms)':<10} {'Min (ms)':<10} {'Max (ms)':<10}")
print("-" * 85)

for row in rows:
    print(
        f"{row['modality']:<10} "
        f"{row['command']:<28} "
        f"{row['n']:<5} "
        f"{row['avg']:<10} "
        f"{row['min']:<10} "
        f"{row['max']:<10}"
    )