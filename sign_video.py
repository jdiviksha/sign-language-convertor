import streamlit as st
import os
import cv2
import time
from gtts import gTTS
import tempfile

# Configuration
VIDEO_INPUT_DIR = "ISL_VIDEOS"

st.set_page_config(page_title="Sign Video to Speech", layout="centered")
st.title("🎬 Sign Video to Speech Translator")

# Helper: Play video
def play_video(path, frame_area):
    cap = cv2.VideoCapture(path)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_area.image(frame, channels="BGR", use_container_width=True)
        time.sleep(0.03)
    cap.release()

# Helper: Speak text using gTTS
def speak_text(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        st.audio(fp.name, format='audio/mp3')

# Load available sign videos
video_files = [f for f in os.listdir(VIDEO_INPUT_DIR) if f.endswith((".mp4", ".mov"))]
video_labels = [os.path.splitext(f)[0].upper() for f in video_files]

# Sidebar - Select video
selected_label = st.selectbox("📁 Select a Sign Video", video_labels)
selected_video = os.path.join(VIDEO_INPUT_DIR, selected_label + ".mov")

if st.button("▶️ Play and Speak"):
    st.subheader(f"🔤 Detected Sign: {selected_label}")
    frame_area = st.empty()
    play_video(selected_video, frame_area)

    # Convert filename to spoken word
    text_to_speak = selected_label.replace("_", " ")
    st.success(f"🗣 Speaking: {text_to_speak}")
    speak_text(text_to_speak)
