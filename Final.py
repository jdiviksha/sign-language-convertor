import streamlit as st
import speech_recognition as sr


import os
import cv2
import time
import numpy as np
from googletrans import Translator

# ========== Config ==========
VIDEO_DIR = "ISL_VIDEOS"
IDLE_IMAGE = "idle.png"

# Custom greeting dictionary
custom_greetings = {
    "வணக்கம்": "HELLO",
    "நன்றி": "THANK YOU",
    "நீங்கள் எப்படி இருக்கிறீர்கள்": "HOW ARE YOU",
    "नमस्ते": "HELLO",
    "धन्यवाद": "THANK YOU",
    "ਸਤ ਸ੍ਰੀ ਅਕਾਲ": "HELLO",
    "నమస్తే": "HELLO",
    "ధన్యవాదాలు": "THANK YOU",
    "ನಮಸ್ಕಾರ": "HELLO",
    "ಧನ್ಯವಾದಗಳು": "THANK YOU",
    "હેલો": "HELLO",
    "મહેરબાની": "THANK YOU",
    "ഹലോ": "HELLO",
    "നന്ദി": "THANK YOU",
    "হ্যালো": "HELLO",
    "ধন্যবাদ": "THANK YOU",
    "السلام علیکم": "HELLO",
}

# Supported input languages
language_options = {
    'English': 'en-IN',
    'Hindi': 'hi-IN',
    'Tamil': 'ta-IN',
    'Telugu': 'te-IN',
    'Kannada': 'kn-IN',
    'Malayalam': 'ml-IN',
    'Bengali': 'bn-IN',
    'Gujarati': 'gu-IN',
    'Punjabi': 'pa-IN',
    'Urdu': 'ur-IN',
    'Marathi': 'mr-IN',
}

# ========== App Configuration ==========
st.set_page_config(page_title="Multilingual ISL Translator", layout="wide")

# Session state defaults
if 'recognized_text' not in st.session_state:
    st.session_state.recognized_text = ""
if 'speed_factor' not in st.session_state:
    st.session_state.speed_factor = 1.0
if 'last_frame' not in st.session_state:
    st.session_state.last_frame = None
if 'translation_history' not in st.session_state:
    st.session_state.translation_history = []

# ========== Sidebar Settings ==========
st.sidebar.title("Settings")
lang_name = st.sidebar.selectbox("Choose Input Language", list(language_options.keys()))
lang_code = language_options[lang_name]
st.session_state.speed_factor = st.sidebar.slider("Playback Speed", 0.5, 5.0, 1.0)
use_ml_morph = st.sidebar.checkbox("Use AI/ML Morphing Transition", value=True)

# ========== Video Functions ==========
@st.cache_data(show_spinner=False)
def load_video_frames(video_path):
    """Load video frames from the given file path."""
    cap = cv2.VideoCapture(video_path)
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(frame)
    cap.release()
    return frames

def resize_frame(frame, width, height):
    """Resize a frame to the given width and height."""
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)

def blend_frames(frame1, frame2, steps=10):
    """Create smooth transition between frames using optical flow morphing."""
    if frame1 is None or frame2 is None:
        return []
    
    # Ensure frames have the same dimensions
    if frame1.shape != frame2.shape:
        frame2 = resize_frame(frame2, frame1.shape[1], frame1.shape[0])
    
    # Convert frames to grayscale for optical flow calculation
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY)
    
    # Calculate optical flow using Farneback method
    flow = cv2.calcOpticalFlowFarneback(
        gray1, gray2, None, 
        pyr_scale=0.5,  # Pyramid scale
        levels=3,       # Number of pyramid levels
        winsize=15,     # Window size
        iterations=3,   # Iterations at each pyramid level
        poly_n=5,       # Size of pixel neighborhood
        poly_sigma=1.2, # Standard deviation for polynomial expansion
        flags=0
    )
    
    # Create morphed frames
    h, w = frame1.shape[:2]
    blended_frames = []
    
    for i in range(steps):
        # Calculate interpolation ratio
        t = i / steps
        
        # Create mapping grid for the morphed frame
        map_x = np.tile(np.arange(w, dtype=np.float32), (h, 1))
        map_y = np.tile(np.arange(h, dtype=np.float32).reshape(h, 1), (1, w))
        
        # Apply weighted displacement from the flow
        map_x = map_x - t * flow[..., 0]
        map_y = map_y - t * flow[..., 1]
        
        # Remap pixels from frame1 according to the flow
        warped = cv2.remap(frame1, map_x, map_y, 
                          interpolation=cv2.INTER_LINEAR, 
                          borderMode=cv2.BORDER_REPLICATE)
        
        # Apply cross-dissolve/alpha blending between warped frame1 and frame2
        morphed_frame = cv2.addWeighted(warped, 1.0 - t, frame2, t, 0)
        blended_frames.append(morphed_frame)
    
    return blended_frames

