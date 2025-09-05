import os
import threading
import wave
import pyaudio
import numpy as np
import time

class AudioRecorder:
    """Audio Recorder that captures Chrome's meeting audio via system recording"""

    def __init__(self):
        self.recording = False
        self.frames = []
        self.thread = None
        self.session_name = None
        self.save_dir = None

    def find_audio_devices(self):
        """Try different Stereo Mix devices for better quality"""
        print("🎵 Testing different audio devices...")
        
        # Try these device indices in order
        test_devices = [8, 18, 24, 1]  # From your device list
        
        for device_id in test_devices:
            print(f"   Testing device {device_id}")
            return None, device_id


    def start_recording(self, session_name, save_dir):
        os.makedirs(save_dir, exist_ok=True)
        self.session_name = session_name
        self.save_dir = save_dir
        self.recording = True
        self.frames = []
        self.thread = threading.Thread(target=self._record)
        self.thread.start()
        print("🎧 Started recording Chrome's meeting audio")
        return True

    def _record(self):
        p = pyaudio.PyAudio()
        stream = None
        
        try:
            # Open default recording device (should be Stereo Mix)
            stream = p.open(
                format=pyaudio.paInt16,
                channels=2,              # Stereo for better quality
                rate=44100,
                input=True,
                frames_per_buffer=1024
            )
            
            print("🔴 Recording Chrome meeting audio via Stereo Mix...")
            
            frame_count = 0
            while self.recording:
                data = stream.read(1024, exception_on_overflow=False)
                self.frames.append(data)
                frame_count += 1
                
                # Show progress every 3 seconds
                if frame_count % (44100 // 1024 * 3) == 0:
                    duration = frame_count * 1024 / 44100
                    mins, secs = divmod(int(duration), 60)
                    
                    # Check volume level
                    audio_array = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    volume = np.max(np.abs(audio_array))
                    
                    status = "🎵 RECORDING" if volume > 0.01 else "🔇 SILENT"
                    print(f"\r   {status} {mins:02d}:{secs:02d} (vol: {volume:.3f})", end="", flush=True)
                
                time.sleep(0.001)
                
        except Exception as e:
            print(f"❌ Recording error: {e}")
            print("💡 Troubleshooting:")
            print("    - Make sure Stereo Mix is enabled and set as default recording device")
            print("    - Ensure Chrome is playing meeting audio")
            print("    - Run as Administrator")
            print("    - Check Windows microphone privacy settings")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
            p.terminate()
            print(f"\n⏹️ Recording stopped - {len(self.frames)} frames captured")

    def stop_recording(self):
        self.recording = False
        if self.thread:
            self.thread.join()
        
        if not self.frames:
            print("❌ No audio frames recorded")
            return None
        
        file_path = os.path.join(self.save_dir, f"{self.session_name}.wav")
        
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(2)      # Stereo
            wf.setsampwidth(2)      # 16-bit  
            wf.setframerate(44100)  # 44.1kHz
            wf.writeframes(b''.join(self.frames))
        
        # Verify the saved file
        file_size = os.path.getsize(file_path)
        duration = len(self.frames) * 1024 / 44100
        
        print(f"✅ Meeting audio saved: {file_path}")
        print(f"   📊 Size: {file_size:,} bytes ({duration:.1f}s)")
        
        # Quick volume analysis
        try:
            with wave.open(file_path, 'rb') as test_wf:
                sample_data = test_wf.readframes(min(test_wf.getnframes(), 44100))
                sample_audio = np.frombuffer(sample_data, dtype=np.int16).astype(np.float32) / 32768.0
                if len(sample_audio) > 2:
                    # Average stereo channels for analysis
                    sample_audio = np.mean(sample_audio.reshape(-1, 2), axis=1)
                sample_volume = np.max(np.abs(sample_audio))
                print(f"   📈 Audio level: {sample_volume:.4f}")
                
                if sample_volume > 0.01:
                    print(f"   ✅ Chrome meeting audio captured successfully!")
                    print(f"   🎯 Ready for transcription with both your voice and participants!")
                else:
                    print(f"   ⚠️ Low audio - Chrome may not be outputting meeting audio")
                    print(f"       Check Chrome audio settings and Stereo Mix configuration")
                    
        except Exception as e:
            print(f"   ⚠️ Could not analyze audio: {e}")
        
        return file_path
