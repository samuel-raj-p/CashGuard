#CashGuard | Computer vision ('q' to Entry version)
from datetime import datetime
import os, pandas as pd, mediapipe as mp, cv2 as cv, threading, keyboard as kb, pygame as pg

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_face = mp.solutions.face_detection
face_detection = mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.6)
mp_draw = mp.solutions.drawing_utils

cap = cv.VideoCapture(0)
if not cap.isOpened(): print("Camera vey ila, aprm epdi?"); exit()

logs = []
cashier_box = None
hand_logged = False
alarm_playing = False
photo_captured = False
cash_box = (200, 340, 400, 480)
print("📸 Unga thiru mugutha oru thadava kaatungo !")

def play_alarm():
    pg.mixer.init()
    pg.mixer.music.load("C:/Users/Samuel Raj/Downloads/alarm.mp3")
    pg.mixer.music.play(-1)

def capture_photo():
    global photo_captured
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    photo_path = f"C:/Users/Samuel Raj/Downloads/alert_face_{now}.jpg"
    cv.imwrite(photo_path, frame)
    print(f"📸 Thiruttu paya maatikittan, face captured and saved at: {photo_path}")
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

while cashier_box is None:
    _, frame = cap.read()
    results = face_detection.process(cv.cvtColor(frame, cv.COLOR_BGR2RGB))
    if results.detections:
        cashier_box = results.detections[0].location_data.relative_bounding_box
        print("Cashier Photo capture over"); break
print("🎬 Starting monitoring now. Press 'q' to stop and save...")

while True:
    ret, frame = cap.read()
    if not ret: print("Frame read failed, exiting."); break

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    frame = cv.cvtColor(gray, cv.COLOR_GRAY2BGR)
    face_result = face_detection.process(frame)
    person = "Unknown"
    face_detected = False

    if face_result.detections:
        face_detected = True
        box = face_result.detections[0].location_data.relative_bounding_box

        def similar(face1, face2, tol=0.1): return all(abs(getattr(face1, attr) - getattr(face2, attr)) < tol for attr in ['xmin', 'ymin', 'width', 'height'])
        if similar(box, cashier_box): person = "Cashier"
        else: person = "Unknown"
        mp_draw.draw_detection(frame, face_result.detections[0])

    if person == "Unknown": cv.putText(frame, "!!! ALERT: Unknown Face Detected !!!", (20, 100), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
    cv.rectangle(frame, (cash_box[0], cash_box[1]), (cash_box[2], cash_box[3]), (0, 255, 0), 2)
    results = hands.process(frame)

    if results.multi_hand_landmarks:
        for hand_landmark in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmark, mp_hands.HAND_CONNECTIONS)
            for lm in hand_landmark.landmark:
                h, w, _ = frame.shape
                cx, cy = int(lm.x * w), int(lm.y * h)

                in_box = cash_box[0] < cx < cash_box[2] and cash_box[1] < cy < cash_box[3]
                if in_box and not hand_logged:
                    hand_logged = True
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    entry_person = person if face_detected else "Alert"
                    logs.append([timestamp, entry_person])
                    print(f"✅ [{timestamp}] - {entry_person} touched cash box")
                    cv.circle(frame, (cx, cy), 10, (0, 0, 255), -1)

                    if entry_person == "Alert" and not alarm_playing:
                        alarm_playing = True
                        photo_captured = False
                        threading.Thread(target=play_alarm, daemon=True).start()
                        threading.Thread(target=capture_photo, daemon=True).start()
                        threading.Thread(target=password, daemon=True).start()

                    elif entry_person == "Unknown" and not photo_captured:
                        photo_captured = False
                        threading.Thread(target=capture_photo, daemon=True).start()

                elif not in_box: hand_logged = False

    text = f"Person: {person}"
    (text_width, text_height), _ = cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, 1, 2)
    cv.rectangle(frame, (15, 20), (15 + text_width + 10, 60), (0, 0, 0), -1)
    cv.putText(frame, text, (20, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    cv.imshow("CashGuard | Computer Vision @samuel-raj-p", frame)
    if cv.waitKey(1) & 0xFF == ord('q'): break

def remove_cons(df):
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])    
    df['Sec'] = df['Timestamp'].dt.second    
    keep_rows = [0]
    for i in range(1, len(df)):
        if df['Sec'].iloc[i] != df['Sec'].iloc[i-1] + 1: keep_rows.append(i)
    cleaned_df = df.iloc[keep_rows].copy()
    cleaned_df.drop(columns='Sec', inplace=True) 
    return cleaned_df

today = datetime.now().strftime("%Y-%m-%d")
save_path = fr"C:/Users/Samuel Raj/Downloads/cashbox_log_{today}.csv"
new_df = pd.DataFrame(logs, columns=["Timestamp", "Person"])

if os.path.exists(save_path):
    try:
        print("📦 File exists. Merging with existing records...")
        old_df = pd.read_csv(save_path)
        combined = remove_cons(pd.concat([old_df, new_df]).drop_duplicates(subset=["Timestamp", "Person"], keep="first"))
        combined.to_csv(save_path, index=False); print(combined.tail())
        print("✅ Merged and saved successfully at:", save_path)
    except Exception as e: print("❌ Error during CSV merge:", e)
else:
    try:
        new_logs = remove_cons(new_df.drop_duplicates(subset=["Timestamp", "Person"], keep="first"))
        new_logs.to_csv(save_path, index=False); print(new_logs.tail())
        print("✅ New file saved at:", save_path)
    except Exception as e: print("❌ Error saving new CSV:", e)

cap.release(); print("📷 Camera closed.")
cv.destroyAllWindows(); print("👋 Meendum Santhippom.")
