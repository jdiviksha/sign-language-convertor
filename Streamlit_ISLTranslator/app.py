
import streamlit as st
import speech_recognition as sr
import os
import cv2

st.set_page_config(page_title="Speech to ISL", layout="centered")
st.title("🎤 Real-Time Speech to ISL Translator")

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Please speak into the microphone.")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        st.success(f"✅ Recognized Text: {text}")
        return text
    except sr.UnknownValueError:
        st.error("Could not understand the audio.")
    except sr.RequestError:
        st.error("API unavailable or unresponsive.")
    return ""

def play_video(word):
    path = f"gestures/{word.lower()}.mp4"
    if not os.path.exists(path):
        st.warning(f"No video found for word: '{word}'")
        return
    cap = cv2.VideoCapture(path)
    stframe = st.empty()
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        stframe.image(frame, channels="BGR")
    cap.release()

if st.button("🎙️ Start Speech to ISL"):
    result = recognize_speech()
    if result:
        words = result.split()
        for word in words:
            play_video(word)
