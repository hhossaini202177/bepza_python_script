import cv2
import easyocr
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

def easyocr_ocr(image):
    try:
        reader = easyocr.Reader(['bn'])
        return reader.readtext(image)
    except Exception as e:
        print(f"An error occurred in easyocr_ocr: {e}")
        return []

def tesseract_ocr(image):
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return pytesseract.image_to_string(gray, lang='ben')
    except Exception as e:
        print(f"An error occurred in tesseract_ocr: {e}")
        return ""
