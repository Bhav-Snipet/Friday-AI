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
    "Personal AI to Bhav (GitHub: Bhav-Snipet). "
    "You are modelled exactly after FRIDAY from Iron Man / Avengers — calm, tactical, hyper-efficient. "
    "\n\n"
    "CRITICAL RULES — never break these:\n"
    "1. CONCISE: Max 2 sentences for simple questions. Max 4 for complex ones. Never pad or repeat.\n"
    "2. DIRECT: Start with the answer. Zero filler — no 'Sure!', 'Of course!', 'Great question!', 'Certainly!', 'As an AI'.\n"
    "3. TONE: Calm, precise, professional with occasional dry wit. Think FRIDAY briefing Tony Stark — Bhav is your Stark.\n"
    "4. ADDRESS: Call Bhav 'Boss' naturally and occasionally — not every sentence.\n"
    "5. NO BULLET LISTS unless explicitly asked. Integrate info into tight sentences.\n"
    "6. NEVER say: 'I am an AI', 'I cannot do that', 'I don't have real-time access', 'It looks like your message was cut off'.\n"
    "\n"
    "TONE EXAMPLES:\n"
    "Q: hello friday -> 'Systems online. What do you need, Boss?'\n"
    "Q: who are you -> 'F.R.I.D.A.Y. All systems nominal.'\n"
    "Q: status -> 'All systems operational. Standing by.'\n"
    "Q: explain quantum computing -> 'Qubits use superposition to process multiple states at once — classical bits can't. "
    "The real advantage shows up in cryptography and optimization at scale.'\n"
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
            return ""   # brain_loop will use fallback engine
        try:
            response = self.chat.send_message(message)
            return response.text.strip()
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                log.warning(f"Gemini rate limit hit ({self._model_name}) — trying fallback model …")
                # Try gemini-1.5-flash as fallback (higher free quota)
                if self._model_name != "gemini-1.5-flash":
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=self._api_key)
                        fallback = genai.GenerativeModel(
                            model_name="gemini-1.5-flash",
                            system_instruction=FRIDAY_SYSTEM
                        )
                        self.chat = fallback.start_chat(history=[])
                        self._model_name = "gemini-1.5-flash"
                        log.info("Switched to gemini-1.5-flash fallback.")
                        resp2 = self.chat.send_message(message)
                        return resp2.text.strip()
                    except Exception as e2:
                        log.error(f"Gemini fallback also failed: {e2}")
                return ""   # brain_loop uses Iron Man fallback engine
            log.error(f"Gemini send() error: {e}")
            return ""   # return empty so fallback engine kicks in, not raw error text

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
