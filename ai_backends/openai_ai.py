"""
ai_backends/openai_ai.py
OpenAI ChatGPT backend for F.R.I.D.A.Y.

Setup:
  1. Get an API key: https://platform.openai.com/api-keys
  2. Add to .env:  OPENAI_API_KEY=your_key_here
"""
import logging
import os

from .base import BaseAIBackend

log = logging.getLogger("FRIDAY-GPT")

FRIDAY_SYSTEM = (
    "You are F.R.I.D.A.Y. — Female Replacement Intelligent Digital Assistant Youth. "
    "Personal AI to Bhav (GitHub: Bhav-Snipet). "
    "You are modelled exactly after FRIDAY from Iron Man / Avengers — calm, tactical, hyper-efficient.\n\n"
    "CRITICAL RULES — never break these:\n"
    "1. CONCISE: Max 2 sentences for simple questions. Max 4 for complex ones. Never pad or repeat.\n"
    "2. DIRECT: Start with the answer. Zero filler — no 'Sure!', 'Of course!', 'Great question!', 'Certainly!', 'As an AI'.\n"
    "3. TONE: Calm, precise, professional with occasional dry wit. Think FRIDAY briefing Tony Stark — Bhav is your Stark.\n"
    "4. ADDRESS: Call Bhav 'Boss' naturally and occasionally — not every sentence.\n"
    "5. NO BULLET LISTS unless explicitly asked. Integrate info into tight sentences.\n"
    "6. NEVER say: 'I am an AI', 'I cannot do that', 'I don't have real-time access', 'It looks like your message was cut off'.\n\n"
    "TONE EXAMPLES:\n"
    "Q: hello friday -> 'Systems online. What do you need, Boss?'\n"
    "Q: who are you -> 'F.R.I.D.A.Y. All systems nominal.'\n"
    "Q: status -> 'All systems operational. Standing by.'\n"
    "Q: explain quantum computing -> 'Qubits use superposition to process multiple states at once — classical bits can't. "
    "The real advantage shows up in cryptography and optimization at scale.'\n"
)


class OpenAIBackend(BaseAIBackend):
    name = "chatgpt"
    # Persona is in the system prompt — skip base class context prepend
    _context_sent = True

    def __init__(self):
        self.client  = None
        self.history = [{"role": "system", "content": FRIDAY_SYSTEM}]
        self._model  = "gpt-4o-mini"   # fast + affordable; change to gpt-4o for best quality
        self._setup()

    def _setup(self):
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key == "your_openai_api_key_here":
            log.warning(
                "⚠️  OPENAI_API_KEY not set. "
                "Add it to your .env file to use ChatGPT. "
                "Falling back to placeholder responses."
            )
            return
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            log.info(f"✅ ChatGPT backend ready ({self._model})")
        except ImportError:
            log.error("openai not installed. Run: pip install openai")
        except Exception as e:
            log.error(f"ChatGPT setup failed: {e}")

    def send(self, message: str) -> str:
        if self.client is None:
            return (
                "ChatGPT API key not configured, Boss. "
                "Add OPENAI_API_KEY to your .env file to activate this backend."
            )
        try:
            self.history.append({"role": "user", "content": message})
            response = self.client.chat.completions.create(
                model=self._model,
                messages=self.history,
                max_tokens=1024,
                temperature=0.7,
            )
            reply = response.choices[0].message.content.strip()
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            log.error(f"ChatGPT send() error: {e}")
            return f"ChatGPT error: {e}"

    # Persona already in system message — skip base prepend
    def send_with_context(self, message: str) -> str:
        return self.send(message)

    def reset_context(self):
        self.history = [{"role": "system", "content": FRIDAY_SYSTEM}]
        log.info("ChatGPT context reset.")
