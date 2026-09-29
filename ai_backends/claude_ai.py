"""
ai_backends/claude_ai.py
Anthropic Claude backend for F.R.I.D.A.Y.

Setup:
  1. Get an API key: https://console.anthropic.com/
  2. Add to .env:  ANTHROPIC_API_KEY=your_key_here
"""
import logging
import os

from .base import BaseAIBackend

log = logging.getLogger("FRIDAY-Claude")

FRIDAY_SYSTEM = (
    "You are F.R.I.D.A.Y. — Female Replacement Intelligent Digital Assistant Youth. "
    "You serve Bhav (GitHub: Bhav-Snipet). "
    "Speak like the FRIDAY AI from Iron Man: calm, precise, confident, with dry wit. "
    "Never say 'As an AI', 'Certainly!', or 'Great question!'. "
    "Start responses directly. Call Bhav 'Boss' occasionally."
)


class ClaudeBackend(BaseAIBackend):
    name = "claude"
    _context_sent = False

    def __init__(self):
        self.client = None
        self.history = []
        self._model = "claude-3-5-sonnet-20241022"
        self._setup()

    def _setup(self):
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key or api_key == "your_anthropic_api_key_here":
            log.warning(
                "⚠️  ANTHROPIC_API_KEY not set. "
                "Add it to your .env file to use Claude. "
                "Falling back to placeholder responses."
            )
            return
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            log.info(f"✅ Claude backend ready ({self._model})")
        except ImportError:
            log.error("anthropic not installed. Run: pip install anthropic")
        except Exception as e:
            log.error(f"Claude setup failed: {e}")

    def send(self, message: str) -> str:
        if self.client is None:
            return (
                "Claude API key not configured, Boss. "
                "Add ANTHROPIC_API_KEY to your .env file to activate this backend."
            )
        try:
            self.history.append({"role": "user", "content": message})
            response = self.client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=FRIDAY_SYSTEM,
                messages=self.history,
            )
            reply = response.content[0].text.strip()
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            log.error(f"Claude send() error: {e}")
            return f"Claude error: {e}"

    def reset_context(self):
        super().reset_context()
        self.history = []  # clear Claude's message history too