def play_video(video_path, display_area):
    """Play the video corresponding to the recognized word or letter."""
    frames = load_video_frames(video_path)
    if not frames:
        st.warning(f"Video {video_path} has no frames!")
        return None

    first_frame = frames[0]
    
    # Apply transition if enabled and we have a last frame
    if use_ml_morph and st.session_state.last_frame is not None:
        transition_frames = blend_frames(st.session_state.last_frame, first_frame)
        for frame in transition_frames:
            display_area.image(frame, channels="RGB", use_container_width=True)
            time.sleep(0.01 / st.session_state.speed_factor)
    
    # Play the actual video
    for frame in frames:
        display_area.image(frame, channels="RGB", use_container_width=True)
        time.sleep(0.02 / st.session_state.speed_factor)
    
    # Store the last frame for next transition
    st.session_state.last_frame = frames[-1]
    return frames[-1]

def stream_videos(text, display_area):
    """Stream sign language videos based on recognized text."""
    if not text:
        if os.path.exists(IDLE_IMAGE):
            display_area.image(IDLE_IMAGE, use_container_width=True)
        else:
            display_area.markdown("### Waiting for input...")
        return

    for word in text.split():
        word_video_path = os.path.join(VIDEO_DIR, f"{word}.mov")
        if os.path.exists(word_video_path):
            play_video(word_video_path, display_area)
        else:
            # If word video not found, spell it out letter by letter
            for char in word:
                if char.isalpha():
                    letter_video_path = os.path.join(VIDEO_DIR, f"{char}.mov")
                    if os.path.exists(letter_video_path):
                        play_video(letter_video_path, display_area)
                    else:
                        st.warning(f"No video found for '{char}'")
            # Small pause between words when spelling
            time.sleep(0.5)

    # Return to idle state
    if os.path.exists(IDLE_IMAGE):
        display_area.image(IDLE_IMAGE, use_container_width=True)

