# 🤖 Real-Time Speech to Indian Sign Language (ISL) Converter

A Python-based project that converts **spoken multilingual audio** (like Tamil, Hindi, Bengali) into **Indian Sign Language gestures** using AI, speech recognition, and video generation. Built for accessibility, inclusion, and real-time communication.

---

## 🧩 Features

- 🎤 **Speech-to-Text** (with Google API)
- 🌐 **Multilingual Support** using `TextBlob`
- 🖐️ **Sign Gesture Mapping** to ISL
- 🎞️ **Human Sign Videos** for each word
- ⚙️ Built with **Streamlit** and **OpenCV**
- 💬 Supports real-time speech in **Hindi, Tamil, Telugu, Bengali, English**

---

## 🏗️ Tech Stack

| Component        | Tool Used               |
|------------------|--------------------------|
| Frontend UI      | Streamlit                |
| Speech-to-Text   | SpeechRecognition (Google API) |
| Language Detection | TextBlob / LangDetect    |
| Video Processing | OpenCV                   |
| Sign Gesture DB  | Pre-recorded `.mp4` files |
| Backend Language | Python                   |

---

## 🚀 How to Run

### 🔧 Requirements
```bash
pip install -r requirements.txt
python -m textblob.download_corpora

streamlit run main.py
