import cv2
import os

print("Program started")

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

cam.set(3, 640)
cam.set(4, 480)

if not cam.isOpened():
    print("ERROR: Camera not working")
    exit()

face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

face_id = input("Enter ID: ")
name = input("Enter Name: ")

# ✅ ADDED (save name)
with open("names.txt", "a") as f:
    f.write(f"{face_id},{name}\n")

print("Capturing...")

count = 0

while True:
    ret, img = cam.read()

    if not ret:
        print("Camera failed")
        break

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # ✅ CHANGED (better detection)
    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=3,
        minSize=(100, 100)
    )

    for (x,y,w,h) in faces:
        count += 1

        if not os.path.exists("dataset"):
            os.makedirs("dataset")

        cv2.imwrite(f"dataset/User.{face_id}.{count}.jpg", gray[y:y+h,x:x+w])

        cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)

    cv2.imshow('Capture', img)

    # ✅ CHANGED (more images)
    if cv2.waitKey(1) == 27 or count >= 50:
        break

cam.release()
cv2.destroyAllWindows()

print("Captured:", count)