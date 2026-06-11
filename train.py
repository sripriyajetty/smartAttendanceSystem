import cv2
import os
import numpy as np

print("Training faces...")

path = 'dataset'
recognizer = cv2.face.LBPHFaceRecognizer_create()

faces = []
ids = []

for image in os.listdir(path):
    img_path = os.path.join(path, image)
    gray_img = cv2.imread(img_path, 0)

    # ✅ ADDED (avoid crash)
    if gray_img is None:
        continue

    id = int(image.split('.')[1])

    faces.append(gray_img)
    ids.append(id)

recognizer.train(faces, np.array(ids))

if not os.path.exists("trainer"):
    os.makedirs("trainer")

recognizer.save('trainer/trainer.yml')

print("Training completed successfully")