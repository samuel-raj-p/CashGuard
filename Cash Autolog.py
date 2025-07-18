# CashGuard | Computer vision (Auto-log version)
from datetime import datetime
import sqlite3 as sql, pandas as pd, mediapipe as mp, cv2 as cv, threading, keyboard as kb, pygame as pg

db_path = "cashguard_logs.db"
conn = sql.connect(db_path)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    person TEXT
)
""")
conn.commit()

def play_alarm():
    pg.mixer.init()
    pg.mixer.music.load("C:/Users/Samuel Raj/Downloads/alarm.mp3")
    pg.mixer.music.play(-1)

def capture_photo():
    global photo_captured
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    photo_path = f"C:/Users/Samuel Raj/Downloads/alert_face_{now}.jpg"
    cv.imwrite(photo_path, frame)
    print(f"📸 Thiruttu paya maatikittan, saved at: {photo_path}")
    photo_captured = True

def password():
    global alarm_playing
    typed = ""
    while alarm_playing:
        event = kb.read_event()
        if event.event_type == 'down': typed += event.name.lower()
        if 'fred' in typed:
            print("🔐Password 'FRED' entered. Alarm stopped!")
            alarm_playing = False
            pg.mixer.music.stop(); break
          
def monitor():
    global cashier_box, alarm_playing, photo_captured, hand_logged, cap
    hand_logged, alarm_playing, photo_captured = False, False, False
    cap = cv.VideoCapture(0)
    if not cap.isOpened(): print("💥 Camera error."); return
    print("🎬 Monitoring started. Press 'q' to stop...")

    while True:
        ret, frame = cap.read()
        if not ret: break

        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        frame = cv.cvtColor(gray, cv.COLOR_GRAY2BGR)
        face_result = face_detection.process(frame)
        person, face_detected = "Unknown", False

        if face_result.detections:
            face_detected = True
            box = face_result.detections[0].location_data.relative_bounding_box
            def similar(f1, f2, tol=0.1): return all(abs(getattr(f1, attr) - getattr(f2, attr)) < tol for attr in ['xmin', 'ymin', 'width', 'height'])
            person = "Cashier" if similar(box, cashier_box) else "Unknown"
            mp_draw.draw_detection(frame, face_result.detections[0])

        if person == "Unknown": cv.putText(frame, "!!! ALERT: Unknown Face Detected !!!", (20, 100), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        cv.rectangle(frame, (cash_box[0], cash_box[1]), (cash_box[2], cash_box[3]), (0, 255, 0), 2)
        results = hands.process(frame)

        if results.multi_hand_landmarks:
            for hand_landmark in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmark, mp_hands.HAND_CONNECTIONS)
                for lm in hand_landmark.landmark:
                    h, w = frame.shape[:2]
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    in_box = cash_box[0] < cx < cash_box[2] and cash_box[1] < cy < cash_box[3]

                    if in_box and not hand_logged:
                        hand_logged = True
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        entry_person = person if face_detected else "Alert"

                        if has_access("write"): insert_log(timestamp, entry_person)
                        print(f"✅ [{timestamp}] - {entry_person} touched cash box")
                        cv.circle(frame, (cx, cy), 10, (0, 0, 255), -1)

                        if entry_person == "Alert" and not alarm_playing:
                            alarm_playing, photo_captured = True, False
                            threading.Thread(target=play_alarm, daemon=True).start()
                            threading.Thread(target=capture_photo, daemon=True).start()
                            threading.Thread(target=password, daemon=True).start()

                        elif entry_person == "Unknown" and not photo_captured:
                            photo_captured = False
                            threading.Thread(target=capture_photo, daemon=True).start()

                    elif not in_box: hand_logged = False

        cv.putText(frame, f"Person: {person}", (20, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv.imshow("CashGuard | Computer Vision @samuel-raj-p", frame)
        key = cv.waitKey(1) & 0xFF
        if key == ord('q') and not alarm_playing: break
        elif key == ord('q') and alarm_playing: print("🔒 Alarm ringing! Enter password to quit.")

    cap.release(); cv.destroyAllWindows(); print("📷 Camera off paniyachu venumna 'restart' panu.")

access_keys = { "VIEWER": "can_read", "EDITOR": "can_read_write"}; activated = "EDITOR" 
def has_access(action): return access_keys[activated] == "can_read_write" or (action == "read" and access_keys[activated])
def insert_log(timestamp, person):
    cursor.execute("SELECT timestamp FROM logs ORDER BY id DESC LIMIT 1")
    last = cursor.fetchone()
    if last:
        last_time = datetime.strptime(last[0], "%Y-%m-%d %H:%M:%S")
        curr_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        if (curr_time - last_time).seconds == 1: return  
    cursor.execute("INSERT INTO logs (timestamp, person) VALUES (?, ?)", (timestamp, person))
    conn.commit()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_face = mp.solutions.face_detection
face_detection = mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.6)
mp_draw = mp.solutions.drawing_utils

cap = cv.VideoCapture(0)
if not cap.isOpened(): print("Camera vey ila, aprm epdi?"); exit()
cashier_box = None
hand_logged, alarm_playing, photo_captured = False, False, False
cash_box = (200, 340, 400, 480)
print("📸 Unga thiru mugutha oru thadava kaatungo !"); monitor()

while True:
  
    choice = input("💾 Wanna save current logs as CSV? (yes/no) or enter 'restart' to work again: ").lower()
    if choice == 'yes':
        df = pd.read_sql("SELECT * FROM logs", conn)
        df.drop_duplicates(subset=["timestamp", "person"], keep="first", inplace=True)
        df.drop(columns=["id"], inplace=True, errors="ignore")
        df.insert(0, "S.No", range(1, len(df) + 1))
        today = datetime.now().strftime("%Y-%m-%d")
        df.to_csv(f"C:/Users/Samuel Raj/Downloads/cashguard_log_{today}.csv", index=False)
        print("✅ Exported [CSV]"); break
    elif choice == 'no': print("❌ You choose not to save logs as CSV."); break
    elif choice == 'restart': print("🔁 Restarting camera and monitoring..."); monitor()
    else: print("🤔 Invalid choice. Please type yes / no / restart.")
