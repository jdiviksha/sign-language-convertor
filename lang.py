import streamlit as st
import speech_recognition as sr
import os
import cv2
import time
import numpy as np
from googletrans import Translator
import sqlite3

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

# ========== Database ==========
def init_db():
    conn = sqlite3.connect("translation_log.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    recognized_text TEXT)''')
    conn.commit()
    return conn

conn = init_db()

def log_recognized_text(text):
    c = conn.cursor()
    c.execute("INSERT INTO logs (recognized_text) VALUES (?)", (text,))
    conn.commit()

# ========== Video Loading ==========
@st.cache_data(show_spinner=False)
def load_video_frames(video_path):
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

def play_video(video_path, display_area):
    frames = load_video_frames(video_path)
    if not frames:
        st.warning(f"Video not found or empty: {video_path}")
        return
    for frame in frames:
        display_area.image(frame, channels="RGB", use_container_width=True)
        time.sleep(0.02 / st.session_state.speed_factor)

# ========== Speech Recognition ==========
def recognize_speech(lang_code):
    recognizer = sr.Recognizer()
    translator = Translator()
    status_placeholder = st.empty()

    with sr.Microphone() as source:
        status_placeholder.info("🎤 Adjusting for noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        status_placeholder.info("🎙️ Speak now...")

        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=6)
            native_text = recognizer.recognize_google(audio, language=lang_code).strip()
            st.write(f"🗣 Native Speech: {native_text}")

            # Custom greeting override
            if native_text in custom_greetings:
                english_text = custom_greetings[native_text]
                st.success("✅ Matched custom dictionary")
            else:
                translation = translator.translate(native_text, dest='en')
                english_text = translation.text.upper().strip()
                st.success(f"🌐 Translated: {english_text}")

            log_recognized_text(english_text)
            return english_text

        except sr.UnknownValueError:
            status_placeholder.error("❌ Could not understand the speech.")
        except sr.RequestError as e:
            status_placeholder.error(f"❌ API error: {e}")
        except Exception as e:
            status_placeholder.error(f"❌ Error: {str(e)}")

    return ""

# ========== Sign Language Display ==========
def stream_videos(text, display_area):
    if not text:
        if os.path.exists(IDLE_IMAGE):
            display_area.image(IDLE_IMAGE, use_container_width=True)
        else:
            display_area.markdown("Waiting for input...")
        return

    for word in text.split():
        word_video = os.path.join(VIDEO_DIR, f"{word}.mov")
        if os.path.exists(word_video):
            play_video(word_video, display_area)
        else:
            for char in word:
                if char.isalpha():
                    letter_video = os.path.join(VIDEO_DIR, f"{char.upper()}.mov")
                    if os.path.exists(letter_video):
                        play_video(letter_video, display_area)
                    else:
                        st.warning(f"No video for letter: {char.upper()}")
            time.sleep(0.5)

    if os.path.exists(IDLE_IMAGE):
        display_area.image(IDLE_IMAGE, use_container_width=True)

# ========== UI ==========
st.set_page_config(page_title="ISL Translator", layout="centered")
st.title("🧏‍♀️ Indian Language Speech to Sign Language")

# Session state defaults
if 'recognized_text' not in st.session_state:
    st.session_state.recognized_text = ""
if 'speed_factor' not in st.session_state:
    st.session_state.speed_factor = 1.0

# Sidebar settings
st.sidebar.title("Settings")
lang_name = st.sidebar.selectbox("Choose Input Language", list(language_options.keys()))
lang_code = language_options[lang_name]
st.session_state.speed_factor = st.sidebar.slider("Playback Speed", 0.5, 3.0, 1.0)

# Main UI
col1, col2 = st.columns([2, 3])
display_area = st.empty()

with col1:
    if st.button("🎧 Start Listening"):
        result = recognize_speech(lang_code)
        if result:
            st.session_state.recognized_text = result
            stream_videos(result, display_area)

    manual = st.text_input("📝 Or enter text manually:")
    if st.button("Submit Text"):
        manual_text = manual.strip().upper()
        st.session_state.recognized_text = manual_text
        log_recognized_text(manual_text)
        stream_videos(manual_text, display_area)

    if st.button("🔁 Reset"):
        st.session_state.recognized_text = ""
        st.experimental_rerun()

# Status and Display
status = st.empty()
if st.session_state.recognized_text:
    status.success(f"✅ Text: {st.session_state.recognized_text}")
else:
    status.info("Waiting for input...")

if not st.session_state.recognized_text:
    if os.path.exists(IDLE_IMAGE):
        display_area.image(IDLE_IMAGE, use_container_width=True)
    else:
        display_area.markdown("🧏 Ready to translate speech to ISL.")