# ========== Speech Recognition ==========
def recognize_speech(lang_code):
    """Recognize speech from microphone and translate if needed."""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 4000
    recognizer.dynamic_energy_threshold = True
    translator = Translator()
    
    status_placeholder = st.empty()
    status_placeholder.info("🎤 Listening...")

    with sr.Microphone() as source:
        status_placeholder.info("🎤 Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        status_placeholder.info("🎙️ Listening... Speak now!")

        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
            status_placeholder.info("🔍 Processing speech...")

            # Recognize in selected language
            native_text = recognizer.recognize_google(audio, language=lang_code).strip()
            st.write(f"🗣 Original: {native_text}")
            
            # Check if it's in custom greeting dictionary
            if native_text in custom_greetings:
                english_text = custom_greetings[native_text]
                st.success("✅ Matched custom dictionary phrase")
            else:
                # If not English, translate to English
                if lang_code != 'en-IN':
                    translation = translator.translate(native_text, dest='en')
                    english_text = translation.text.upper().strip()
                    st.success(f"🌐 Translated: {english_text}")
                else:
                    english_text = native_text.upper()
            
            # Add to session history instead of database
            timestamp = time.strftime("%H:%M:%S")
            st.session_state.translation_history.insert(0, {
                "timestamp": timestamp,
                "original": native_text,
                "language": lang_name,
                "translated": english_text
            })
            
            # Limit history size
            if len(st.session_state.translation_history) > 10:
                st.session_state.translation_history = st.session_state.translation_history[:10]
                
            status_placeholder.success(f"✅ Recognized: {english_text}")
            return english_text
            
        except sr.WaitTimeoutError:
            status_placeholder.error("⏱️ Listening timed out. Please try again.")
        except sr.UnknownValueError:
            status_placeholder.error("❓ Could not understand audio. Please try again.")
        except sr.RequestError as e:
            status_placeholder.error(f"🌐 Request error: {e}. Check your internet connection.")
        except Exception as e:
            status_placeholder.error(f"❌ Error: {str(e)}")

    return ""

# ========== UI ==========
st.title("🧏‍♀️ Multilingual Speech to Indian Sign Language Translator")
st.markdown("Convert speech from multiple languages to Indian Sign Language")

# Main UI layout
col1, col2 = st.columns([2, 3])

with col1:
    st.markdown("### Input Methods")
    if st.button("🎧 Start Listening", use_container_width=True):
        recognized_text = recognize_speech(lang_code)
        if recognized_text:
            st.session_state.recognized_text = recognized_text
    
    # Manual text input
    manual_text = st.text_input("📝 Or enter text manually:", key="manual_text")
    manual_col1, manual_col2 = st.columns(2)
    
    with manual_col1:
        if st.button("Submit Text", use_container_width=True):
            if manual_text:
                processed_text = manual_text.strip().upper()
                st.session_state.recognized_text = processed_text
                
                # Add manual entry to history
                timestamp = time.strftime("%H:%M:%S")
                st.session_state.translation_history.insert(0, {
                    "timestamp": timestamp,
                    "original": manual_text,
                    "language": "manual",
                    "translated": processed_text
                })
                
                # Limit history size
                if len(st.session_state.translation_history) > 10:
                    st.session_state.translation_history = st.session_state.translation_history[:10]
    
    with manual_col2:
        if st.button("Reset", use_container_width=True):
            st.session_state.recognized_text = ""
            st.session_state.last_frame = None
            st.experimental_rerun()
    
    # History section using session state
    st.markdown("### Recent Translations")
    if st.session_state.translation_history:
        for idx, entry in enumerate(st.session_state.translation_history):
            with st.expander(f"#{idx+1}: {entry['translated']} ({entry['timestamp']})"):
                st.write(f"Original: {entry['original']}")
                st.write(f"Language: {entry['language']}")
                st.write(f"Translated: {entry['translated']}")
                if st.button(f"Play this again", key=f"play_{idx}"):
                    st.session_state.recognized_text = entry['translated']
    else:
        st.info("No translation history yet")

# Status and display area
status_area = st.empty()
if st.session_state.recognized_text:
    status_area.success(f"✅ Current text: {st.session_state.recognized_text}")
else:
    status_area.info("Ready. Press 'Start Listening' or enter text manually.")

st.markdown("---")
st.markdown("### Sign Language Display")
display_area = st.empty()

# Display idle image or start video playback
if not st.session_state.recognized_text:
    if os.path.exists(IDLE_IMAGE):
        display_area.image(IDLE_IMAGE, use_container_width=True)
    else:
        display_area.markdown("### Ready for input...")
else:
    stream_videos(st.session_state.recognized_text, display_area)

# Footer
st.markdown("---")
st.markdown("### About")
st.markdown("""
This application converts speech or text to Indian Sign Language (ISL) videos.
It supports multiple Indian languages with automatic translation to English before 
converting to sign language. You can either speak or type your input.
""")

# Clear button for history
if st.session_state.translation_history:
    if st.button("Clear History"):
        st.session_state.translation_history = []
        st.experimental_rerun()