"""
logic_brain.py  –  F.R.I.D.A.Y. Brain Orchestrator
Created by Bhav  ·  github.com/Bhav-Snipet/Friday-AI
"""
import logging
import os
import pathlib
import threading
import time

from STT import listen, _stop_event as stt_stop

logging.basicConfig(level=logging.INFO, format="[FRIDAY-BRAIN] %(message)s")
log = logging.getLogger(__name__)

_BASE        = pathlib.Path(__file__).parent
INPUT_FILE   = _BASE / "web" / "input.txt"
OUTPUT_FILE  = _BASE / "web" / "response.txt"

# ── Active AI backend ─────────────────────────────────────────────────────────
_active_ai_name = os.getenv("ACTIVE_AI", "piai").lower()
_backend        = None
_backend_lock   = threading.Lock()


def _load_backend(name: str):
    """Instantiate the requested AI backend and load context on first use."""
    global _backend, _active_ai_name
    log.info(f"Loading AI backend: {name} …")
    try:
        from ai_backends import get_backend
        b = get_backend(name)
        _active_ai_name = name
        _backend = b
        log.info(f"✅ Backend ready: {name}")
    except Exception as e:
        log.error(f"Failed to load backend '{name}': {e}")


def set_active_ai(name: str):
    """Switch the active AI backend (called from Friday.py when user clicks switcher)."""
    with _backend_lock:
        if _backend is not None and hasattr(_backend, 'reset_context'):
            _backend.reset_context()
        _load_backend(name)
        log.info(f"AI switched → {name}")


# ── TTS ───────────────────────────────────────────────────────────────────────
_tts = None
try:
    import pyttsx3
    _tts = pyttsx3.init()
    _tts.setProperty("rate", 165)
    _tts.setProperty("volume", 1.0)
    for v in _tts.getProperty("voices"):
        if "zira" in v.name.lower() or "female" in v.name.lower():
            _tts.setProperty("voice", v.id)
            break
    log.info("TTS engine ready.")
except Exception as e:
    log.warning(f"TTS not available: {e}")


def _speak(text: str):
    if _tts and text:
        try:
            _tts.say(text)
            _tts.runAndWait()
        except Exception as e:
            log.warning(f"TTS error: {e}")


# ── Brain loop ────────────────────────────────────────────────────────────────
def brain_loop(stop_event: threading.Event):
    last_input = ""
    INPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not INPUT_FILE.exists():  INPUT_FILE.write_text("", encoding="utf-8")
    if not OUTPUT_FILE.exists(): OUTPUT_FILE.write_text("", encoding="utf-8")

    log.info("Brain loop started — waiting for wake word 'friday' …")

    while not stop_event.is_set():
        try:
            current = INPUT_FILE.read_text(encoding="utf-8").strip()
            if current and current != last_input:
                last_input = current
                cmd = current.lower()
                if "friday" in cmd:
                    log.info(f"Wake word detected → {cmd!r}")
                    with _backend_lock:
                        if _backend is None:
                            log.warning("No backend loaded yet.")
                        else:
                            # Send with context injection on first call
                            response = _backend.send_with_context(cmd)

                    if response:
                        OUTPUT_FILE.write_text(response, encoding="utf-8")
                        (_BASE / "output.txt").write_text(response, encoding="utf-8")
                        log.info(f"Response ({len(response)} chars) saved.")
                        _speak(response)
        except Exception as e:
            log.error(f"Brain loop error: {e}")
        time.sleep(0.4)

    log.info("Brain loop stopped.")


# ── Friday brain orchestrator ─────────────────────────────────────────────────
def friday_brain():
    stop_event = threading.Event()

    # Load default backend
    _load_backend(_active_ai_name)

    t_stt   = threading.Thread(target=listen,     args=(stt_stop,),   daemon=True, name="STT")
    t_brain = threading.Thread(target=brain_loop, args=(stop_event,), daemon=True, name="Brain")

    t_stt.start()
    t_brain.start()

    try:
        while t_stt.is_alive() and t_brain.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Shutdown requested …")
    finally:
        stop_event.set()
        stt_stop.set()
        if _backend and hasattr(_backend, 'close'):
            _backend.close()
        log.info("FRIDAY Brain shut down cleanly.")
