import streamlit as st
import speech_recognition as sr
import os
import cv2
import time
import numpy as np
import sqlite3
from functools import lru_cache
VIDEO_DIR = r"ISL_VIDEOS"
IDLE_IMAGE = "./idle.png"
SPEED_FACTOR = st.sidebar.slider("Playback Speed Factor", 0.5, 5.0, 0.95)
USE_ML_MORPH = st.sidebar.checkbox("Use ML/AI Morphing Transition", value=True)


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


def recognize_speech():

    recognizer = sr.Recognizer()

    recognizer.energy_threshold = 4000
    recognizer.dynamic_energy_threshold = True
    
    status_placeholder = st.empty()
    status_placeholder.info("Listening...")
    
    with sr.Microphone() as source:
        
        status_placeholder.info("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        status_placeholder.info("Listening... Speak now!")
        
        try:

            audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
            status_placeholder.info("Processing speech...")
            
    
            text = recognizer.recognize_google(audio)
            text = text.upper()
            log_recognized_text(text)
            status_placeholder.success(f"Recognized: {text}")
            return text
        except sr.WaitTimeoutError:
            status_placeholder.error("Listening timed out. Please try again.")
        except sr.UnknownValueError:
            status_placeholder.error("Could not understand audio. Please try again.")
        except sr.RequestError as e:
            status_placeholder.error(f"Request error: {e}. Check your internet connection.")
        except Exception as e:
            status_placeholder.error(f"Error: {str(e)}")
    
    return ""


def resize_frame(frame, width, height):
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)

def blend_frames(frame1, frame2, steps=10):
    blended_frames = []
    if frame1.shape != frame2.shape:
        frame2 = resize_frame(frame2, frame1.shape[1], frame1.shape[0])
    for i in range(steps):
        alpha = i / steps
        blended = cv2.addWeighted(frame1, 1 - alpha, frame2, alpha, 0)
        blended_frames.append(blended)
    return blended_frames

def ml_morph_frames(frame1, frame2, steps=10):
    """
    ML/AI-Inspired Morphing Transition:
    Uses optical flow to compute motion between the last frame (frame1)
    and the first frame (frame2), then warps both images gradually to create a smooth morph.
    """
    if frame1.shape != frame2.shape:
        frame2 = resize_frame(frame2, frame1.shape[1], frame1.shape[0])
    
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY)
    

    flow = cv2.calcOpticalFlowFarneback(
        gray1, gray2, None, 
        pyr_scale=0.5, levels=3, winsize=15, iterations=3, 
        poly_n=5, poly_sigma=1.2, flags=0
    )
    h, w = gray1.shape
    morph_frames = []
    for i in range(steps):
        t = i / steps

        grid_x, grid_y = np.meshgrid(np.arange(w), np.arange(h))
        grid_x = grid_x.astype(np.float32)
        grid_y = grid_y.astype(np.float32)
        

        map_x1 = grid_x + t * flow[..., 0]
        map_y1 = grid_y + t * flow[..., 1]
        warp1 = cv2.remap(frame1, map_x1, map_y1, interpolation=cv2.INTER_LINEAR)
        

        map_x2 = grid_x - (1 - t) * flow[..., 0]
        map_y2 = grid_y - (1 - t) * flow[..., 1]
        warp2 = cv2.remap(frame2, map_x2, map_y2, interpolation=cv2.INTER_LINEAR)
        
        blended = cv2.addWeighted(warp1, 1 - t, warp2, t, 0)
        morph_frames.append(blended)
    return morph_frames

def play_video(video_path, display_area, last_frame=None):
    frames = load_video_frames(video_path)
    if not frames:
        st.warning(f"Video {video_path} has no frames!")
        return last_frame
    
    for frame in frames:
        display_area.image(frame, channels="RGB", use_container_width=True)
        time.sleep(0.02 / SPEED_FACTOR)
    
    if last_frame is not None and last_frame.shape == frames[0].shape:
        if USE_ML_MORPH:
            transition_frames = ml_morph_frames(last_frame, frames[0])
        else:
            transition_frames = blend_frames(last_frame, frames[0])
        for trans_frame in transition_frames:
            display_area.image(trans_frame, channels="RGB", use_container_width=True)
            time.sleep(0.03)
    
    return frames[-1]

def stream_videos(text, display_area):
    last_frame = None
    if not text:
        if os.path.exists(IDLE_IMAGE):
            display_area.image(IDLE_IMAGE, use_container_width=True)
        else:
            display_area.markdown("### Waiting for input...")
        return
    
    word_video_path = os.path.join(VIDEO_DIR, f"{text}.mov")
    if os.path.exists(word_video_path):
        last_frame = play_video(word_video_path, display_area, last_frame)
    else:
        
        for char in text:
            if char == ' ':
                if os.path.exists(IDLE_IMAGE):
                    display_area.image(IDLE_IMAGE, use_container_width=True)
                time.sleep(0.5)
            else:
                letter_video_path = os.path.join(VIDEO_DIR, f"{char}.mov")
                if os.path.exists(letter_video_path):
                    last_frame = play_video(letter_video_path, display_area, last_frame)
                else:
                    st.warning(f"No video found for '{char}'")
    

    if os.path.exists(IDLE_IMAGE):
        display_area.image(IDLE_IMAGE, use_container_width=True)


st.title("Speech to Sign Language Convertor")


if 'listening_active' not in st.session_state:
    st.session_state.listening_active = False
if 'recognized_text' not in st.session_state:
    st.session_state.recognized_text = ""
col1, col2 = st.columns([2, 3])

with col1:
    if st.button("Start Listening"):
        st.session_state.listening_active = True
        recognized_text = recognize_speech()
        if recognized_text:
            st.session_state.recognized_text = recognized_text
            st.rerun()

        else:
            st.session_state.listening_active = False
    

    feedback_text = st.text_input("Or enter text manually:", key="manual_text")
    submit_btn = st.button("Submit Text")
    
  
    if st.button("Reset"):
        st.session_state.recognized_text = ""
        st.session_state.listening_active = False
        st.experimental_rerun()

status_area = st.empty()
if st.session_state.recognized_text:
    status_area.success(f"Recognized: {st.session_state.recognized_text}")
elif st.session_state.listening_active:
    status_area.info("Listening...")
else:
    status_area.info("Ready. Press 'Start Listening' or enter text manually.")

st.markdown("---")
st.markdown("### Sign Language Display")
display_area = st.empty()

if os.path.exists(IDLE_IMAGE) and not st.session_state.listening_active:
    display_area.image(IDLE_IMAGE, use_container_width=True)
else:
    display_area.markdown("### Ready for input...")

if submit_btn and feedback_text:
    corrected_text = feedback_text.upper()
    st.session_state.recognized_text = corrected_text
    log_recognized_text(corrected_text)
    status_area.success(f"Processing: {corrected_text}")
    stream_videos(corrected_text, display_area)


if st.session_state.recognized_text and not st.session_state.listening_active:
    stream_videos(st.session_state.recognized_text, display_area)