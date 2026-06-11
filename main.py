import tkinter as tk
from tkinter import ttk
import cv2
import os
import numpy as np
import time
from PIL import Image, ImageTk
from datetime import date
import serial

# ================= GLOBAL =================
CURRENT_DATE = str(date.today())
ATTENDANCE_FILE = f"attendance_{CURRENT_DATE}.csv"

cap = None
running = False

ser = None
is_connected = False

frame_names = []
STABILITY_COUNT = 10

# ================= UI =================
root = tk.Tk()
root.title("AI Attendance System")
root.geometry("950x520")
root.configure(bg="#121212")

# ---------- LEFT PANEL ----------
left = tk.Frame(root, width=260, bg="#1e1e2f")
left.pack(side="left", fill="y")

# ---------- RIGHT PANEL ----------
right = tk.Frame(root, bg="black")
right.pack(side="right", expand=True, fill="both")

video_label = tk.Label(right)
video_label.pack(expand=True)

# ================= INPUTS =================
tk.Label(left, text="ID", bg="#1e1e2f", fg="white").pack(pady=5)
entry_id = tk.Entry(left)
entry_id.pack()

tk.Label(left, text="Name", bg="#1e1e2f", fg="white").pack(pady=5)
entry_name = tk.Entry(left)
entry_name.pack()

tk.Label(left, text="COM Port", bg="#1e1e2f", fg="white").pack(pady=5)
com_port = ttk.Combobox(left, values=["COM1","COM2","COM3","COM4","COM5"])
com_port.pack()

# COM STATUS
com_status = tk.Label(left, text="Disconnected", bg="#1e1e2f", fg="red")
com_status.pack(pady=5)

tk.Label(left, text="Date", bg="#1e1e2f", fg="white").pack(pady=5)
date_entry = tk.Entry(left)
date_entry.insert(0, CURRENT_DATE)
date_entry.pack()

status = tk.Label(left, text="Status: Ready", bg="#1e1e2f", fg="yellow")
status.pack(pady=10)

def set_status(msg):
    status.config(text=f"Status: {msg}")
    root.update()

# ================= LOAD NAMES =================
def load_names():
    names = {}
    if os.path.exists("names.txt"):
        with open("names.txt", "r") as f:
            for line in f:
                id, name = line.strip().split(',')
                names[int(id)] = name
    return names

# ================= COM CONNECT =================
def connect_com():
    global ser, is_connected

    port = com_port.get()

    if not port:
        set_status("Select COM Port")
        return

    try:
        ser = serial.Serial(port, 9600, timeout=1)
        is_connected = True
        com_status.config(text=f"Connected: {port}", fg="green")
        set_status("COM Connected")
    except:
        is_connected = False
        com_status.config(text="Connection Failed", fg="red")
        set_status("COM Error")

# ================= CAMERA LOOP =================
def update_frame(recognize=False):
    global cap, running, frame_names

    if not running:
        return

    ret, frame = cap.read()
    if not ret:
        return

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(gray, 1.1, 4)

    detected_name = None

    for (x,y,w,h) in faces:
        id, conf = recognizer.predict(gray[y:y+h, x:x+w])

        if conf < 80:
            detected_name = names.get(id, "Unknown")
        else:
            detected_name = "Unknown"

        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
        cv2.putText(frame,
                f"{detected_name} ({round(conf,1)})",
                (x,y-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255,255,255),
                2)

    # ---------- STABILITY ----------
    if recognize and detected_name:
        frame_names.append(detected_name)

        if len(frame_names) > STABILITY_COUNT:
            frame_names.pop(0)

        if len(frame_names) == STABILITY_COUNT and len(set(frame_names)) == 1:
            stable_name = frame_names[0]

            if stable_name != "Unknown":
                mark_attendance(stable_name)
            else:
                set_status("Unknown Face")
                if is_connected:
                    ser.write("UNKNOWN\n".encode())

            frame_names.clear()

    # DISPLAY
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = ImageTk.PhotoImage(Image.fromarray(rgb))
    video_label.imgtk = img
    video_label.configure(image=img)

    video_label.after(10, lambda: update_frame(recognize))


