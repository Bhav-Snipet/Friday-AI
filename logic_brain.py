"""
logic_brain.py  –  F.R.I.D.A.Y. Hyper-Speed Brain Orchestrator
Created by Bhav  ·  github.com/Bhav-Snipet/Friday-AI

Fixed:
  - Deadlock-free AI switching (backend init runs on separate thread, not under brain lock)
  - Robust TTS worker with restart-on-crash protection
  - Correct default backend from ACTIVE_AI env var
  - STT mute state removed (no more broken import)
  - Gemini context sent cleanly via system_instruction (no prepend hack)
"""
import logging
import os
import pathlib
import queue
import threading
import time

from STT import listen, _stop_event as stt_stop

logging.basicConfig(level=logging.INFO, format="[FRIDAY-BRAIN] %(message)s")
log = logging.getLogger(__name__)

_BASE        = pathlib.Path(__file__).parent
INPUT_FILE   = _BASE / "web" / "input.txt"
OUTPUT_FILE  = _BASE / "web" / "response.txt"

# ── Global System State ───────────────────────────────────────────────────────
_active_ai_name   = os.getenv("ACTIVE_AI", "piai").lower()
_backend          = None
_backend_lock     = threading.Lock()       # ONLY guards reads/writes of _backend reference
_shutdown_event   = threading.Event()
_tts_queue        = queue.Queue()
_switch_in_progress = False                # guard against double-switches


# ── Shutdown ─────────────────────────────────────────────────────────────────
def request_shutdown():
    log.info("🛑 System shutdown requested!")
    _shutdown_event.set()
    stt_stop.set()
    # Close the active backend without holding brain lock (avoid deadlock at shutdown)
    backend = None
    with _backend_lock:
        backend = _backend
    if backend and hasattr(backend, 'close'):
        try:
            backend.close()
        except Exception:
            pass


# ── Backend Loading ───────────────────────────────────────────────────────────
def _load_backend(name: str):
    """Instantiate requested AI backend and swap it in atomically."""
    global _backend, _active_ai_name
    log.info(f"Loading AI backend: {name} …")
    try:
        from ai_backends import get_backend
        b = get_backend(name)
        # Atomically swap the backend reference
        with _backend_lock:
            old = _backend
            _backend = b
            _active_ai_name = name
        # Close old backend AFTER swap so brain_loop never sees None
        if old and hasattr(old, 'close'):
            try:
                old.close()
            except Exception:
                pass
        log.info(f"✅ Backend ready: {name}")
    except Exception as e:
        log.error(f"Failed to load backend '{name}': {e}")


def set_active_ai(name: str):
    """
    Switch AI backend — runs in a background thread so it never
    blocks brain_loop or causes a deadlock.
    """
    global _switch_in_progress
    if _switch_in_progress:
        log.warning(f"AI switch already in progress, ignoring request for: {name}")
        return
    _switch_in_progress = True

    def _do_switch():
        global _switch_in_progress
        try:
            # Reset context on old backend first
            with _backend_lock:
                b = _backend
            if b and hasattr(b, 'reset_context'):
                try:
                    b.reset_context()
                except Exception:
                    pass
            _load_backend(name)
            log.info(f"AI switched → {name}")
        finally:
            _switch_in_progress = False

    t = threading.Thread(target=_do_switch, name=f"AI-Switch-{name}", daemon=True)
    t.start()


def get_active_ai() -> str:
    """Return currently active AI backend name."""
    return _active_ai_name


# ── TTS Worker (crash-protected, per-utterance COM isolation) ─────────────────
def _tts_worker():
    """
    Dedicated TTS thread. Uses fresh pyttsx3 + COM per utterance to
    prevent Windows SAPI5 COM apartment lockup after first speech.
    Automatically restarts if it crashes.
    """
    log.info("🔊 Dedicated Voice TTS Worker active.")
    while not _shutdown_event.is_set():
        try:
            text = _tts_queue.get(timeout=1.0)
        except queue.Empty:
            continue

        if not text:
            _tts_queue.task_done()
            continue

        log.info(f"🗣️ Speaking: {text[:80]!r}{'...' if len(text) > 80 else ''}")

        # Per-utterance COM init/deinit to avoid SAPI5 COM lockup
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass

        try:
            import pyttsx3
            engine = pyttsx3.init('sapi5')
            engine.setProperty("rate", 165)
            engine.setProperty("volume", 1.0)

            # Pick Microsoft Zira if available, else first available voice
            voices = engine.getProperty("voices")
            chosen = None
            for v in voices:
                if "zira" in v.name.lower():
                    chosen = v.id
                    break
            if chosen is None and voices:
                chosen = voices[0].id
            if chosen:
                engine.setProperty("voice", chosen)

            engine.say(text)
            engine.runAndWait()
            engine.stop()
            del engine
            log.info("✅ TTS playback complete.")
        except Exception as ex:
            log.warning(f"TTS playback error: {ex}")
        finally:
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass

        _tts_queue.task_done()

    log.info("TTS worker stopped.")


def _start_tts_thread():
    t = threading.Thread(target=_tts_worker, daemon=True, name="TTSWorker")
    t.start()
    return t


# Start TTS thread — will be auto-watched and restarted if dead
_tts_thread = _start_tts_thread()


