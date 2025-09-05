import os
import time
import signal
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.meet_bot import GoogleMeetBot
from src.audio_recorder import AudioRecorder
from src.transcription_service import TranscriptionService

# Configuration
class Config:
    BASE_OUTPUT_DIR = "outputs"
    AUDIO_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, "audio")
    EXPORT_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, "exports")
    
    @classmethod
    def create_directories(cls):
        os.makedirs(cls.AUDIO_OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.EXPORT_OUTPUT_DIR, exist_ok=True)

# Global variables
recording_active = True
shutdown_requested = False

def signal_handler(signum, frame):
    global recording_active, shutdown_requested
    recording_active = False
    shutdown_requested = True
    print("\n🛑 Stopping bot...")

def main():
    global recording_active, shutdown_requested
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🤖 GOOGLE MEET RECORDING BOT - ENHANCED")
    print("=" * 100)
    print("🔧 Invisible bot with Chrome profile authentication")
    print("🎵 Clean audio recording (meeting audio only)")
    print("📝 Premium transcription (AssemblyAI + Whisper fallback)")
    print("👥 Automatic participant detection")
    print("🚫 Completely silent operation")
    print("=" * 100)
    
    Config.create_directories()
    
    meet_url = input("\n🌐 Enter Google Meet URL: ").strip()
    
    if "meet.google.com" not in meet_url:
        print("❌ Invalid Google Meet URL")
        return
    
    # Initialize components
    bot = GoogleMeetBot()
    transcription_service = TranscriptionService()
    
    try:
        # Step 1: Join meeting
        print(f"\n1. 🚪 Joining meeting...")
        if not bot.join_meeting(meet_url):
            print("❌ Failed to join meeting")
            return

        # Step 2: Start recording
        print(f"\n2. 🎙️ Starting recording...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = f"meeting_{timestamp}"
        
        recorder = AudioRecorder()
        if not recorder.start_recording(session_name, Config.AUDIO_OUTPUT_DIR):
            print("❌ Failed to start recording")
            return
        
        print("✅ Recording started")
        
        # Step 3: Record session
        print(f"\n3. 📝 Recording active...")
        print("   Press Ctrl+C to stop recording and transcribe")
        
        try:
            while recording_active and not shutdown_requested:
                time.sleep(1)
                if not bot.is_meeting_active():
                    print("\n⚠️ Meeting ended")
                    break
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
        
        # Step 4: Stop recording
        print(f"\n4. ⏹️ Processing recording...")
        audio_file = recorder.stop_recording()
        
        if not audio_file:
            print("❌ No audio recorded")
            return
        
        # Step 5: Transcribe
        print(f"\n5. 🤖 Starting transcription...")
        participant_names = ["Person 1", "Person 2", "Person 3", "Person 4"]
        transcript_text = transcription_service.transcribe_audio(audio_file, participant_names)
        
        # Step 6: Save transcript
        print(f"\n6. 💾 Saving transcript...")
        transcript_filename = f"{Config.EXPORT_OUTPUT_DIR}/transcript_{timestamp}.txt"
        
        with open(transcript_filename, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
        
        # Success summary
        print(f"\n🎉 SUCCESS!")
        print(f"📁 Audio: {os.path.basename(audio_file)}")
        print(f"📄 Transcript: {os.path.basename(transcript_filename)}")
        print(f"💾 Output Location: {Config.BASE_OUTPUT_DIR}/")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    finally:
        print(f"\n🧹 Cleaning up...")
        try:
            bot.quit()
        except:
            pass
        print("✅ Cleanup completed")
        
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
