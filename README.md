<div align="center">

```
███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗
██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝
█████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝ 
██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝  
██║     ██║  ██║██║██████╔╝██║  ██║   ██║   
╚═╝     ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝  
```

**Female Replacement Intelligent Digital Assistant Youth**

*Built by [Bhav-Snipet](https://github.com/Bhav-Snipet)*

![Python](https://img.shields.io/badge/Python-3.14-blue?style=flat-square&logo=python)
![Selenium](https://img.shields.io/badge/Selenium-4.49-green?style=flat-square&logo=selenium)
![Status](https://img.shields.io/badge/Status-ONLINE-brightgreen?style=flat-square)
![AI](https://img.shields.io/badge/AI-Pi.ai%20%7C%20Gemini%20%7C%20Claude-cyan?style=flat-square)

</div>

---

## What is FRIDAY?

FRIDAY is a voice-controlled AI assistant modelled after the AI from Iron Man. It listens for your voice, sends your queries to an AI backend, speaks the response aloud, and displays everything on a holographic HUD.

**Say "Friday…"** followed by your question — she does the rest.

---

## Features

- 🎤 **Voice input** via browser Speech-to-Text (Selenium → Netlify)
- 🤖 **Multi-AI switching** — Pi.ai, Google Gemini, Anthropic Claude
- 🗣️ **Text-to-speech** output (pyttsx3, female voice)
- 🖥️ **Holographic HUD** — Jarvis-style animated UI (Eel + Chrome)
- 📋 **Context log** — FRIDAY introduces herself to each AI on first launch
- 🔇 **Headless mode** — runs silently in the background after first setup

---

## Architecture

```
Friday.py          → Entry point · Eel UI + thread orchestration
logic_brain.py     → Brain loop · wake-word · TTS · AI backend routing
STT.py             → Selenium → Netlify STT page → web/input.txt
ai_backends/
  ├── pi_ai.py     → Selenium → pi.ai/talk (no API key needed)
  ├── gemini_ai.py → Google Gemini API (gemini-1.5-pro)
  └── claude_ai.py → Anthropic Claude API (claude-3-5-sonnet)
web/index.html     → Holographic FRIDAY HUD
FRIDAY_CONTEXT.txt → System briefing submitted to AI on first launch
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API keys (optional)
```bash
cp .env.example .env
# Edit .env and add your Gemini/Claude keys
```

### 3. First-time login (Pi.ai)
In `logic_brain.py` change:
```python
init_driver(headless=True)   →   _load_backend("piai")  # headless=False in pi_ai.py
```
Run `python Friday.py`, log in to pi.ai in the browser, then revert.

### 4. Run
```bash
python Friday.py
```

Say **"Friday, what's the weather like?"** — she'll answer.

---

## AI Backends

| Backend | Key Required | Notes |
|---------|-------------|-------|
| **Pi.ai** | ❌ None | Session saved in `chromedata/` after first login |
| **Gemini** | ✅ `GEMINI_API_KEY` | [Get key](https://aistudio.google.com/app/apikey) |
| **Claude** | ✅ `ANTHROPIC_API_KEY` | [Get key](https://console.anthropic.com/) |

Switch AI live from the HUD — no restart needed.

---

## ⚠️ Notes

- `pyaudio` requires **Microsoft C++ Build Tools** on Windows (Python 3.14)
- Pi.ai Selenium automation may violate their ToS — use at your own risk
- `chromedata/` contains login cookies — never commit this folder

---

<div align="center">
  <sub>© Bhav-Snipet · <a href="https://github.com/Bhav-Snipet/Friday-AI">github.com/Bhav-Snipet/Friday-AI</a></sub>
</div>
