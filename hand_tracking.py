import cv2
import mediapipe as mp
import pyautogui
import math
import time
import threading
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from logger_utils import log_event

def is_handshake_pose(lm):
    return abs(lm[0].x - lm[5].x) < 0.1

def fingers_flicked_left(prev_pos, curr_pos):
    return all(curr[0] < prev[0] - 0.05 for prev, curr in zip(prev_pos, curr_pos))

def run_hand_tracking():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume_ctrl = cast(interface, POINTER(IAudioEndpointVolume))

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, max_num_hands=2)

    cv2.setUseOptimized(True)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    screen_w, screen_h = pyautogui.size()
    prev_x, prev_y = 0, 0
    scroll_mode = None
    scroll_thread = None
    stop_scroll = threading.Event()
    zoom_state = "idle"
    zoom_triggered = False
    zoom_start_distance = None

    volume_mode = None
    volume_start_distance = None
    last_volume_time = 0
    volume_cooldown = 0.3

    flick_ready = False
    prev_finger_positions = []
    flick_last_time = 0
    flick_cooldown = 0.6

    click_ready = True
    
    def scroll_loop(direction):
        nonlocal stop_scroll
        while not stop_scroll.is_set():
            pyautogui.scroll(direction)
            time.sleep(0.002)
            
    def start_scrolling(direction):
        nonlocal scroll_thread, stop_scroll
        if scroll_thread is not None and scroll_thread.is_alive():
            return
        stop_scroll.clear()
        scroll_thread = threading.Thread(target=scroll_loop, args=(direction,), daemon=True)
        scroll_thread.start()
        
    def stop_scrolling():
        nonlocal stop_scroll, scroll_thread
        stop_scroll.set()
        if scroll_thread is not None and scroll_thread.is_alive():
            scroll_thread.join(timeout=0.1)
        scroll_thread = None
        
    def is_index_only_up(landmarks):
        lm = landmarks.landmark
        return (
            lm[8].y < lm[6].y and
            lm[12].y > lm[10].y and
            lm[16].y > lm[14].y and
            lm[20].y > lm[18].y and
            lm[4].y > lm[6].y
        )

    def is_hand_open(landmarks):
        lm = landmarks.landmark
        return (
            lm[4].x < lm[3].x and
            lm[8].y < lm[6].y and
            lm[12].y < lm[10].y and
            lm[16].y < lm[14].y and
            lm[20].y < lm[18].y
        )

    def get_thumb_index_distance(landmarks, w, h):
        x1, y1 = int(landmarks.landmark[4].x * w), int(landmarks.landmark[4].y * h)
        x2, y2 = int(landmarks.landmark[8].x * w), int(landmarks.landmark[8].y * h)
        return math.hypot(x2 - x1, y2 - y1)

    frame_skip = 2
    frame_count = 0

    while True:
        success, img = cap.read()
        if not success:
            break
        frame_count += 1
        if frame_count % frame_skip != 0:
            continue

        img = cv2.flip(img, 1)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = hands.process(img_rgb)
        h, w, _ = img.shape

        gesture_detected = False
        hand_data = result.multi_hand_landmarks

        if hand_data:
            hand_count = len(hand_data)

            # === Flick Left Detection (only after handshake pose) ===
            if hand_count == 1:
                lm = hand_data[0].landmark
                if is_handshake_pose(lm) and not flick_ready:
                    flick_ready = True
                    prev_finger_positions = []
                    
                if flick_ready:
                    fingertip_ids = [8, 12, 16, 20]
                    curr_finger_positions = [(lm[i].x, lm[i].y) for i in fingertip_ids]

                    if prev_finger_positions:
                        current_time = time.time()
                        if current_time - flick_last_time > flick_cooldown:
                            if fingers_flicked_left(prev_finger_positions, curr_finger_positions):
                                log_event("hand", "gesture_recognized", "flick_left_tab_switch")
                                pyautogui.hotkey('ctrl', 'shift', 'tab')
                                log_event("hand", "action", "flick_left_tab_switch")
                                flick_ready = False
                                prev_finger_positions = []
                                flick_last_time = current_time
                                                                                                
                    prev_finger_positions = curr_finger_positions

            if hand_count == 1:
                hand_landmarks = hand_data[0]
                lm = hand_landmarks.landmark

                fingers_up = {
                    "thumb": lm[4].x < lm[3].x,
                    "index": lm[8].y < lm[6].y,
                    "middle": lm[12].y < lm[10].y,
                    "ring": lm[16].y < lm[14].y,
                    "pinky": lm[20].y < lm[18].y
                }

                volume_pose = (
                    fingers_up["index"] and
                    not fingers_up["middle"] and
                    not fingers_up["ring"] and
                    not fingers_up["pinky"]
                )

                if volume_pose:
                    dist = get_thumb_index_distance(hand_landmarks, w, h)

                    if volume_start_distance is None:
                        volume_start_distance = dist
                        volume_mode = "idle"
                    else:
                        delta = dist - volume_start_distance
                        current_time = time.time()
                        if delta > 30 and current_time - last_volume_time > volume_cooldown:
                            log_event("hand", "gesture_recognized", "volume_up", round(delta, 2))
                            pyautogui.press('volumeup')
                            log_event("hand", "action", "volume_up", round(delta, 2))
                            volume_mode = "up"
                            last_volume_time = current_time
                        elif delta < -30 and current_time - last_volume_time > volume_cooldown:
                            log_event("hand", "gesture_recognized", "volume_down", round(delta, 2))
                            pyautogui.press('volumedown')
                            log_event("hand", "action", "volume_down", round(delta, 2))
                            volume_mode = "down"
                            last_volume_time = current_time
                else:
                    volume_mode = None
                    volume_start_distance = None
            else:
                volume_mode = None
                volume_start_distance = None
                                
            if hand_count != 1:
                flick_ready = False
                prev_finger_positions = []
           
            if hand_count == 2:
                lm1 = hand_data[0]
                lm2 = hand_data[1]
                x1, y1 = int(lm1.landmark[8].x * w), int(lm1.landmark[8].y * h)
                x2, y2 = int(lm2.landmark[8].x * w), int(lm2.landmark[8].y * h)
                distance = math.hypot(x2 - x1, y2 - y1)

                if is_hand_open(lm1) and is_hand_open(lm2):
                    zoom_state = "idle"
                    zoom_triggered = False
                    zoom_start_distance = None
                    continue

                if is_index_only_up(lm1) and is_index_only_up(lm2):
                    if zoom_start_distance is None:
                        zoom_start_distance = distance
                        zoom_triggered = False
                    else:
                        delta = distance - zoom_start_distance
                        if delta > 40 and not zoom_triggered:
                            log_event("hand", "gesture_recognized", "zoom_in", round(delta, 2))
                            pyautogui.hotkey('ctrl', '+')
                            log_event("hand", "action", "zoom_in", round(delta, 2))
                            zoom_triggered = True
                            zoom_state = "in"
                        elif delta < -40 and not zoom_triggered:
                            log_event("hand", "gesture_recognized", "zoom_out", round(delta, 2))
                            pyautogui.hotkey('ctrl', '-')
                            log_event("hand", "action", "zoom_out", round(delta, 2))
                            zoom_triggered = True
                            zoom_state = "out"
                else:
                    zoom_start_distance = None
                    zoom_triggered = False

                cv2.circle(img, (x1, y1), 10, (255, 0, 255), -1)
                cv2.circle(img, (x2, y2), 10, (0, 255, 255), -1)

            elif hand_count == 1 and volume_mode is None:
                lm = hand_data[0].landmark
                ix, iy = int(lm[8].x * w), int(lm[8].y * h)
                mx, my = int(lm[12].x * w), int(lm[12].y * h)

                if prev_x == 0 and prev_y == 0:
                    prev_x, prev_y = ix, iy

                dx, dy = ix - prev_x, iy - prev_y
                distance = math.hypot(dx, dy)
                smoothing = max(0.1, min(0.45, distance * 0.015))
                if distance > 1:
                    smooth_x = int(prev_x + dx * smoothing)
                    smooth_y = int(prev_y + dy * smoothing)
                    screen_x = int(smooth_x * screen_w / w)
                    screen_y = int(smooth_y * screen_h / h)
                    pyautogui.moveTo(screen_x, screen_y)
                    prev_x, prev_y = smooth_x, smooth_y

                finger_dist = math.hypot(ix - mx, iy - my)
                fingers_up = {
                    "thumb": lm[4].x < lm[3].x,
                    "index": lm[8].y < lm[6].y,
                    "middle": lm[12].y < lm[10].y,
                    "ring": lm[16].y < lm[14].y,
                    "pinky": lm[20].y < lm[18].y
                }

                thumb_tip = lm[4]
                index_base = lm[5]

                thumb_to_index_base = math.hypot(
                    (thumb_tip.x - index_base.x) * w,
                    (thumb_tip.y - index_base.y) * h
                )

                click_pose = (
                    fingers_up["index"] and fingers_up["middle"] and fingers_up["ring"] and fingers_up["pinky"]
                    and thumb_tip.y > index_base.y
                    and thumb_to_index_base < 45
                )

                if click_pose and click_ready:
                    log_event("hand", "gesture_recognized", "click")
                    pyautogui.click()
                    log_event("hand", "action", "click")
                    click_ready = False
                elif not click_pose:
                    click_ready = True
                if (finger_dist < 25 and
                    fingers_up["index"] and fingers_up["middle"] and
                    not fingers_up["ring"] and not fingers_up["pinky"] and
                    lm[8].y < lm[6].y and lm[12].y < lm[10].y):
                    gesture_detected = True
                    if scroll_mode != "up":
                        log_event("hand", "gesture_recognized", "scroll_up_start")
                        stop_scrolling()
                        start_scrolling(40)
                        log_event("hand", "action", "scroll_up_start")
                        scroll_mode = "up"
                                                                        
                elif (finger_dist < 25 and
                      not fingers_up["ring"] and not fingers_up["pinky"] and
                      lm[8].z < lm[6].z and lm[12].z < lm[10].z):
                    gesture_detected = True
                    if scroll_mode != "down":
                        log_event("hand", "gesture_recognized", "scroll_down_start")
                        stop_scrolling()
                        start_scrolling(-40)
                        log_event("hand", "action", "scroll_down_start")
                        scroll_mode = "down"
                                                                        
                cv2.circle(img, (ix, iy), 10, (0, 255, 0), -1)
                cv2.circle(img, (mx, my), 10, (255, 255, 0), -1)

        if not hand_data:
            if scroll_mode is not None:
                stop_scrolling()
                log_event("hand", "action", "scroll_stop")
                scroll_mode = None
                
            volume_mode = None
            volume_start_distance = None
            zoom_state = "idle"
            zoom_triggered = False
            zoom_start_distance = None
            flick_ready = False
            prev_finger_positions = []
            click_ready = True

        elif not gesture_detected and scroll_mode is not None:
            stop_scrolling()
            log_event("hand", "action", "scroll_stop")
            scroll_mode = None
            
        cv2.imshow("Hand Control System", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            log_event("system", "shutdown", "q_pressed_in_hand_window")
            break
        
    stop_scrolling()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_hand_tracking()
