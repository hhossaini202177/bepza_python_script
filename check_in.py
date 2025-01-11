import base64
import os
from datetime import datetime

import cv2
import requests
import yaml
from dotenv import load_dotenv
from kafka import KafkaProducer

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
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "license_plate_topic"

producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)

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

            detected_plate, detected_image = detect_license_plate(frame)
            if detected_plate is None:
                print("License plate not detected.")
                continue

            easyocr_text = easyocr_ocr(detected_plate)
            tesseract_text = tesseract_ocr(detected_plate)

            # Extract text from OCR results
            easyocr_result = " ".join([item[1] for item in easyocr_text]) if easyocr_text else ""
            tesseract_result = tesseract_text.strip()
            detected_text = f"{easyocr_result} {tesseract_result}".strip()

            # Save the cropped license plate and annotated images
            cropped_filename = save_image(detected_plate, "cropped_license_plates")
            annotated_filename = save_image(detected_image, "annotated_images")

            # Convert the annotated image (detected_image) to Base64 for Kafka
            with open(annotated_filename, "rb") as img_file:
                base64_annotated_image = base64.b64encode(img_file.read()).decode("utf-8")

            # Convert the cropped license plate image (detected_plate) to Base64 for HTTP POST
            with open(cropped_filename, "rb") as img_file:
                base64_cropped_image = base64.b64encode(img_file.read()).decode("utf-8")

            current_time = datetime.now()
            current_time_ms = int(current_time.timestamp() * 1000)

            # Kafka Message
            kafka_message = {
                "dateTime": current_time_ms,
                "licensePlateNumber": detected_text,
                "gateId": 1,
                "entryType": "IN",
                "image": base64_annotated_image  # Annotated image for Kafka
            }
            producer.send(KAFKA_TOPIC, value=bytes(str(kafka_message), "utf-8"))
            print("Message sent to Kafka:", kafka_message)

            # HTTP POST Message
            message = {
                "dateTime": current_time_ms,
                "licensePlateNumber": detected_text,
                "gateId": 1,
                "entryType": "IN",
                "image": base64_cropped_image  # Cropped license plate for HTTP POST
            }
            url = "http://localhost:8082/api/entry-exit"
            response = requests.post(url, json=message)

            # Handle the response
            if response.status_code == 200:
                print("Check-in message successfully sent.")
            else:
                print(f"Failed to send message. Status code: {response.status_code}, Response: {response.text}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'cap' in locals():
            cap.release()
