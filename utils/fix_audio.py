"""
Audio Processing Utility
Fix and process existing audio files
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import Config
from src.transcription_service import TranscriptionService

def find_latest_audio_file():
    """Find the most recent audio file"""
    audio_dir = Config.AUDIO_OUTPUT_DIR
    if not os.path.exists(audio_dir):
        return None
    
    audio_files = [f for f in os.listdir(audio_dir) 
                   if f.endswith(('.wav', '.mp3', '.m4a'))]
    
    if not audio_files:
        return None
    
    # Sort by modification time
    audio_files.sort(
        key=lambda x: os.path.getmtime(os.path.join(audio_dir, x)), 
        reverse=True
    )
    
    return os.path.join(audio_dir, audio_files[0])

def process_audio_file(audio_file_path):
    """Process existing audio file"""
    if not os.path.exists(audio_file_path):
        print(f"❌ Audio file not found: {audio_file_path}")
        return False
    
    print(f"🎵 Processing: {os.path.basename(audio_file_path)}")
    
    Config.create_directories()
    
    try:
        # Initialize transcription service
        transcription_service = TranscriptionService()
        
        print("🤖 Starting AI transcription...")
        transcript_data = transcription_service.transcribe_with_speakers(audio_file_path)
        
        if not transcript_data:
            print("⚠️ Transcription failed")
            return False
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return False
    
    # Save transcript
    text_file = save_transcript(transcript_data, audio_file_path)
    
    if text_file:
        print(f"✅ SUCCESS! Transcript saved: {os.path.basename(text_file)}")
        return True
    else:
        print("❌ Failed to save transcript")
        return False

def save_transcript(transcript_data, audio_file_path):
    """Save transcript file"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{Config.EXPORT_OUTPUT_DIR}/processed_transcript_{timestamp}.txt"
        
        # Map speakers to names
        speaker_names = assign_speaker_names(transcript_data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("PROCESSED AUDIO TRANSCRIPT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("FILE DETAILS:\n")
            f.write(f"Audio File: {os.path.basename(audio_file_path)}\n")
            f.write(f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Participants: {len(set(item['speaker'] for item in transcript_data))}\n\n")
            
            f.write("CONVERSATION:\n")
            f.write("-" * 30 + "\n\n")
            
            for entry in transcript_data:
                speaker = entry['speaker']
                text = entry['text']
                display_name = speaker_names.get(speaker, speaker)
                f.write(f"{display_name}: {text}\n\n")
            
            f.write("=" * 50 + "\n")
        
        return filename
        
    except Exception as e:
        print(f"Error saving transcript: {e}")
        return None

def assign_speaker_names(transcript_data):
    """Assign real names to speakers"""
    speakers = list(set(item['speaker'] for item in transcript_data))
    speakers.sort()
    
    name_mapping = {}
    for i, speaker in enumerate(speakers):
        if i < len(Config.DEFAULT_SPEAKER_NAMES):
            name_mapping[speaker] = Config.DEFAULT_SPEAKER_NAMES[i]
        else:
            name_mapping[speaker] = f"Person {i+1}"
    
    return name_mapping

def main():
    """Main function for standalone execution"""
    print("🔧 AUDIO PROCESSOR")
    print("="*40)
    
    # Look for latest audio file
    latest_audio = find_latest_audio_file()
    
    if latest_audio:
        print(f"📁 Found: {os.path.basename(latest_audio)}")
        choice = input("Process this file? (y/n): ").lower()
        
        if choice == 'y':
            success = process_audio_file(latest_audio)
            if success:
                print("\n🎉 Processing completed!")
            else:
                print("\n❌ Processing failed")
        else:
            print("Skipped processing")
    else:
        audio_file = input("Enter path to audio file: ").strip()
        if os.path.exists(audio_file):
            process_audio_file(audio_file)
        else:
            print("❌ File not found")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
