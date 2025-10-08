# Voice Input Feature - nQuiry System

## Overview

The Voice Input feature enables hands-free operation of the nQuiry intelligent query processing system. Users can speak their queries instead of typing them, making the system more accessible and convenient to use.

## Features

### 🎤 Voice-to-Text Input
- **Speech Recognition**: Convert spoken queries to text using Google Speech Recognition (online) with offline fallback
- **Microphone Input**: Direct system microphone access for real-time recording
- **Real-time Processing**: Immediate transcription and processing of voice queries
- **Simple Interface**: One-click voice recording with clear visual feedback

### 🔊 Audio Feedback
- **Text-to-Speech Responses**: Optional audio playback of bot responses
- **Configurable Settings**: Enable/disable audio responses per user preference
- **Smart Text Cleaning**: Removes markdown formatting and emojis for better speech synthesis
- **Response Truncation**: Limits audio to key information for better user experience

### 🎯 Enhanced Accessibility
- **Hands-free Operation**: Perfect for users who cannot type or prefer voice interaction
- **Multitasking Support**: Query the system while working on other tasks
- **Disability Support**: Assists users with mobility or visual impairments

## Installation

### 1. Install Dependencies

**Automatic Installation:**
```bash
python install_voice.py
```

**Manual Installation:**
```bash
pip install speechrecognition pyaudio pyttsx3
```

### 2. System-Specific Setup

**Windows:**
- PyAudio should install automatically
- If issues occur, download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install speechrecognition pyaudio pyttsx3
```

**macOS:**
```bash
brew install portaudio
pip install speechrecognition pyaudio pyttsx3
```

### 3. Test Installation
```bash
python test_voice_functionality.py
```

## Usage

### Voice Input Methods

#### Microphone Input
- Click the radio button to select "🎤 Voice"
- Click "🎤 Start Voice Input" button
- Speak your query clearly
- Wait for transcription to complete
- Review the recognized text before submission

### Audio Response Settings
- Check "🔊 Audio Responses" to enable text-to-speech
- Bot responses will be spoken aloud automatically
- Audio can be played alongside text responses

### Best Practices

#### For Optimal Voice Recognition:
- 🎯 **Speak Clearly**: Use normal pace and clear pronunciation
- 🔇 **Minimize Noise**: Use in quiet environments
- 📱 **Good Microphone**: Use quality recording device
- ⏱️ **Pause**: Brief pause before and after speaking
- 🗣️ **Complete Sentences**: Speak in full, structured sentences

#### Example Voice Queries:
- "Create a ticket for database access issue"
- "Help me with JIRA access for new user"
- "I need troubleshooting for deployment problem"
- "How do I reset my password"
- "Grant JIRA access to John Smith"

## Technical Implementation

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Microphone    │───▶│  Speech-to-Text   │───▶│  Query Processor │
│   Input         │    │  Recognition      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│   Audio Output  │◀───│  Text-to-Speech  │◀────────────┘
│   Speaker       │    │  Synthesis       │
└─────────────────┘    └──────────────────┘
```

### Components

#### 1. VoiceInputManager
- **Primary Interface**: Main voice input handling
- **Speech Recognition**: Google Speech Recognition with Sphinx fallback
- **Microphone Management**: Auto-initialization and ambient noise adjustment
- **Error Handling**: Timeout and recognition error management

#### 2. WebRTCVoiceInput  
- **Browser Compatibility**: WebRTC-based recording for web browsers
- **Frame Processing**: Real-time audio frame capture and processing
- **File Export**: Temporary audio file creation for processing

#### 3. Audio Feedback System
- **Text-to-Speech**: pyttsx3-based speech synthesis
- **Response Cleaning**: Markdown and emoji removal for speech
- **Threading**: Non-blocking audio playback
- **Configurable**: User-controlled enable/disable

### Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| speechrecognition | Speech-to-text conversion | ≥3.10.0 |
| pyaudio | Audio input/output interface | ≥0.2.11 |
| pyttsx3 | Text-to-speech synthesis | ≥2.90 |

## Troubleshooting

### Common Issues

#### 1. PyAudio Installation Failed
**Symptoms**: `ERROR: Failed building wheel for pyaudio`

**Solutions**:
- Windows: Download precompiled wheel from UCI repository
- Linux: `sudo apt-get install portaudio19-dev`
- macOS: `brew install portaudio`

#### 2. No Microphone Detected
**Symptoms**: "No microphones found" error

**Solutions**:
- Check microphone is connected and working
- Grant microphone permissions to browser/application
- Restart application after connecting microphone
- Check Windows Sound settings for default recording device

#### 3. Speech Recognition Accuracy Issues
**Symptoms**: Incorrect transcriptions

**Solutions**:
- Speak more clearly and slower
- Move closer to microphone
- Reduce background noise
- Use headset microphone for better quality

#### 4. Audio Playback Not Working
**Symptoms**: No sound from text-to-speech

**Solutions**:
- Check speaker/headphone connections
- Verify system audio settings
- Try different TTS voice in settings
- Restart application

#### 5. WebRTC Not Working in Browser
**Symptoms**: Recording interface not appearing

**Solutions**:
- Use HTTPS (required for microphone access)
- Allow microphone permissions in browser
- Try different browser (Chrome/Firefox recommended)
- Check browser console for errors

### Performance Optimization

#### 1. Response Time
- Use wired microphone for better latency
- Close unnecessary applications
- Ensure stable internet for Google Speech Recognition

#### 2. Accuracy Improvement
- Train with consistent speaking patterns
- Use noise-canceling microphone
- Speak in quiet environment

## Future Enhancements

### Planned Features
- 🌐 **Multi-language Support**: Recognition in different languages
- 🎵 **Voice Commands**: Specific voice shortcuts for common actions
- 🎚️ **Audio Settings**: Voice selection and speed control
- 📊 **Voice Analytics**: Track usage patterns and accuracy
- 🔒 **Voice Authentication**: Optional voice-based user verification

### Integration Possibilities
- 🤖 **AI Voice Assistant**: Natural conversation flow
- 📱 **Mobile App**: Native mobile voice interface
- 🏢 **Enterprise Features**: Custom voice models for technical terms
- 🔌 **API Integration**: Voice capabilities for external applications

## Support

For issues or questions about voice input functionality:

1. **Test Setup**: Run `python test_voice_functionality.py`
2. **Check Dependencies**: Verify all packages are installed
3. **System Requirements**: Ensure microphone and speakers work
4. **Browser Compatibility**: Use Chrome/Firefox for WebRTC features
5. **Documentation**: Review this guide for troubleshooting steps

## Security & Privacy

- **Local Processing**: Speech recognition prefers local processing when possible
- **No Recording Storage**: Audio is processed in real-time, not stored
- **User Control**: All voice features can be disabled
- **Permission-Based**: Requires explicit user permission for microphone access