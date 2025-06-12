# Enhanced speech system with multiple TTS/STT engines, voice customization, and audio processing
import threading
import queue
import logging
import time
import json
import os
import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Dict, Callable
from enum import Enum
import sounddevice as sd
import webrtcvad
import wave
import asyncio
from concurrent.futures import ThreadPoolExecutor
import torch

class SpeechEngine(Enum):
    PYTTSX3 = "pyttsx3"
    ELEVENLABS = "elevenlabs"
    COQUI = "coqui"
    OPENAI_WHISPER = "whisper"
    GOOGLE_CLOUD = "google"
    AZURE = "azure"

@dataclass
class VoiceProfile:
    name: str
    engine: SpeechEngine
    language: str
    gender: str
    speed: float
    pitch: float
    volume: float
    settings: Dict

class AudioProcessor:
    def __init__(self):
        self.vad = webrtcvad.Vad(3)  # Aggressive VAD
        self.sample_rate = 16000
        self.frame_duration = 30  # ms
        self.buffer = []
        self.is_speaking = False
        
    def process_audio(self, indata, frames, time, status):
        """Real-time audio processing with VAD"""
        audio_chunk = indata.copy()
        is_speech = self.vad.is_speech(
            audio_chunk.tobytes(),
            sample_rate=self.sample_rate
        )
        
        if is_speech and not self.is_speaking:
            self.is_speaking = True
            self.buffer = [audio_chunk]
        elif is_speech:
            self.buffer.append(audio_chunk)
        elif self.is_speaking:
            self.is_speaking = False
            return np.concatenate(self.buffer)
        
        return None

class SpeechManager:
    def __init__(self):
        self.tts_queue = queue.Queue()
        self.stt_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.voice_profiles = {}
        self.current_profile = None
        self.audio_processor = AudioProcessor()
        self.whisper_model = None
        self.load_whisper_model()
        
    def load_whisper_model(self):
        """Load Whisper model for offline speech recognition"""
        if torch.cuda.is_available():
            self.whisper_model = torch.hub.load('openai/whisper', 'medium')
            self.whisper_model.to('cuda')
        else:
            self.whisper_model = torch.hub.load('openai/whisper', 'small')
        
    def create_voice_profile(self, name: str, engine: SpeechEngine, **kwargs):
        """Create and store a voice profile"""
        profile = VoiceProfile(
            name=name,
            engine=engine,
            language=kwargs.get('language', 'en-US'),
            gender=kwargs.get('gender', 'neutral'),
            speed=kwargs.get('speed', 1.0),
            pitch=kwargs.get('pitch', 1.0),
            volume=kwargs.get('volume', 1.0),
            settings=kwargs.get('settings', {})
        )
        self.voice_profiles[name] = profile
        if not self.current_profile:
            self.current_profile = profile
            
    def switch_voice(self, profile_name: str):
        """Switch to a different voice profile"""
        if profile_name in self.voice_profiles:
            self.current_profile = self.voice_profiles[profile_name]
            return True
        return False

    async def speak(self, text: str, profile_name: Optional[str] = None):
        """Async TTS with multiple engine support"""
        profile = self.voice_profiles.get(profile_name, self.current_profile)
        
        if profile.engine == SpeechEngine.ELEVENLABS:
            await self._speak_elevenlabs(text, profile)
        elif profile.engine == SpeechEngine.COQUI:
            await self._speak_coqui(text, profile)
        else:  # Fallback to pyttsx3
            await self._speak_pyttsx3(text, profile)

    async def listen(self, timeout: float = 5.0, continuous: bool = False) -> str:
        """Enhanced speech recognition with VAD and multiple engines"""
        try:
            with sd.InputStream(
                channels=1,
                samplerate=self.audio_processor.sample_rate,
                callback=self.audio_processor.process_audio
            ):
                while True:
                    audio_data = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        lambda: self.stt_queue.get(timeout=timeout)
                    )
                    
                    if audio_data is not None:
                        # Try Whisper first (offline)
                        try:
                            text = self.whisper_model.transcribe(audio_data)['text']
                            if text.strip():
                                return text
                        except Exception:
                            pass
                        
                        # Fallback to Google Speech Recognition
                        try:
                            import speech_recognition as sr
                            recognizer = sr.Recognizer()
                            audio = sr.AudioData(
                                audio_data.tobytes(),
                                self.audio_processor.sample_rate,
                                2
                            )
                            return recognizer.recognize_google(audio)
                        except Exception as e:
                            logging.error(f"Speech recognition error: {e}")
                            
                    if not continuous:
                        break
                        
        except Exception as e:
            logging.error(f"Audio capture error: {e}")
            return ""

    async def _speak_elevenlabs(self, text: str, profile: VoiceProfile):
        """Eleven Labs TTS integration"""
        try:
            from elevenlabs import generate, play
            audio = generate(
                text=text,
                voice=profile.settings.get('voice_id'),
                model=profile.settings.get('model', 'eleven_monolingual_v1')
            )
            play(audio)
        except Exception as e:
            logging.error(f"ElevenLabs TTS error: {e}")
            await self._speak_pyttsx3(text, profile)  # Fallback

    async def _speak_coqui(self, text: str, profile: VoiceProfile):
        """Coqui TTS integration"""
        try:
            from TTS.api import TTS
            tts = TTS(profile.settings.get('model_name', 'tts_models/en/ljspeech/tacotron2-DDC'))
            tts.tts_to_file(text=text, file_path="temp.wav")
            self._play_audio("temp.wav")
            os.remove("temp.wav")
        except Exception as e:
            logging.error(f"Coqui TTS error: {e}")
            await self._speak_pyttsx3(text, profile)  # Fallback

    async def _speak_pyttsx3(self, text: str, profile: VoiceProfile):
        """Traditional pyttsx3 TTS"""
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', int(175 * profile.speed))
        engine.setProperty('volume', profile.volume)
        
        voices = engine.getProperty('voices')
        for voice in voices:
            if profile.gender.lower() in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
                
        engine.say(text)
        engine.runAndWait()
        engine.stop()

    def _play_audio(self, file_path: str):
        """Play audio file using sounddevice"""
        with wave.open(file_path, 'rb') as wf:
            data = wf.readframes(wf.getnframes())
            sd.play(
                np.frombuffer(data, dtype=np.int16),
                wf.getframerate()
            )
            sd.wait()

# Global speech manager instance
speech_manager = SpeechManager()

# Create default voice profiles
speech_manager.create_voice_profile(
    "default",
    SpeechEngine.PYTTSX3,
    gender="neutral",
    speed=1.0
)

try:
    speech_manager.create_voice_profile(
        "eleven_labs",
        SpeechEngine.ELEVENLABS,
        settings={
            'voice_id': 'your_voice_id_here',
            'model': 'eleven_monolingual_v1'
        }
    )
except:
    pass

try:
    speech_manager.create_voice_profile(
        "coqui",
        SpeechEngine.COQUI,
        settings={
            'model_name': 'tts_models/en/ljspeech/tacotron2-DDC'
        }
    )
except:
    pass
