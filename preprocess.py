import os
from datetime import datetime

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def create_folder(folder_name):
    try:
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
    except Exception as e:
        print(f"An error occurred while creating folder '{folder_name}': {e}")

def save_image(image, folder_name="detected_images"):
    try:
        create_folder(folder_name)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        filename = f"{folder_name}/{timestamp}.jpg"
        cv2.imwrite(filename, image)
        return filename
    except Exception as e:
        print(f"An error occurred in save_image: {e}")
        return None

def add_bangla_text(image, text, position, font_path):
    try:
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        font = ImageFont.truetype(font_path, 30)
        draw = ImageDraw.Draw(pil_image)
        draw.text(position, text, font=font, fill=(0, 255, 0))
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"An error occurred in add_bangla_text: {e}")
        return image
