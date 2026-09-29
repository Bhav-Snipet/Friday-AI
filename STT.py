import logging
import pathlib
import threading
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format="[FRIDAY-STT] %(message)s")
log = logging.getLogger(__name__)

# ── Path to the file where recognised speech is written ───────────────────────
_BASE = pathlib.Path(__file__).parent
RECOG_FILE = _BASE / "web" / "input.txt"
RECOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── Stop event so listen() can be cleanly shut down from another thread ────────
_stop_event = threading.Event()


def _build_stt_driver() -> webdriver.Chrome:
    """
    Build a headless Chrome instance that:
    - Grants microphone permission automatically (needed by the STT page)
    - Uses --use-fake-ui-for-media-stream so Chrome won't pop a permission dialog
    """
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--log-level=3")

    # Fake the media stream permission grant so headless Chrome allows mic access
    opts.add_argument("--use-fake-ui-for-media-stream")
    # If you want to use a real mic feed instead of silence: remove the next line
    opts.add_argument("--use-fake-device-for-media-stream")

    service = Service(ChromeDriverManager().install())
    drv = webdriver.Chrome(service=service, options=opts)
    return drv


def listen(stop_event: threading.Event = _stop_event) -> None:
    """
    Open the Netlify STT page in a headless browser, click the Start button,
    and continuously write the recognised text to web/input.txt.

    The function runs until *stop_event* is set or a KeyboardInterrupt occurs.
    """
    log.info("Starting Speech-To-Text service …")
    driver = _build_stt_driver()

    STT_URL = "https://allorizenproject1.netlify.app/"
    driver.get(STT_URL)
    log.info(f"Opened STT page: {STT_URL}")

    try:
        # Wait for the Start button to appear
        start_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "startButton"))
        )
        start_btn.click()
        log.info("✅ STT Activated – listening …")

        last_written = ""

        while not stop_event.is_set():
            try:
                output_el = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "output"))
                )
                current_text = output_el.text.strip().lower()

                if current_text and current_text != last_written:
                    last_written = current_text
                    RECOG_FILE.write_text(current_text, encoding="utf-8")
                    log.info(f"User said: {current_text!r}")

            except Exception as e:
                log.debug(f"STT poll error (transient): {e}")

            time.sleep(0.5)   # poll twice per second

    except KeyboardInterrupt:
        log.info("STT stopped by keyboard interrupt.")
    except Exception as e:
        log.error(f"STT fatal error: {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        log.info("STT driver closed.")
