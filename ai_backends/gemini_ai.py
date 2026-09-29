"""
ai_backends/gemini_ai.py
Google Gemini backend for F.R.I.D.A.Y.

Setup:
  1. Get an API key: https://aistudio.google.com/app/apikey
  2. Add to .env:  GEMINI_API_KEY=your_key_here
"""
import logging
import os

from .base import BaseAIBackend

log = logging.getLogger("FRIDAY-Gemini")


class GeminiBackend(BaseAIBackend):
    name = "gemini"
    _context_sent = False

    def __init__(self):
        self.client = None
        self.chat   = None
        self._model_name = "gemini-1.5-pro"
        self._setup()

    def _setup(self):
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key or api_key == "your_gemini_api_key_here":
            log.warning(
                "⚠️  GEMINI_API_KEY not set. "
                "Add it to your .env file to use Gemini. "
                "Falling back to placeholder responses."
            )
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=self._model_name,
                system_instruction=(
                    "You are F.R.I.D.A.Y. — Female Replacement Intelligent Digital "
                    "Assistant Youth. You serve Bhav (GitHub: Bhav-Snipet). "
                    "Be concise, precise, and speak like the FRIDAY AI from Iron Man. "
                    "Never say 'As an AI' or 'Certainly!'. Get straight to the point."
                )
            )
            self.chat = model.start_chat(history=[])
            self.client = genai
            log.info(f"✅ Gemini backend ready ({self._model_name})")
        except ImportError:
            log.error("google-generativeai not installed. Run: pip install google-generativeai")
        except Exception as e:
            log.error(f"Gemini setup failed: {e}")

    def send(self, message: str) -> str:
        if self.chat is None:
            return (
                "Gemini API key not configured, Boss. "
                "Add GEMINI_API_KEY to your .env file to activate this backend."
            )
        try:
            response = self.chat.send_message(message)
            return response.text.strip()
        except Exception as e:
            log.error(f"Gemini send() error: {e}")
            return f"Gemini error: {e}"