# ================= CAPTURE =================
def capture():
    face_id = entry_id.get()
    name = entry_name.get()

    if not face_id or not name:
        set_status("Enter ID & Name")
        return

    with open("names.txt", "a") as f:
        f.write(f"{face_id},{name}\n")

    cam = cv2.VideoCapture(0)
    detector = cv2.CascadeClassifier(cv2.data.haarcascades +
                                     'haarcascade_frontalface_default.xml')

    count = 0
    set_status("Capturing...")

    while True:
        ret, img = cam.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        faces = detector.detectMultiScale(gray, 1.1, 3)

        for (x,y,w,h) in faces:
            count += 1

            if not os.path.exists("dataset"):
                os.makedirs("dataset")

            cv2.imwrite(f"dataset/User.{face_id}.{count}.jpg",
                        gray[y:y+h, x:x+w])

        cv2.imshow("Capture", img)

        if cv2.waitKey(1) == 27 or count >= 50:
            break

    cam.release()
    cv2.destroyAllWindows()

    set_status("Capture Done")


# ================= TRAIN =================
def train():
    path = 'dataset'
    faces = []
    ids = []

    for img in os.listdir(path):
        gray = cv2.imread(os.path.join(path, img), 0)
        if gray is None:
            continue

        id = int(img.split('.')[1])
        faces.append(gray)
        ids.append(id)

    recognizer.train(faces, np.array(ids))

    if not os.path.exists("trainer"):
        os.makedirs("trainer")

    recognizer.save("trainer/trainer.yml")
    set_status("Training Done")


# ================= ATTENDANCE =================
def mark_attendance(name):
    global ATTENDANCE_FILE

    selected_date = date_entry.get()
    ATTENDANCE_FILE = f"attendance_{selected_date}.csv"

    if not os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, "w") as f:
            f.write("Name,Time\n")

    with open(ATTENDANCE_FILE, "r") as f:
        data = f.read()

    if name in data:
        set_status(f"Already Marked: {name}")
        if is_connected:
            ser.write(f"ALREADY:{name}\n".encode())
    else:
        with open(ATTENDANCE_FILE, "a") as f:
            f.write(f"{name},{time.ctime()}\n")

        set_status(f"Marked: {name}")
        if is_connected:
            ser.write(f"MARKED:{name}\n".encode())


# ================= START RECOGNITION =================
def recognize():
    global cap, running, recognizer, faceCascade, names

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("trainer/trainer.yml")

    faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades +
                                        'haarcascade_frontalface_default.xml')

    names = load_names()
    

    cap = cv2.VideoCapture(0)
    running = True

    set_status("Recognizing...")
    update_frame(recognize=True)


# ================= STOP =================
def stop():
    global running, cap, ser, is_connected

    running = False

    if cap:
        cap.release()

    if ser and is_connected:
        ser.close()
        is_connected = False
        com_status.config(text="Disconnected", fg="red")

    set_status("Stopped")
def calculate_metrics():
    global TP, FP, TN, FN

    total = TP + FP + TN + FN

    if total == 0:
        set_status("No data for metrics")
        return

    accuracy = (TP + TN) / total

    precision = TP / (TP + FP) if (TP + FP) != 0 else 0
    recall = TP / (TP + FN) if (TP + FN) != 0 else 0

    if (precision + recall) == 0:
        f1 = 0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)

    msg = f"Acc:{accuracy:.2f}  Prec:{precision:.2f}  Rec:{recall:.2f}  F1:{f1:.2f}"

    set_status(msg)

# ================= BUTTONS =================
tk.Button(left, text="Capture", bg="#00bbf9", width=25, command=capture).pack(pady=5)
tk.Button(left, text="Train", bg="#fee440", width=25, command=train).pack(pady=5)
tk.Button(left, text="Recognize", bg="#9b5de5", width=25, command=recognize).pack(pady=5)

tk.Button(left, text="Connect COM", bg="#00f5d4", width=25, command=connect_com).pack(pady=5)
tk.Button(left, text="Stop Camera", bg="#f15bb5", width=25, command=stop).pack(pady=5)
tk.Button(left, text="Quit", bg="red", width=25, command=root.destroy).pack(pady=20)


# ================= INIT =================
recognizer = cv2.face.LBPHFaceRecognizer_create()
faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades +
                                    'haarcascade_frontalface_default.xml')
names = load_names()

root.mainloop()
