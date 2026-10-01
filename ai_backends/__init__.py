"""
ai_backends/__init__.py
AI backend registry for F.R.I.D.A.Y.

Backends:
  piai    → Pi.ai        (Selenium, login-based)
  gemini  → Google Gemini (Selenium, login-based)
  claude  → Claude        (Selenium, login-based)
  chatgpt → ChatGPT       (Selenium, login-based)

API-key backends (optional, if you prefer):
  gemini_api → Gemini API key
  claude_api → Claude API key
  gpt_api    → OpenAI API key
"""
from .pi_ai              import PiAIBackend
from .gemini_selenium    import GeminiSeleniumBackend
from .claude_selenium    import ClaudeSeleniumBackend
from .chatgpt_selenium   import ChatGPTSeleniumBackend

# Optional API-key backends
from .gemini_ai  import GeminiBackend
from .claude_ai  import ClaudeBackend
from .openai_ai  import OpenAIBackend

BACKENDS = {
    # ── Selenium (browser login) ──────────────────────────
    "piai":    PiAIBackend,
    "gemini":  GeminiSeleniumBackend,
    "claude":  ClaudeSeleniumBackend,
    "chatgpt": ChatGPTSeleniumBackend,

    # ── API key based (optional) ──────────────────────────
    "gemini_api":  GeminiBackend,
    "claude_api":  ClaudeBackend,
    "chatgpt_api": OpenAIBackend,
}


def get_backend(name: str, headless: bool = True):
    import os
    import logging
    log = logging.getLogger('FRIDAY-BACKENDS')

    target_name = name.lower()

    # ── API Key Routing (instant — no browser needed) ─────────────────────────
    # Only intercepts "gemini"/"chatgpt" if API key exists.
    # "piai" and "claude" always use their Selenium backends.
    if target_name in ["gemini", "gemini_api"] and os.getenv("GEMINI_API_KEY"):
        log.info("⚡ [GEMINI API] — using API key backend (no browser)")
        return GeminiBackend()

    if target_name in ["chatgpt", "chatgpt_api", "gpt_api"] and os.getenv("OPENAI_API_KEY"):
        log.info("⚡ [CHATGPT API] — using API key backend (no browser)")
        return OpenAIBackend()

    # ── Selenium Browser Backends ─────────────────────────────────────────────
    if os.getenv("FRIDAY_SETUP_MODE", "false").lower() == "true":
        headless = False
        log.info("🔓 SETUP MODE: headless=False (set FRIDAY_SETUP_MODE=false when done)")

    cls = BACKENDS.get(target_name)
    if not cls:
        raise ValueError(
            f"Unknown backend: {name!r}. "
            f"Available: {list(BACKENDS.keys())}"
        )

    log.info(f"🌐 [{target_name.upper()}] — using Selenium browser backend")
    try:
        return cls(headless=headless)
    except TypeError:
        return cls()

