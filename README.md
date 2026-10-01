# 🤖 F.R.I.D.A.Y. AI — Voice Assistant & Multi-Agent Intelligence
> **"Boss, quantum eigenstate simulation complete. All systems nominal."**
> 
> *Created by [Bhav-Snipet](https://github.com/Bhav-Snipet/Friday-AI.git) • Powered by F.R.I.D.A.Y. AI*

---

## 🌟 Overview & Long-Term Support (LTS) Architecture

**F.R.I.D.A.Y.** is an enterprise-grade, Iron Man-inspired voice intelligence system engineered for **Long-Term Support (LTS)**. It features real-time Speech-to-Text (STT), Text-to-Speech (TTS), an interactive dynamic web HUD dashboard, and multi-model AI agent switching (Pi.ai, Google Gemini, Anthropic Claude, OpenAI ChatGPT).

---

## ✨ Key Features & Controls

- 🎙️ **Instant Mic / Mute Controls**: Direct instant voice capture with immediate submit on Mute toggle (0 ms registration delay).
- 🌙 **Sleep & Wake Modes**: Voice commands (`"Friday, go to sleep"`, `"Friday, wake up"`) and single-click UI sleep mode.
- 🛑 **Clean System Shutdown**: Voice command (`"Friday, shutdown"`) and top-bar UI shutdown button to cleanly terminate background processes.
- 🔒 **Strict "Friday" Keyword Protection**: Responds **ONLY** when queries explicitly contain the keyword `"friday"`.
- ⚡ **Multi-Agent AI Switcher**: Seamlessly switch between **Pi.ai**, **Google Gemini**, **Anthropic Claude**, **OpenAI ChatGPT**, or direct API backends from the UI.
- 🌐 **No API Key Required (Selenium Login Mode)**: Persistent session cookies saved under `sessions/<backend>/` in headless Chrome.
- 🛡️ **Self-Healing LTS Engine**: Automatic browser recovery and dynamic `selectors.json` configuration for 100% uptime.

---

## 🧪 Spoken Technical Voice Commands & Controls

| Voice Command / Query | Action / F.R.I.D.A.Y. Response |
|-----------------------|--------------------------------|
| *"Friday, go to sleep"* | Puts F.R.I.D.A.Y into Sleep Mode (pauses listening, dims HUD). |
| *"Friday, wake up"* | Wakes F.R.I.D.A.Y up from standby into operational state. |
| *"Friday, shutdown"* | Cleanly shuts down all F.R.I.D.A.Y backend engines and browser sessions. |
| *"Friday, run a quantum eigenstate simulation on the Möbius strip configuration."* | *"Boss, quantum eigenstate simulation complete. 99.4% topological coherence maintained."* |
| *"Friday, analyze the gold-titanium nanoparticle lattice density for Mark LXXXV armor."* | *"Structural integrity confirms micro-thrusters can be safely boosted by 14%."* |

---

## 🚀 Quick Setup & Usage

### 1. Installation
```bash
git clone https://github.com/Bhav-Snipet/Friday-AI.git
cd Friday-AI
pip install -r requirements.txt
```

### 2. One-Time Browser Login (Setup Mode)
To log into your AI accounts (Gemini, Claude, ChatGPT, Pi.ai) visually:
```bash
$env:FRIDAY_SETUP_MODE="true"   # PowerShell
python Friday.py
```
Log into your account in the browser window. Cookies save to `sessions/<agent>/`.

### 3. Run F.R.I.D.A.Y. Headless
```bash
python Friday.py
```
Open **`http://localhost:8090`** in your browser.

---

## 🏷️ Credits & Watermark

Developed & Maintained by **[Bhav-Snipet](https://github.com/Bhav-Snipet/Friday-AI.git)**  
*Watermark: `Powered by F.R.I.D.A.Y. AI • Created by Bhav-Snipet`*
