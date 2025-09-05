import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for Google Meet Recording Bot"""
    
    # API Keys - Load from .env file
    ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY', None)
    
    # Audio Recording Settings
    AUDIO_SAMPLE_RATE = 44100
    AUDIO_CHANNELS = 2
    AUDIO_FORMAT = "wav"
    AUDIO_BUFFER_SIZE = 4096
    
    # Directory Structure
    BASE_OUTPUT_DIR = "outputs"
    AUDIO_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, "audio")
    EXPORT_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, "exports")
    
    # Generic participant names (empty = use "Person 1", "Person 2")
    DEFAULT_SPEAKER_NAMES = []  # Empty for generic names
    
    # Audio Device Settings
    MIC_DEVICE_ID = 1           # Your working microphone
    SYSTEM_AUDIO_DEVICE_ID = 7  # Your working system audio
    
    @classmethod
    def create_directories(cls):
        os.makedirs(cls.AUDIO_OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.EXPORT_OUTPUT_DIR, exist_ok=True)
    
    @classmethod
    def get_participant_names(cls, count=2):
        """Return generic 'Person N' format when no names provided"""
        if not cls.DEFAULT_SPEAKER_NAMES:
            return [f"Person {i+1}" for i in range(count)]
        return cls.DEFAULT_SPEAKER_NAMES[:count]
    
    @classmethod
    def validate_api_key(cls):
        """Check if AssemblyAI API key is loaded"""
        if cls.ASSEMBLYAI_API_KEY and len(cls.ASSEMBLYAI_API_KEY) > 10:
            print("✅ AssemblyAI API key loaded from .env file")
            return True
        else:
            print("⚠️ AssemblyAI API key not found in .env file")
            return False
