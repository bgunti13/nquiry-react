"""
Voice Input Module for nQuiry System
Provides speech-to-text functionality for hands-free query input
"""

import streamlit as st
import speech_recognition as sr
import threading
import queue
import time
from typing import Optional, Tuple

class VoiceInputManager:
    """Manages voice input and speech-to-text conversion"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_listening = False
        self.audio_queue = queue.Queue()
        
        # Configure recognition parameters
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.operation_timeout = None
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.8
        
    def initialize_microphone(self) -> bool:
        """Initialize microphone for speech recognition"""
        try:
            self.microphone = sr.Microphone()
            # Adjust for ambient noise
            with self.microphone as source:
                st.info("🎤 Adjusting for ambient noise... Please wait.")
                self.recognizer.adjust_for_ambient_noise(source)
            return True
        except Exception as e:
            st.error(f"❌ Failed to initialize microphone: {e}")
            return False
    
    def listen_for_speech(self, timeout: float = 5.0, phrase_time_limit: float = 30.0) -> Optional[str]:
        """
        Listen for speech and convert to text
        
        Args:
            timeout: Time to wait for speech to start
            phrase_time_limit: Maximum time for a single phrase
            
        Returns:
            Recognized text or None if failed
        """
        if not self.microphone:
            if not self.initialize_microphone():
                return None
        
        try:
            with self.microphone as source:
                st.info("🎤 Listening... Speak your query now!")
                
                # Listen for audio
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
                
                st.info("🔄 Processing speech...")
                
                # Try Google Speech Recognition first
                try:
                    text = self.recognizer.recognize_google(audio)
                    return text
                except sr.RequestError:
                    # Fallback to offline recognition
                    try:
                        text = self.recognizer.recognize_sphinx(audio)
                        return text
                    except:
                        st.error("❌ Offline speech recognition not available")
                        return None
                        
        except sr.WaitTimeoutError:
            st.warning("⏰ No speech detected within timeout period")
            return None
        except sr.UnknownValueError:
            st.warning("❓ Could not understand the speech")
            return None
        except Exception as e:
            st.error(f"❌ Error during speech recognition: {e}")
            return None
    
    def create_voice_interface(self) -> Optional[str]:
        """
        Create Streamlit interface for voice input
        
        Returns:
            Recognized text or None
        """
        # Auto-start recording when this component is called
        if 'voice_recording_started' not in st.session_state:
            st.session_state.voice_recording_started = True
            
            # Show recording status
            st.info("🎤 Listening... Speak your query now!")
            
            # Start recording immediately
            recognized_text = self.listen_for_speech()
            
            if recognized_text:
                st.session_state.voice_text = recognized_text
                st.success(f"✅ Voice recognized: {recognized_text}")
                # Reset the flag so it can record again next time
                st.session_state.voice_recording_started = False
                return recognized_text
            else:
                st.warning("❓ No speech detected or could not understand. Try again.")
                st.session_state.voice_text = ""
                st.session_state.voice_recording_started = False
                return None
        
        return st.session_state.get('voice_text', None)

def create_voice_input_component() -> Optional[str]:
    """
    Main function to create voice input component
    Returns recognized text or None
    """
    voice_manager = VoiceInputManager()
    recognized_text = voice_manager.create_voice_interface()
    
    return recognized_text

def add_voice_tips():
    """Add helpful tips for voice input"""
    with st.expander("💡 Voice Input Tips"):
        st.markdown("""
        **For best results:**
        - 🎯 Speak clearly and at normal pace
        - 🔇 Minimize background noise
        - 📱 Use a good quality microphone
        - ⏱️ Pause briefly before and after speaking
        - 🗣️ Speak in complete sentences
        
        **Example queries:**
        - "Create a ticket for database access issue"
        - "Help me with JIRA access for new user"
        - "I need troubleshooting for deployment problem"
        """)

# Text-to-speech for responses (bonus feature)
def speak_response(text: str):
    """Convert text response to speech (optional feature)"""
    try:
        import pyttsx3
        
        if 'tts_engine' not in st.session_state:
            st.session_state.tts_engine = pyttsx3.init()
            # Configure speech rate and voice
            st.session_state.tts_engine.setProperty('rate', 150)
        
        # Speak the text
        st.session_state.tts_engine.say(text)
        st.session_state.tts_engine.runAndWait()
        
    except ImportError:
        st.info("💡 Install pyttsx3 for text-to-speech: pip install pyttsx3")
    except Exception as e:
        st.error(f"Error in text-to-speech: {e}")