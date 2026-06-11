import cv2
import time
import os

print("Starting Attendance System...")

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')

faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

font = cv2.FONT_HERSHEY_SIMPLEX

# ✅ CHANGED (better name handling)
names = {}
if os.path.exists("names.txt"):
    with open("names.txt", "r") as f:
        for line in f:
            id, name = line.strip().split(',')
            names[int(id)] = name

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cam.set(3, 640)
cam.set(4, 480)

if not cam.isOpened():
    print("Camera not working")
    exit()

time.sleep(2)

if not os.path.exists("attendance.csv"):
    with open("attendance.csv", "w") as f:
        f.write("Name,Time\n")

marked_names = set()
stop_flag = False
message = ""

while True:
    ret, img = cam.read()

    if not ret:
        print("Camera error")
        break

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    # ✅ CHANGED (more stable detection)
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(100,100)
    )

    if len(faces) == 0:
        message = "No Face Detected"

    for (x,y,w,h) in faces:
        cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)

        id, confidence = recognizer.predict(gray[y:y+h,x:x+w])

        print("Confidence:", confidence)
        print("ID:", id)

        # ✅ CHANGED (better threshold)
        if confidence < 80:
            name = names.get(id, "Unknown")

            if name != "Unknown":
                time_now = time.ctime()

                if name not in marked_names:
                    with open("attendance.csv", "a") as f:
                        f.write(f"{name},{time_now}\n")

                    marked_names.add(name)
                    message = f"Attendance Marked: {name}"
                    stop_flag = True
                else:
                    message = f"Already Marked: {name}"
                    stop_flag = True
            else:
                message = "Not Registered"
                stop_flag = True

        else:
            name = "Unknown"
            message = "Face Not Recognized"
            stop_flag = True

        cv2.putText(img, name, (x,y-10), font, 1, (255,255,255), 2)

    cv2.putText(img, message, (10,30), font, 0.8, (0,255,0), 2)

    cv2.imshow('Attendance System', img)

    if stop_flag:
        print(message)
        time.sleep(2)
        break

    if cv2.waitKey(1) == 27:
        break

cam.release()
cv2.destroyAllWindows()