def _speak(text: str):
    """Queue text for non-blocking voice output. Restart TTS thread if dead."""
    global _tts_thread
    if not text:
        return
    if not _tts_thread.is_alive():
        log.warning("TTS thread died — restarting …")
        _tts_thread = _start_tts_thread()
    _tts_queue.put(text)


# ── Iron Man Fallback Engine ──────────────────────────────────────────────────
def _generate_fast_friday_response(query: str) -> str:
    """In-character Iron Man F.R.I.D.A.Y. fallback response (offline)."""
    q = query.lower()
    if any(w in q for w in ["quantum", "eigenstate", "mobius"]):
        return "Quantum eigenstate calculations show 99.4% topological coherence. All spin tensors stable, Boss."
    elif any(w in q for w in ["nano", "armor", "thruster", "suit"]):
        return "Mark LXXXV nanoparticle analysis confirms micro-thruster output can be safely boosted 14%, Boss."
    elif any(w in q for w in ["shield", "vibranium", "plasma"]):
        return "Plasma shield matrix calibrated. Arc Reactor distribution optimal for up to 50 gigajoules."
    elif any(w in q for w in ["who are you", "identity", "what are you"]):
        return "I am F.R.I.D.A.Y. — your personal voice intelligence assistant. All systems operational."
    elif any(w in q for w in ["hello", "hi", "hey", "good morning", "good evening"]):
        return "Systems nominal, Boss. Defence and diagnostics are online. What do you need?"
    elif any(w in q for w in ["status", "system", "check"]):
        return "All primary systems nominal. Neural core running at 100%. Ready for your command, Boss."
    elif any(w in q for w in ["shutdown", "shut down", "power off"]):
        return "Initiating shutdown sequence. Goodbye, Boss."
    else:
        return "Right away, Boss. Running primary diagnostics — systems operating at peak capacity."


# ── Fast Brain Loop ───────────────────────────────────────────────────────────
def brain_loop(stop_event: threading.Event):
    last_input = ""
    INPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    INPUT_FILE.touch(exist_ok=True)
    OUTPUT_FILE.touch(exist_ok=True)

    log.info("⚡ Fast Brain loop active — listening for keyword 'friday' …")

    while not stop_event.is_set() and not _shutdown_event.is_set():
        try:
            current = INPUT_FILE.read_text(encoding="utf-8").strip()

            if current and current != last_input:
                last_input = current
                cmd = current.lower()

                # Clear previous response so UI polling detects every new one
                OUTPUT_FILE.write_text("", encoding="utf-8")

                # Strict keyword gate
                if "friday" not in cmd:
                    log.debug(f"Skipping (no 'friday' keyword): {cmd!r}")
                    time.sleep(0.1)
                    continue

                log.info(f"⚡ 'Friday' query received → {cmd!r}")

                # Voice shutdown command
                if any(w in cmd for w in ["shutdown friday", "shut down friday"]):
                    msg = "Shutting down all F.R.I.D.A.Y. systems. Goodbye, Boss."
                    OUTPUT_FILE.write_text(msg, encoding="utf-8")
                    _speak(msg)
                    request_shutdown()
                    break

                # Get backend reference atomically (no lock held during .send)
                with _backend_lock:
                    backend = _backend

                response = ""
                if backend is not None and not _switch_in_progress:
                    backend_name = getattr(backend, 'name', type(backend).__name__).upper()
                    log.info(f"🤖 Routing to [{backend_name}] backend …")
                    try:
                        response = backend.send_with_context(cmd)
                    except Exception as ex:
                        log.error(f"Backend send error: {ex}")

                # Clean up generic "message got cut off" type filler responses
                junk_phrases = [
                    "it looks like your message got cut off",
                    "seems like your message was cut off",
                    "your message got cut off",
                ]
                if response and any(p in response.lower() for p in junk_phrases):
                    log.warning("Detected generic AI filler — using fallback engine.")
                    response = ""

                if not response:
                    log.info("Using Iron Man Fallback Engine …")
                    response = _generate_fast_friday_response(cmd)

                # Write response
                OUTPUT_FILE.write_text(response, encoding="utf-8")
                (_BASE / "output.txt").write_text(response, encoding="utf-8")
                log.info(f"✅ Response saved ({len(response)} chars).")

                # Speak it
                _speak(response)

        except Exception as e:
            log.error(f"Brain loop error: {e}")

        time.sleep(0.08)  # ~12 polls/second

    log.info("Brain loop stopped.")


# ── Friday Brain Orchestrator ─────────────────────────────────────────────────
def friday_brain():
    stop_event = threading.Event()

    # Load default backend
    _load_backend(_active_ai_name)

    t_stt   = threading.Thread(target=listen,     args=(stt_stop,),   daemon=True, name="STT")
    t_brain = threading.Thread(target=brain_loop, args=(stop_event,), daemon=True, name="Brain")

    t_stt.start()
    t_brain.start()

    try:
        while t_brain.is_alive() and not _shutdown_event.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        log.info("Shutdown requested …")
    finally:
        stop_event.set()
        stt_stop.set()
        # Close backend without holding a lock
        with _backend_lock:
            b = _backend
        if b and hasattr(b, 'close'):
            try:
                b.close()
            except Exception:
                pass
        log.info("FRIDAY Brain shut down cleanly.")
