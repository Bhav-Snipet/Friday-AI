"""
ai_backends/base.py
Abstract base class for all FRIDAY AI backends.
"""
from abc import ABC, abstractmethod
import pathlib

CONTEXT_FILE = pathlib.Path(__file__).parent.parent / "FRIDAY_CONTEXT.txt"


class BaseAIBackend(ABC):
    """Every AI backend must implement send() and optionally init_context()."""

    name: str = "base"
    _context_sent: bool = False

    def _load_context(self) -> str:
        try:
            return CONTEXT_FILE.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    @abstractmethod
    def send(self, message: str) -> str:
        """Send a message and return the AI's response as a string."""
        ...

    def send_with_context(self, message: str) -> str:
        """
        On first call: prepend the FRIDAY context log to the message
        so the AI knows who Bhav is and how to behave.
        """
        if not self.__class__._context_sent:
            context = self._load_context()
            if context:
                full_message = f"{context}\n\n---\n\nBhav says: {message}"
                self.__class__._context_sent = True
                return self.send(full_message)
        return self.send(message)

    def reset_context(self):
        """Force context to be re-sent on next message (e.g. after AI switch)."""
        self.__class__._context_sent = False
