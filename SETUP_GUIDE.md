# F.R.I.D.A.Y. — Agent Activation Setup Guide
# Created by Bhav-Snipet

All AI backends work the same way as Pi.ai — you log in once via a visible
browser, the session is saved, then FRIDAY runs fully headless forever after.

No API keys needed for any of them (unless you prefer the API route).

---

## How the Session System Works

Each backend saves its login session in its own folder:

```
sessions/
  piai/       ← Pi.ai session (already done ✅)
  gemini/     ← Google Gemini session
  claude/     ← Claude (Anthropic) session
  chatgpt/    ← ChatGPT (OpenAI) session
```

Once a session is saved, headless mode works forever (until the site logs
you out, which is rare — usually months).

---

## STEP-BY-STEP: Activating Each Agent

### ✅ Pi.ai — Already Active
Your session is already saved. Nothing to do.

---

### 🔵 Google Gemini

**Account needed:** Any Google account (gmail.com works)

**Step 1** — Open `logic_brain.py`, find this line:
```python
_load_backend(_active_ai_name)
```
Above it, temporarily set:
```python
_SETUP_HEADLESS = False   # SET THIS → False for setup
```
**Actually the easier way:** Edit `ai_backends/__init__.py` → `get_backend()`:
```python
# Change this temporarily:
return cls(headless=True)
# To:
return cls(headless=False)
```

**Step 2** — Click **Gemini** button in the FRIDAY HUD  
OR set `ACTIVE_AI=gemini` in your `.env` and restart

**Step 3** — A Chrome window opens at `gemini.google.com`  
→ Sign in with your Google account  
→ Wait until you see the chat interface  

**Step 4** — Close FRIDAY (`Ctrl+C` in terminal)

**Step 5** — Revert `headless=False` back to `headless=True`

**Step 6** — `python Friday.py` — Gemini now works headless ✅

---

### 🟡 Claude (Anthropic)

**Account needed:** Free account at https://claude.ai

**Step 1** — Create account at https://claude.ai (free tier available)

**Step 2** — Temporarily set `headless=False` in `ai_backends/__init__.py`  
(same as Gemini step 1 above)

**Step 3** — Click **Claude** button in FRIDAY HUD  
OR set `ACTIVE_AI=claude` and restart

**Step 4** — Chrome opens at `claude.ai/new`  
→ Sign in (Google, email, etc.)  
→ Wait until you see the chat input  

**Step 5** — Close FRIDAY, revert to `headless=True`, restart ✅

---

### 🟢 ChatGPT (OpenAI)

**Account needed:** Free account at https://chat.openai.com

**Step 1** — Create account at https://chat.openai.com (free tier: GPT-4o mini)

**Step 2** — Temporarily set `headless=False` (same process as above)

**Step 3** — Click **ChatGPT** button in FRIDAY HUD

**Step 4** — Chrome opens at `chat.openai.com`  
→ Sign in  
→ Wait for chat interface  

**Step 5** — Close FRIDAY, revert `headless=True`, restart ✅

---

## Quick Setup Flag (Easier Method)

Instead of editing `__init__.py` every time, add this to your `.env`:

```env
# Set to "true" to run ALL backends in visible mode for login
FRIDAY_SETUP_MODE=false
```

Then in `ai_backends/__init__.py` the `get_backend()` function reads this:
```python
import os
headless = os.getenv("FRIDAY_SETUP_MODE", "false").lower() != "true"
return cls(headless=headless)
```

So to do first-time login for any backend:
1. Set `FRIDAY_SETUP_MODE=true` in `.env`
2. Start FRIDAY, click the agent button, log in
3. Close FRIDAY
4. Set `FRIDAY_SETUP_MODE=false` in `.env`
5. Done — runs headless forever ✅

---

## API Key Alternative (Optional)

If you prefer using API keys instead of browser login:

| Backend   | .env key            | Code backend name |
|-----------|--------------------|--------------------|
| Gemini    | `GEMINI_API_KEY`    | `gemini_api`       |
| Claude    | `ANTHROPIC_API_KEY` | `claude_api`       |
| ChatGPT   | `OPENAI_API_KEY`    | `chatgpt_api`      |

Get keys:
- Gemini: https://aistudio.google.com/app/apikey (FREE)
- Claude: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/api-keys

Set in `.env`:
```env
GEMINI_API_KEY=AIza...
ACTIVE_AI=gemini_api
```

---

## Switching AI Live (No Restart)

Click any button in the FRIDAY HUD:
```
[ Pi.ai ]  [ Gemini ]  [ Claude ]  [ ChatGPT ]
```
FRIDAY switches instantly. The new backend loads and submits the FRIDAY
context briefing on its first message so it knows who Bhav is.

---

## Files

| File | Purpose |
|------|---------|
| `sessions/piai/`    | Pi.ai Chrome session |
| `sessions/gemini/`  | Gemini Chrome session |
| `sessions/claude/`  | Claude Chrome session |
| `sessions/chatgpt/` | ChatGPT Chrome session |
| `FRIDAY_CONTEXT.txt` | Briefing sent to AI on first message |
| `.env`              | API keys + active backend config |

> ⚠️ Never commit `sessions/` or `.env` to GitHub (already in `.gitignore`)
