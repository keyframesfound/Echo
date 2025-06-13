"""
Basic speech recognition module.
"""
import speech_recognition as sr

# Recognize speech from the default microphone

def recognize_speech(timeout: int = 5) -> str:
    """
    Recognize speech from the microphone and return as text.
    Args:
        timeout (int): Maximum seconds to wait for speech.
    Returns:
        str: Recognized text or error message.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            print("Listening...")
            audio = recognizer.listen(source, timeout=timeout)
            print("Recognizing...")
            text = recognizer.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            return "[No speech detected]"
        except sr.UnknownValueError:
            return "[Could not understand audio]"
        except Exception as e:
            return f"[Speech recognition error: {e}]" 