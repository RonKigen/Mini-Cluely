import os
import json
import speech_recognition as sr

def get_config():
    """Get configuration information from config.json"""
    with open('config/config.json', 'r') as f:
        return json.load(f)

def speech_to_text(wav_file_path):
    """Convert speech file to text using speech recognition with fallback options"""
    import wave
    import struct
    
    recognizer = sr.Recognizer()
    
    # Configure recognizer for better performance
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    
    try:
        # First, check if the audio file has sufficient content
        with wave.open(wav_file_path, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            if len(frames) == 0:
                return {
                    'err_no': 3303,
                    'err_msg': 'Audio file is empty',
                    'result': []
                }
            
            # Check audio amplitude to see if there's meaningful content
            audio_values = struct.unpack('<' + 'h' * (len(frames) // 2), frames)
            max_amplitude = max(abs(v) for v in audio_values) if audio_values else 0
            
            if max_amplitude < 100:  # Very quiet audio
                return {
                    'err_no': 3304,
                    'err_msg': 'Audio is too quiet or silent. Please speak louder and closer to the microphone.',
                    'result': []
                }
        
        # Load audio file for recognition
        with sr.AudioFile(wav_file_path) as source:
            # Adjust for ambient noise to improve recognition
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Record the audio data
            audio_data = recognizer.record(source)
        
        # Try offline recognition first (Sphinx/PocketSphinx)
        try:
            print("Trying offline speech recognition (Sphinx)...")
            recognized_text = recognizer.recognize_sphinx(audio_data)
            print(f"Sphinx recognition successful: {recognized_text}")
            return {
                'err_no': 0,
                'err_msg': 'success (Sphinx offline)',
                'result': [recognized_text]
            }
        except sr.UnknownValueError:
            print("Sphinx could not understand audio")
        except Exception as e:
            print(f"Sphinx recognition failed: {e}")
        
        # Try Google recognition as backup
        try:
            print("Trying online speech recognition (Google)...")
            recognized_text = recognizer.recognize_google(audio_data, language='en-US')
            print(f"Google recognition successful: {recognized_text}")
            return {
                'err_no': 0,
                'err_msg': 'success (Google online)',
                'result': [recognized_text]
            }
        except sr.UnknownValueError:
            print("Google could not understand audio")
        except sr.RequestError as e:
            print(f"Google API error: {e}")
        except Exception as e:
            print(f"Google recognition failed: {e}")
        
        # If both methods failed to understand audio
        return {
            'err_no': 3301,
            'err_msg': 'Could not understand audio with any recognition method. The speech may be unclear, too quiet, or contain background noise. Please try speaking more clearly or use text input.',
            'result': []
        }
        
    except Exception as e:
        # Any other error
        return {
            'err_no': 3300,
            'err_msg': f'Speech recognition error: {e}',
            'result': []
        }
