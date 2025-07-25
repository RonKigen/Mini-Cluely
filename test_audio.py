#!/usr/bin/env python3
"""
Test script for audio recording and speech recognition
"""

import pyaudio
import wave
import time
import os
from chatbot.utils import speech_to_text

def test_microphone():
    """Test if microphone is working"""
    print("Testing microphone...")
    
    try:
        audio = pyaudio.PyAudio()
        
        # Get info about available devices
        print("\nAvailable audio devices:")
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  {i}: {info['name']} (inputs: {info['maxInputChannels']})")
        
        # Test default input device
        default_device = audio.get_default_input_device_info()
        print(f"\nDefault input device: {default_device['name']}")
        
        audio.terminate()
        return True
        
    except Exception as e:
        print(f"Microphone test failed: {e}")
        return False

def record_test_audio(duration=5):
    """Record a test audio file"""
    print(f"\nRecording test audio for {duration} seconds...")
    print("Please speak clearly into your microphone!")
    
    audio = pyaudio.PyAudio()
    frames = []
    
    try:
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        # Record audio
        for i in range(0, int(16000 / 1024 * duration)):
            data = stream.read(1024)
            frames.append(data)
            if i % 10 == 0:  # Print progress
                print(".", end="", flush=True)
        
        print("\nRecording complete!")
        
        # Save to file
        output_file = "test_recording.wav"
        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b''.join(frames))
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        return output_file
        
    except Exception as e:
        print(f"Recording failed: {e}")
        audio.terminate()
        return None

def test_speech_recognition(audio_file):
    """Test speech recognition on an audio file"""
    print(f"\nTesting speech recognition on {audio_file}...")
    
    if not os.path.exists(audio_file):
        print(f"Audio file {audio_file} not found!")
        return
    
    result = speech_to_text(audio_file)
    print(f"Recognition result:")
    print(f"  Error code: {result.get('err_no')}")
    print(f"  Error message: {result.get('err_msg')}")
    print(f"  Result: {result.get('result')}")

if __name__ == "__main__":
    print("=== Audio System Test ===")
    
    # Test 1: Check microphone
    if not test_microphone():
        print("Microphone test failed. Please check your audio setup.")
        exit(1)
    
    # Test 2: Test with existing audio file
    existing_file = "assets/recorded_audio.wav"
    if os.path.exists(existing_file):
        print(f"\nTesting with existing file: {existing_file}")
        test_speech_recognition(existing_file)
    
    # Test 3: Record new audio and test
    print("\n" + "="*50)
    input("Press Enter to start a new 5-second recording test...")
    
    test_file = record_test_audio(5)
    if test_file:
        test_speech_recognition(test_file)
        
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
    
    print("\n=== Test Complete ===")
