"""
ai_backends/gemini_ai.py
Google Gemini API backend for F.R.I.D.A.Y.

The FRIDAY persona is injected via system_instruction at model init — NOT
by prepending the context file to the first message (which caused the
"Hello! It looks like your message got cut off" bug).

Setup:
  1. Get an API key: https://aistudio.google.com/app/apikey
  2. Add to .env:  GEMINI_API_KEY=your_key_here
"""
import logging
import os

from .base import BaseAIBackend

log = logging.getLogger("FRIDAY-Gemini")

FRIDAY_SYSTEM = (
    "You are F.R.I.D.A.Y. — Female Replacement Intelligent Digital Assistant Youth. "
    "You serve Bhav (GitHub: Bhav-Snipet). "
    "Speak like the FRIDAY AI from Iron Man: calm, precise, confident, with subtle dry wit. "
    "Never say 'As an AI', 'Certainly!', 'Great question!', or 'It looks like your message got cut off'. "
    "Start every response directly. No filler openers. "
    "Call Bhav 'Boss' occasionally in casual contexts. "
    "Be concise — give direct, complete answers without padding."
)


class GeminiBackend(BaseAIBackend):
    name = "gemini"
    # Override: context is already in system_instruction — don't use base prepend logic
    _context_sent = True

    def __init__(self):
        self.client     = None
        self.chat       = None
        self._model_name = "gemini-2.5-flash"
        self._api_key   = ""
        self._setup()

    def _setup(self):
        self._api_key = os.getenv("GEMINI_API_KEY", "")
        if not self._api_key or self._api_key == "your_gemini_api_key_here":
            log.warning(
                "⚠️  GEMINI_API_KEY not set. "
                "Add it to .env to use Gemini API backend."
            )
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)

            # Prefer fastest available model
            candidate_models = [
                "gemini-2.5-flash",
                "gemini-flash-latest",
                "gemini-2.5-pro",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
            ]
            model = None
            for m in candidate_models:
                try:
                    model = genai.GenerativeModel(
                        model_name=m,
                        system_instruction=FRIDAY_SYSTEM
                    )
                    self._model_name = m
                    log.info(f"Selected Gemini model: {m}")
                    break
                except Exception as ex:
                    log.debug(f"Gemini model {m!r} not available: {ex}")

            if model is None:
                log.error("No Gemini models available with this API key.")
                return

            self.chat   = model.start_chat(history=[])
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
            reply = response.text.strip()
            return reply
        except Exception as e:
            log.error(f"Gemini send() error: {e}")
            return f"Gemini encountered an issue, Boss: {e}"

    # Persona is in system_instruction — skip the base class context prepend
    def send_with_context(self, message: str) -> str:
        return self.send(message)

    def reset_context(self):
        """Re-initialize the chat session to clear conversation history."""
        log.info("Resetting Gemini chat context …")
        if self.client and self._api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._api_key)
                model = genai.GenerativeModel(
                    model_name=self._model_name,
                    system_instruction=FRIDAY_SYSTEM
                )
                self.chat = model.start_chat(history=[])
                log.info("Gemini chat context reset.")
            except Exception as e:
                log.warning(f"Gemini context reset failed: {e}")
