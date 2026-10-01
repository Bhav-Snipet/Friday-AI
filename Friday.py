"""
Friday.py  –  F.R.I.D.A.Y. V1 Entry Point
Created by Bhav  ·  github.com/Bhav-Snipet/Friday-AI
"""
import logging
import os
import pathlib
import sys
import threading
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import eel
from logic_brain import (
    friday_brain,
    set_active_ai as _brain_set_ai,
    get_active_ai as _brain_get_ai,
    request_shutdown
)


logging.basicConfig(level=logging.INFO, format="[FRIDAY] %(message)s")
log = logging.getLogger(__name__)

_BASE         = pathlib.Path(__file__).parent
INPUT_FILE    = _BASE / "web" / "input.txt"
RESPONSE_FILE = _BASE / "web" / "response.txt"
OUTPUT_FILE   = _BASE / "output.txt"

for f in (INPUT_FILE, RESPONSE_FILE, OUTPUT_FILE):
    f.parent.mkdir(parents=True, exist_ok=True)
    if not f.exists():
        f.write_text("", encoding="utf-8")

eel.init(str(_BASE / "web"))


# ── Eel exposed functions ─────────────────────────────────────────────────────
@eel.expose
def get_latest_input() -> str:
    try:    return INPUT_FILE.read_text(encoding="utf-8").strip()
    except: return ""

@eel.expose
def get_latest_response() -> str:
    try:    return RESPONSE_FILE.read_text(encoding="utf-8").strip()
    except: return ""

@eel.expose
def get_active_ai() -> str:
    """Return active AI name for UI sync."""
    return _brain_get_ai()

@eel.expose
def set_active_ai(name: str):
    """Called from JS when user clicks an AI switcher button."""
    log.info(f"AI switched to: {name}")
    _brain_set_ai(name)

@eel.expose
def send_voice_input(text: str):
    """Direct instant voice/text submission from UI."""
    if text:
        log.info(f"UI submitted text: {text!r}")
        INPUT_FILE.write_text(text, encoding="utf-8")

@eel.expose
def shutdown_friday():
    log.info("Shutdown requested from UI button.")
    request_shutdown()
    time.sleep(0.5)
    os._exit(0)



def _on_window_close(page, sockets):
    log.info("Browser window closed by user — shutting down all F.R.I.D.A.Y. processes...")
    request_shutdown()
    time.sleep(0.5)
    os._exit(0)


# ── UI thread ─────────────────────────────────────────────────────────────────
def _ui():
    try:
        eel.start(
            "index.html",
            mode="chrome",
            port=8090,
            cmdline_args=["--start-fullscreen"],
            close_callback=_on_window_close,
            block=True,
        )
    except Exception as e:
        log.error(f"UI error: {e}")



# ── Main ──────────────────────────────────────────────────────────────────────
def friday():
    log.info("=" * 60)
    log.info("  F.R.I.D.A.Y.  —  Created by Bhav  (Bhav-Snipet)")
    log.info("  github.com/Bhav-Snipet/Friday-AI")
    log.info("  Say 'Friday' to wake me up.")
    log.info("=" * 60)

    t_brain = threading.Thread(target=friday_brain, daemon=True, name="FridayBrain")
    t_ui    = threading.Thread(target=_ui,           daemon=True, name="FridayUI")

    t_brain.start()
    time.sleep(1)
    t_ui.start()

    try:
        while t_brain.is_alive() or t_ui.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        log.info("Shutdown requested — goodbye, Boss.")


if __name__ == "__main__":
    friday()