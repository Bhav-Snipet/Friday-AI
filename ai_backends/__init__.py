"""
ai_backends/__init__.py
AI backend registry for F.R.I.D.A.Y.
"""
from .pi_ai import PiAIBackend
from .gemini_ai import GeminiBackend
from .claude_ai import ClaudeBackend

BACKENDS = {
    "piai":   PiAIBackend,
    "gemini": GeminiBackend,
    "claude": ClaudeBackend,
}

def get_backend(name: str):
    cls = BACKENDS.get(name.lower())
    if not cls:
        raise ValueError(f"Unknown backend: {name!r}. Choose from: {list(BACKENDS)}")
    return cls()
