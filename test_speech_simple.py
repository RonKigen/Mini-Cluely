"""
Simple speech recognition test utility
This script helps test speech recognition with better error handling
"""

import speech_recognition as sr
import wave
import struct
import sys
import os

def simple_speech_test(audio_file):
    """Simple speech recognition test"""
    print(f"Testing speech recognition on: {audio_file}")
    
    if not os.path.exists(audio_file):
        print(f"❌ Audio file not found: {audio_file}")
        return None
    
    # Check audio properties first
    try:
        with wave.open(audio_file, 'rb') as wf:
            print(f"📊 Audio Properties:")
            print(f"   Channels: {wf.getnchannels()}")
            print(f"   Sample Rate: {wf.getframerate()}")
            print(f"   Duration: {wf.getnframes() / wf.getframerate():.2f} seconds")
            
            # Check amplitude
            frames = wf.readframes(min(16000, wf.getnframes()))  # First second
            if frames:
                audio_values = struct.unpack('<' + 'h' * (len(frames) // 2), frames)
                max_amp = max(abs(v) for v in audio_values) if audio_values else 0
                print(f"   Max Amplitude: {max_amp}")
                
                if max_amp < 100:
                    print("⚠️ Warning: Very low audio levels detected!")
                    return None
                    
    except Exception as e:
        print(f"❌ Error reading audio file: {e}")
        return None
    
    # Try recognition
    recognizer = sr.Recognizer()
    
    try:
        print("🎤 Loading audio...")
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
        print("✅ Audio loaded successfully")
        
        # Try Sphinx (offline) first
        try:
            print("🔄 Trying offline recognition (Sphinx)...")
            text = recognizer.recognize_sphinx(audio_data)
            print(f"✅ Sphinx Success: '{text}'")
            return text
        except Exception as e:
            print(f"❌ Sphinx failed: {e}")
        
        # Try Google (online) as backup
        try:
            print("🔄 Trying online recognition (Google)...")
            text = recognizer.recognize_google(audio_data, language='en-US')
            print(f"✅ Google Success: '{text}'")
            return text
        except Exception as e:
            print(f"❌ Google failed: {e}")
        
        print("❌ All recognition methods failed")
        return None
        
    except Exception as e:
        print(f"❌ Error during recognition: {e}")
        return None

if __name__ == "__main__":
    # Test with the recorded audio file
    audio_file = "assets/recorded_audio.wav"
    result = simple_speech_test(audio_file)
    
    if result:
        print(f"\n🎉 Final Result: '{result}'")
    else:
        print("\n❌ Speech recognition failed")
        print("\n💡 Suggestions:")
        print("1. Check your microphone volume in Windows settings")
        print("2. Record a new sample with clear speech")
        print("3. Use the text input instead")
        print("4. Try the microphone test in the app")
