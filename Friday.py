"""
Friday.py  –  F.R.I.D.A.Y. V1 Entry Point
Created by Bhav  ·  github.com/Bhav-Snipet/Friday-AI
"""
import os
import threading
import time
import pathlib
import logging

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import eel
from logic_brain import friday_brain, set_active_ai

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
def set_active_ai(name: str):
    """Called from JS when user clicks an AI switcher button."""
    log.info(f"AI switched to: {name}")
    set_active_ai(name)


# ── UI thread ─────────────────────────────────────────────────────────────────
def _ui():
    try:
        eel.start(
            "index.html",
            mode="chrome",
            port=8090,
            cmdline_args=["--start-fullscreen"],
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
    time.sleep(2)
    t_ui.start()

    try:
        while t_brain.is_alive() or t_ui.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Shutdown requested — goodbye, Boss.")


if __name__ == "__main__":
    friday()