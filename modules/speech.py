# Handles speech-to-text and text-to-speech

import threading
import queue
import logging
import time

class TTSManager:
    def __init__(self):
        self.queue = queue.Queue()
        self.thread = None
        self.engine = None
        self.lock = threading.Lock()
        
    def _init_engine(self):
        import pyttsx3
        if self.engine is None:
            self.engine = pyttsx3.init()
            # Configure for better stability
            self.engine.setProperty('rate', 175)     # Speed of speech
            self.engine.setProperty('volume', 1.0)   # Volume level
            
    def _cleanup_engine(self):
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
            self.engine = None
    
    def _tts_worker(self):
        while True:
            try:
                text = self.queue.get(timeout=5)  # 5 second timeout
                if text is None:
                    break
                    
                with self.lock:
                    try:
                        self._init_engine()
                        self.engine.say(text)
                        self.engine.runAndWait()
                    except Exception as e:
                        logging.error(f"TTS error: {e}")
                        self._cleanup_engine()  # Reinitialize on next attempt
                    finally:
                        self.queue.task_done()
                        
            except queue.Empty:
                # No speech for 5 seconds, cleanup engine
                with self.lock:
                    self._cleanup_engine()
                continue
            except Exception as e:
                logging.error(f"TTS worker error: {e}")
                time.sleep(1)  # Prevent rapid retries
                continue

# Global TTS manager instance
_tts_manager = TTSManager()

def speak(text):
    """Thread-safe function to speak text"""
    global _tts_manager
    
    # Start thread if needed
    with _tts_manager.lock:
        if _tts_manager.thread is None or not _tts_manager.thread.is_alive():
            _tts_manager.thread = threading.Thread(
                target=_tts_manager._tts_worker, 
                daemon=True
            )
            _tts_manager.thread.start()
    
    # Queue the text
    _tts_manager.queue.put(text)

# Placeholder for speech-to-text

def listen():
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio)
        except Exception as e:
            return None
