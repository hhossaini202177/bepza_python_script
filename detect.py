import os

import cv2
from ultralytics import YOLO

# Load YOLOv8 model
# model = YOLO('./weight-file/ best.pt')
# Define the relative path to the weights file
WEIGHT_FILE = os.path.join("weight-file", "best.pt")

# Check if the file exists
if not os.path.exists(WEIGHT_FILE):
    raise FileNotFoundError(f"Weight file not found at '{WEIGHT_FILE}'. Please ensure the file exists.")

# Load YOLOv8 model
model = YOLO(WEIGHT_FILE)

def detect_license_plate(image):
    try:
        results = model(image)
        for result in results[0].boxes.data:
            x1, y1, x2, y2, conf, cls = result.tolist()
            if int(cls) == 0:  # Assuming class '0' is license plate
                x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
                cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cropped_plate = image[y1:y2, x1:x2]
                return cropped_plate, image
        return None, image
    except Exception as e:
        print(f"An error occurred in detect.py: {e}")
        return None, image
