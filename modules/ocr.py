# Handles screen capture and OCR

def extract_text_from_image(image):
    import pytesseract
    return pytesseract.image_to_string(image)

# Placeholder for screen capture

def capture_screen():
    # TODO: Implement screen capture
    return None
