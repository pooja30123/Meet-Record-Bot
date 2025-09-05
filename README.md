# 🚀 Google Meet Recording & Transcription Bot 🤖

![GitHub release (latest by date)](https://img.shields.io/github/v/release/pooja30123/google-meet-bot?color=orange)  
![GitHub license](https://img.shields.io/github/license/pooja30123/google-meet-bot?color=green)  
![Python](https://img.shields.io/badge/python-3.8%2B-blue)  
![Platforms](https://img.shields.io/badge/platform-windows-yellow)

---

## 📌 Overview

Automated, silent Google Meet recorder that joins meetings, captures system audio, and generates professional AI-powered transcripts with speaker diarization.

---

## ✨ Features

- **🤖 Auto-join Google Meet** (no manual intervention)
- **🔇 Silent & invisible** (muted mic, disabled camera, green mic indicator up)
- **🎧 Stereo Mix recording** (captures all meeting audio)
- **📝 AI Transcription** (AssemblyAI Premium + OpenAI Whisper fallback)
- **👥 Speaker diarization** (who said what?)
- **📂 Automatic output** (audio & transcripts saved in `/outputs`)

---

## 🎥 Demo Video

See the bot in action! [Watch on YouTube](https://youtu.be/CqdJRwgY1to) 

---

## 💻 Installation

### Prerequisites
- **Python 3.8+**
- **Chrome browser** (latest stable)
- **ChromeDriver** (same Chrome version)
- **AssemblyAI API key** (get yours [here](https://www.assemblyai.com/))
- **Windows**: Enable "Stereo Mix" in Sound settings

---

### Quick Setup

```
git clone https://github.com/pooja30123/google-meet-bot.git
cd google-meet-bot
python -m venv venv

Windows
venv\Scripts\activate

macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
echo ASSEMBLYAI_API_KEY=your_api_key_here > .env

Download ChromeDriver from https://chromedriver.chromium.org/downloads (same Chrome version)
```

**Enable Stereo Mix:**  
Right-click speaker icon → Sounds → Recording → Enable "Stereo Mix" → Properties → Listen → "Listen to this device" (tick).

---

## ▶️ Usage

```
python main.py
```

Paste your Google Meet URL (with `https://`) when prompted.

---

## 📂 Project Structure

```
├── main.py # Application entry
├── GoogleMeetBot.py # Meet automation
├── TranscriptionService.py # AI transcription
├── requirements.txt # Python requirements
├── .env # API key (don't share!)
├── outputs/
│ ├── audio/ # Recorded audio (.wav)
│ └── transcripts/ # Transcripts (.txt)
├── chromedriver.exe # ChromeDriver (optional)
└── README.md
```

---

## 🛠️ Troubleshooting

- **No audio?**  
  Enable Stereo Mix, run terminal as Administrator (Windows)
- **Bot can't join?**  
  Use full URL: `https://meet.google.com/abc-defg-hij`
- **AssemblyAI/Selenium errors?**  
  Check API key, Chrome/ChromeDriver version, firewall
- **Need help?**  
  Open an issue on GitHub

---

## ⚖️ License

MIT

---

## ❤️ Acknowledgments

Special thanks to [AssemblyAI](https://www.assemblyai.com/), [OpenAI Whisper](https://github.com/openai/whisper), and [Selenium](https://www.selenium.dev/).

---

## 👤 Author

**Pooja Verma**  
[GitHub](https://github.com/pooja30123) | poojaverma300702@gmail.com

---

⭐ **If this repo helped you, please star it!** ⭐



