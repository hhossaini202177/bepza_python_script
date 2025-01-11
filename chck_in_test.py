import base64
import os
from datetime import datetime

import cv2
import numpy as np
import requests
import yaml
from dotenv import load_dotenv
from kafka import KafkaProducer
from kafka.errors import KafkaError

from detect import detect_license_plate
from ocr import easyocr_ocr, tesseract_ocr
from preprocess import save_image

# Load environment variables
load_dotenv()

# Extract credentials from the .env file
RTSP_USERNAME = os.getenv("RTSP_USERNAME")
RTSP_PASSWORD = os.getenv("RTSP_PASSWORD")
RTSP_IP = os.getenv("RTSP_IP")

# Load RTSP URL template from YAML
with open("config.yml", "r") as file:
    config = yaml.safe_load(file)

rtsp_url_template = config["rtsp"]["url_template"]
rtsp_url = rtsp_url_template.format(username=RTSP_USERNAME, password=RTSP_PASSWORD, ip=RTSP_IP)

# Kafka Configuration
KAFKA_BROKER = "192.169.20.20:9092"
KAFKA_TOPIC = "license_plate_topic"

# Initialize Kafka producer with error handling
try:
    producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
except KafkaError as e:
    print(f"Failed to initialize Kafka producer: {e}")
    producer = None

def main(font_path):
    try:
        # Open video stream from RTSP URL
        cap = cv2.VideoCapture(rtsp_url)
        if not cap.isOpened():
            raise ValueError("Failed to open RTSP stream.")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("No frame captured. Exiting...")
                break

            # Process the frame to detect the license plate
            detected_plate, detected_image = detect_license_plate(frame)
            if detected_plate is None:
                print("License plate not detected.")
                # continue
                break

            # Perform OCR on the detected license plate
            easyocr_text = easyocr_ocr(detected_plate)
            tesseract_text = tesseract_ocr(detected_plate)

            # Extract text from OCR results
            easyocr_result = " ".join([item[1] for item in easyocr_text]) if easyocr_text else ""
            tesseract_result = tesseract_text.strip()
            detected_text = f"{easyocr_result} {tesseract_result}".strip()

            # Save the cropped image and resize it for Base64 conversion
            cropped_filename = save_image(detected_plate, "cropped_license_plates")

            # Encode the detected frame (annotated image) to Base64
            _, jpeg = cv2.imencode(".jpg", detected_image)
            base64_annotated_image = base64.b64encode(jpeg).decode("utf-8")

            # Post API Message
            current_time = datetime.now()
            current_time_ms = int(current_time.timestamp() * 1000)
            post_message = {
                "dateTime": current_time_ms,
                "licensePlateNumber": detected_text,
                "gateId": 1,
                "entryType": "IN",
                "token": "Asuff87-=!",  # Include the required token
                "imagePath": cropped_filename  # Include file path
            }
            url = "http://192.169.20.20:8082/api/entry-exit"
            response = requests.post(url, json=post_message)

            # Print API response
            if response.status_code == 200:
                print("Check-in message successfully sent to API.")
            else:
                print(f"API request failed: {response.status_code}, {response.text}")

            # Kafka Message (Base64 encoded image from real-time frame)
            kafka_message = base64_annotated_image.encode("utf-8")
            if producer:
                producer.send(KAFKA_TOPIC, value=kafka_message)
                print("Real-time frame sent to Kafka.")
            break

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if "cap" in locals():
            cap.release()

if __name__ == "__main__":
    font_path = "./bangla-text/SolaimanLipi.ttf"  # Replace with the actual path to your font file
    main(font_path)
