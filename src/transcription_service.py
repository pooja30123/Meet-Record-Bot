"""
Complete Transcription Service with Speaker Diarization for Conversation Format
"""

import os
import time
import numpy as np
from datetime import datetime
import re
import wave
from dotenv import load_dotenv

load_dotenv()

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import assemblyai as aai
    ASSEMBLYAI_AVAILABLE = True
except ImportError:
    ASSEMBLYAI_AVAILABLE = False

class TranscriptionService:
    def __init__(self):
        self.whisper_model = None
        self.assemblyai_client = None
        self.diarization_pipeline = None

        # Initialize AssemblyAI with extended timeout
        if ASSEMBLYAI_AVAILABLE:
            api_key = os.getenv('ASSEMBLYAI_API_KEY')
            if api_key and len(api_key) > 10:
                try:
                    aai.settings.api_key = api_key
                    aai.settings.http_timeout = 300.0      # 5 minute timeout
                    aai.settings.polling_interval = 10.0   # Check every 10 seconds
                    self.assemblyai_client = aai.Transcriber()
                    print("✅ AssemblyAI initialized - Premium transcription ready!")
                except Exception as e:
                    print(f"⚠️ AssemblyAI initialization failed: {e}")
            else:
                print("⚠️ AssemblyAI API key missing or invalid.")
        
        # Load Whisper as fallback
        if WHISPER_AVAILABLE:
            try:
                self.whisper_model = whisper.load_model("base")
                print("✅ Whisper model loaded as fallback")
            except Exception as e:
                print(f"❌ Whisper loading failed: {e}")

        # Optional: Load pyannote for better speaker diarization
        try:
            from pyannote.audio import Pipeline
            self.diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
            print("✅ Pyannote diarization loaded")
        except Exception as e:
            print(f"⚠️ Pyannote diarization not available: {e}")

    def transcribe_audio(self, audio_file_path, participant_names=None):
        """Main transcription method with conversation format"""
        if not os.path.exists(audio_file_path):
            return "❌ Error: Audio file not found"
        
        if not participant_names:
            participant_names = [f"Person {i+1}" for i in range(5)]
        
        print(f"🤖 Starting transcription: {os.path.basename(audio_file_path)}")
        
        # Analyze audio quality
        audio_info = self.get_audio_info(audio_file_path)
        print(f"   📊 Duration: {audio_info['duration']:.1f}s")
        print(f"   📦 Size: {audio_info['filesize']:,} bytes")
        print(f"   🔊 Volume: {audio_info['max_volume']:.3f}")
        
        # Check if audio has meaningful content
        if audio_info['max_volume'] < 0.01:
            return self.create_error_message(audio_file_path, audio_info)
        
        # Try AssemblyAI with speaker diarization enabled
        if self.assemblyai_client:
            print("   🚀 Trying AssemblyAI Premium...")
            try:
                transcript_text = self._transcribe_with_assemblyai(audio_file_path)
                if transcript_text:
                    print("   ✅ AssemblyAI completed successfully")
                    return self.create_professional_transcript(transcript_text, audio_file_path, audio_info, "AssemblyAI Premium")
                else:
                    print(f"   ❌ AssemblyAI failed to produce transcript")
            except Exception as e:
                print(f"   ❌ AssemblyAI exception: {e}")
        
        # Fallback to Whisper if AssemblyAI fails
        if self.whisper_model:
            print("   🔄 Using Whisper fallback...")
            try:
                transcript_text = self._transcribe_with_whisper(audio_file_path)
                if transcript_text:
                    print("   ✅ Whisper completed successfully")
                    # Format Whisper output as conversation with simple speaker detection
                    formatted_text = self._format_whisper_as_conversation(transcript_text)
                    return self.create_professional_transcript(formatted_text, audio_file_path, audio_info, "Whisper Local")
            except Exception as e:
                print(f"   ❌ Whisper failed: {e}")
        
        return self.create_failure_message(audio_file_path, audio_info)

    def _format_whisper_as_conversation(self, transcript_text):
        """Format Whisper transcript as conversation by detecting natural breaks"""
        if not transcript_text or len(transcript_text.strip()) < 10:
            return f"Person 1: {transcript_text}"
        
        # Split by sentences and natural conversation breaks
        sentences = re.split(r'[.!?]+\s*', transcript_text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 1:
            return f"Person 1: {transcript_text}"
        
        conversation_parts = []
        current_speaker = 1
        
        for i, sentence in enumerate(sentences):
            if sentence:
                # Simple heuristic: alternate speakers every 2-3 sentences or on certain phrases
                if i > 0 and (
                    i % 3 == 0 or  # Every 3 sentences
                    any(phrase in sentence.lower() for phrase in [
                        'yes', 'no', 'okay', 'right', 'sure', 'well', 'so', 'but', 'however',
                        'i think', 'i believe', 'actually', 'basically', 'definitely'
                    ])
                ):
                    current_speaker = 2 if current_speaker == 1 else 1
                
                conversation_parts.append(f"Person {current_speaker}: {sentence.strip()}.")
        
        return "\n\n".join(conversation_parts)

    def _transcribe_with_assemblyai(self, audio_file_path):
        """Transcribe using AssemblyAI WITH speaker diarization for conversation format"""
        try:
            # CRITICAL: Enable speaker_labels for conversation format
            config = aai.TranscriptionConfig(
                speaker_labels=True,              # ENABLE for conversation format
                speakers_expected=2,              # Expected number of speakers
                punctuate=True,
                format_text=True,
                language_detection=True,
                auto_chapters=False,              # Disable chapters for cleaner output
                entity_detection=False            # Disable entities for cleaner output
            )
            
            print("      📡 Uploading to AssemblyAI with speaker diarization...")
            transcript = self.assemblyai_client.transcribe(audio_file_path, config)
            
            # Wait for completion with extended timeout
            start_time = time.time()
            max_wait_time = 900  # 15 minutes max
            
            while transcript.status not in ["completed", "error"]:
                elapsed = time.time() - start_time
                if elapsed > max_wait_time:
                    print("      ❌ AssemblyAI timeout after 15 minutes")
                    return None
                
                mins, secs = divmod(int(elapsed), 60)
                print(f"      🔄 Processing... {mins:02d}:{secs:02d}", end='\r')
                
                time.sleep(10)  # Check every 10 seconds
                
                try:
                    transcript = self.assemblyai_client.get_transcript(transcript.id)
                except Exception as e:
                    print(f"      ⚠️ Polling error: {e}")
                    time.sleep(5)
                    continue
            
            if transcript.status == "completed":
                elapsed = int(time.time() - start_time)
                print(f"      ✅ AssemblyAI completed in {elapsed}s")
                
                # PROCESS utterances for conversation format
                if hasattr(transcript, 'utterances') and transcript.utterances:
                    conversation_parts = []
                    for utterance in transcript.utterances:
                        speaker_label = utterance.speaker
                        # Convert speaker label to readable format
                        if isinstance(speaker_label, str) and speaker_label.startswith('Speaker '):
                            speaker_name = f"Person {speaker_label.split(' ')[1]}"
                        else:
                            speaker_num = int(speaker_label) + 1 if isinstance(speaker_label, int) else 1
                            speaker_name = f"Person {speaker_num}"
                        
                        # Clean and format the utterance text
                        utterance_text = utterance.text.strip()
                        if utterance_text:
                            conversation_parts.append(f"{speaker_name}: {utterance_text}")
                    
                    if conversation_parts:
                        # Join with double newlines for proper paragraph separation
                        formatted_conversation = "\n\n".join(conversation_parts)
                        print(f"      🎯 Formatted {len(conversation_parts)} speaker utterances")
                        return formatted_conversation
                
                # Fallback to single speaker format if no utterances
                text = transcript.text.strip() if transcript.text else None
                if text:
                    # Try to format as conversation even without diarization
                    return self._format_whisper_as_conversation(text)
                else:
                    return None
            else:
                error = getattr(transcript, 'error', 'Unknown error')
                print(f"      ❌ AssemblyAI error: {error}")
                return None
                
        except Exception as e:
            print(f"      ❌ AssemblyAI exception: {e}")
            return None

    def _transcribe_with_whisper(self, audio_file_path):
        """Transcribe using Whisper with hallucination prevention"""
        try:
            print("      🎯 Processing with Whisper...")
            
            result = self.whisper_model.transcribe(
                audio_file_path,
                fp16=False,
                language="en",
                verbose=False,
                temperature=0.0,
                condition_on_previous_text=False,  # Prevents repetition
                no_speech_threshold=0.6,          # Better silence detection
                logprob_threshold=-1.0            # Filter low-confidence words
            )
            
            text = result["text"].strip()
            
            # DETECT AND FILTER HALLUCINATIONS
            words = text.split()
            if len(words) > 3:
                # Check for repeated words (hallucination detection)
                word_counts = {}
                for word in words:
                    word_counts[word] = word_counts.get(word, 0) + 1
                
                # If any word appears more than 30% of the time, it's likely hallucination
                max_word_count = max(word_counts.values())
                if max_word_count > len(words) * 0.3:
                    most_repeated = max(word_counts, key=word_counts.get)
                    print(f"      ⚠️ Hallucination detected: '{most_repeated}' repeated {max_word_count} times")
                    
                    # Clean the text by removing excessive repetitions
                    cleaned_words = []
                    prev_word = ""
                    repeat_count = 0
                    
                    for word in words:
                        if word == prev_word:
                            repeat_count += 1
                            if repeat_count < 2:  # Allow max 1 consecutive repeat
                                cleaned_words.append(word)
                        else:
                            cleaned_words.append(word)
                            repeat_count = 0
                        prev_word = word
                    
                    text = " ".join(cleaned_words)
                    print(f"      🔧 Cleaned text: {len(cleaned_words)} words (was {len(words)})")
            
            if len(text) > 5:
                print(f"      ✅ Whisper completed ({len(text)} characters)")
                return text
            else:
                print("      ⚠️ Whisper result too short after cleaning")
                return None
                
        except Exception as e:
            print(f"      ❌ Whisper error: {e}")
            return None

    def get_audio_info(self, audio_file_path):
        """Analyze audio file for quality and content"""
        try:
            filesize = os.path.getsize(audio_file_path)
            
            with wave.open(audio_file_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / rate
                
                # Read sample to check volume
                sample_frames = min(frames, rate)  # First second
                audio_data = wf.readframes(sample_frames)
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                max_volume = np.max(np.abs(audio_array)) if len(audio_array) > 0 else 0.0
            
            return {
                "duration": duration,
                "filesize": filesize,
                "max_volume": max_volume,
                "samplerate": rate
            }
        except Exception as e:
            print(f"   ⚠️ Audio analysis error: {e}")
            return {
                "duration": 0,
                "filesize": 0,
                "max_volume": 0,
                "samplerate": 44100
            }

    def create_professional_transcript(self, conversation_text, audio_file_path, audio_info, service_name):
        """Create formatted professional transcript"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        filename = os.path.basename(audio_file_path)
        
        return f"""GOOGLE MEET PROFESSIONAL TRANSCRIPT
{'=' * 70}
📅 Generated: {timestamp}
🔧 Transcription Service: {service_name}
📁 Audio File: {filename}
⏱️ Duration: {audio_info['duration']:.1f} seconds
🔊 Audio Quality: {audio_info['max_volume']:.3f}
📊 File Size: {audio_info['filesize']:,} bytes
✅ Status: TRANSCRIPTION COMPLETED SUCCESSFULLY


MEETING CONVERSATION:
{'─' * 70}
{conversation_text}
{'─' * 70}


MEETING SUMMARY:
• Total Duration: {audio_info['duration']:.1f} seconds
• Audio Quality: {'Excellent' if audio_info['max_volume'] > 0.3 else 'Good' if audio_info['max_volume'] > 0.1 else 'Fair'}
• Transcription Method: {service_name}
• Processing Date: {timestamp}


{'=' * 70}
Meeting transcript generated by Google Meet Recording Bot.
Bot operated invisibly with visible microphone indicator.
{'=' * 70}"""

    def create_error_message(self, audio_file_path, audio_info):
        """Create error message for silent audio"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        filename = os.path.basename(audio_file_path)
        
        return f"""GOOGLE MEET TRANSCRIPT - NO SPEECH DETECTED
{'=' * 70}
📅 Generated: {timestamp}
📁 Audio File: {filename}
⏱️ Duration: {audio_info['duration']:.1f} seconds
🔊 Volume Level: {audio_info['max_volume']:.3f}


⚠️ ISSUE: No meaningful speech detected in the audio recording.


TROUBLESHOOTING STEPS:
1. Check Windows microphone privacy permissions
2. Verify Stereo Mix configuration and enable "Listen to this device"
3. Test Chrome audio output with music playback
4. Ensure bot shows green microphone indicator
5. Run Command Prompt as Administrator


{'=' * 70}
Please fix audio setup and try recording again.
{'=' * 70}"""

    def create_failure_message(self, audio_file_path, audio_info):
        """Create failure message when transcription services fail"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        filename = os.path.basename(audio_file_path)
        
        return f"""GOOGLE MEET TRANSCRIPT - TRANSCRIPTION SERVICES ISSUE
{'=' * 70}
📅 Generated: {timestamp}
📁 Audio File: {filename}
⏱️ Duration: {audio_info['duration']:.1f} seconds
🔊 Volume Level: {audio_info['max_volume']:.3f}


❌ ISSUE: Both AssemblyAI and Whisper transcription failed.


LIKELY CAUSES:
• AssemblyAI timeout (network/server issues)
• Audio format incompatibility
• Temporary service disruption
• Poor audio quality


SOLUTIONS:
• Try again in a few minutes (AssemblyAI server may be busy)
• Check internet connection stability
• Verify AssemblyAI API key is valid
• Test with different Stereo Mix device


TECHNICAL DETAILS:
• Audio Level: {audio_info['max_volume']:.4f} (Good: > 0.01)
• File Size: {audio_info['filesize']:,} bytes
• Duration: {audio_info['duration']:.1f} seconds


{'=' * 70}
Audio was captured successfully - transcription service issue only.
{'=' * 70}"""
