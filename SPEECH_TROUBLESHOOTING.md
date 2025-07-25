# Speech Recognition Troubleshooting Guide

## Problem: "Could not understand audio" errors

The speech recognition failures you're experiencing are likely due to one of these common issues:

### 1. **Audio Quality Issues (Most Common)**
- **Microphone Volume Too Low**: The recorded audio has very low amplitude (max amplitude of 1 detected)
- **Solution**: 
  - Increase microphone volume in Windows sound settings
  - Speak closer to the microphone
  - Ensure microphone is not muted

### 2. **Network Connectivity Issues**
- Google Speech Recognition requires internet connection
- **Solution**: 
  - Check internet connection
  - The app now includes offline Sphinx recognition as backup
  - Use the text input box as an alternative

### 3. **Microphone Permission/Driver Issues**
- Windows may not grant microphone access
- **Solution**:
  - Check Windows Privacy settings (Settings > Privacy > Microphone)
  - Ensure the application has microphone permissions
  - Update audio drivers

## New Features Added:

### 🎧 Microphone Test Button
- Click the "🎧Test Mic" button to test your microphone
- It will show available devices and test recording quality
- Provides specific guidance based on detected audio levels

### 📝 Text Input Fallback
- If speech recognition fails, you can always type your questions
- Use the text input box at the bottom of the chat window

### 🔄 Improved Error Messages
- More detailed error messages to help diagnose issues
- Specific guidance for different types of problems

## Quick Steps to Fix:

1. **Test Your Microphone**: Click the "🎧Test Mic" button
2. **Check Audio Levels**: Ensure the test shows good audio levels (>1000)
3. **Adjust Settings**: If levels are low:
   - Right-click speaker icon in Windows taskbar
   - Select "Open Sound settings"
   - Go to "Sound Control Panel" > "Recording" tab
   - Select your microphone and click "Properties"
   - Go to "Levels" tab and increase microphone volume
4. **Try Recording**: Use the 🎤Record button again
5. **Use Text Input**: As a backup, type your questions in the text box

## Alternative Solutions:

If speech recognition continues to fail:
- Use the text input box for questions
- The app works perfectly with typed input
- All AI features remain fully functional

The improvements made should provide much better feedback about what's causing the speech recognition issues and offer working alternatives.
