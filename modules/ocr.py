"""
OCR module for extracting text from images.
"""
from PIL import Image
import pytesseract

def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image file using pytesseract.
    Args:
        image_path (str): Path to the image file.
    Returns:
        str: Extracted text or error message.
    """
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip() if text.strip() else "[No text found in image]"
    except Exception as e:
        return f"[OCR error: {e}]" 