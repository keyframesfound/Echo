# Handles image recognition from webcam

def recognize_objects(frame):
    """
    Use the hybrid LLM backend to describe the webcam image for engineering, electronics, and general scene context.
    Converts the frame to a JPEG and sends to the vision+text LLM for a detailed description.
    """
    import cv2
    from modules import llm
    # Encode frame as JPEG
    ret, jpeg = cv2.imencode('.jpg', frame)
    if not ret:
        return ["[Could not capture webcam image]"]
    img_bytes = jpeg.tobytes()
    # Use a detailed prompt for the vision model
    prompt = (
        "Describe this image in detail for an engineer. "
        "If you see any circuits, components, or tools, identify and describe them. "
        "Otherwise, describe the general scene."
    )
    # Get the raw response for debugging
    description = llm.generate_vision_description(img_bytes, prompt)
    print("[Vision LLM raw response]", description)
    return [description.strip() if isinstance(description, str) else str(description)]
