from datetime import datetime
import cv2
import pika
from detect import detect_license_plate
from ocr import easyocr_ocr, tesseract_ocr
from preprocess import add_bangla_text, save_image


QUEUE_NAME = "vehicle_queue"
rabbitmq_url = "amqp://localhost"

def main(image_path, font_path):
    try:
        # Image loading
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Could not open or find the image.")

        # Detect license plate
        detected_plate, detected_image = detect_license_plate(image)
        if detected_plate is None:
            raise ValueError("License plate not detected.")

        # Perform OCR
        easyocr_text = easyocr_ocr(detected_plate)
        tesseract_text = tesseract_ocr(detected_plate)
        detected_text = easyocr_text[0][1] if easyocr_text else tesseract_text.strip()

        # Save results
        cropped_filename = save_image(detected_plate, "cropped_license_plates")
        annotated_filename = save_image(detected_image, "annotated_images")

        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

       
        message = {
            "ocr_text": detected_text,
            "image_path": annotated_filename,
            "time": current_time,
            "status": "check_out"
        }
        print("message",message)

        connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME)
        channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=str(message))
        print("Check-out message sent.")
        connection.close()
    except Exception as e:
        print(f"An error occurred in check_out.py: {e}")

if __name__ == "__main__":
    main("abcd.jpg", "./bangla-text/SolaimanLipi.ttf")
