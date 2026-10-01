"""
ai_backends/pi_ai.py
Pi.ai backend — uses Selenium to automate the pi.ai/talk chat interface.
Optimized for fast response detection: ~0.8s minimum latency.
"""
import logging
import pathlib
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from .base import BaseAIBackend

log = logging.getLogger("FRIDAY-PiAI")
_BASE = pathlib.Path(__file__).parent.parent


class PiAIBackend(BaseAIBackend):
    name = "piai"
    _context_sent = False

    def __init__(self, headless: bool = True):
        self.driver = None
        self._last_msg_count = 0   # track message count to detect new replies fast
        self._init_driver(headless)
        self._login()
        # Send context briefing in background so it never blocks startup or queries
        import threading
        threading.Thread(
            target=self._send_context_briefing,
            daemon=True,
            name="PiAI-Context"
        ).start()

    def _init_driver(self, headless: bool):
        # Each backend gets its own sessions/ subfolder — no profile lock conflicts
        session_dir = _BASE / "sessions" / "piai"
        session_dir.mkdir(parents=True, exist_ok=True)

        opts = Options()
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        opts.add_argument(f"user-data-dir={session_dir}")
        opts.add_argument("--profile-directory=Default")
        opts.add_argument("--log-level=3")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        if headless:
            opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=opts
        )
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        log.info("Pi.ai Chrome driver ready.")

    def _login(self):
        try:
            self.driver.get("https://pi.ai/talk")
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "textarea[placeholder]"))
            )
            log.info("✅ Pi.ai — already logged in.")
        except Exception:
            log.warning("Pi.ai session not found — attempting onboarding …")
            try:
                for _ in range(3):
                    btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='button']"))
                    )
                    btn.click()
                    time.sleep(0.8)
            except Exception as e:
                log.error(f"Pi.ai onboarding failed: {e}")

    def _send_context_briefing(self):
        """
        Send FRIDAY_CONTEXT.txt as a silent first message on startup so Pi.ai
        knows who Bhav is. This is done ONCE at init, NOT at query time,
        so regular queries don't carry the huge context overhead.
        """
        if self.__class__._context_sent:
            return
        context = self._load_context()
        if not context:
            return
        log.info("Sending FRIDAY context briefing to Pi.ai …")
        try:
            response = self.send(context)
            self.__class__._context_sent = True
            log.info(f"Context briefing sent. Pi.ai ack: {response[:80]}…" if response else "Context sent (no ack).")
        except Exception as e:
            log.warning(f"Context briefing failed (non-fatal): {e}")

    def _get_messages(self):
        """Return all visible AI reply elements."""
        return self.driver.find_elements(
            By.CSS_SELECTOR,
            "div[class*='break-words'], div[data-testid*='message'], "
            ".prose, [class*='ChatMessage'], div[class*='response']"
        )

    def send(self, message: str) -> str:
        """
        Send message and wait for response.
        Uses body text snapshot to detect new content — more reliable than
        counting elements (which fails when Pi.ai reuses DOM nodes).
        """
        response_text = ""
        try:
            # Snapshot page body text BEFORE sending
            try:
                before_body = self.driver.find_element(By.TAG_NAME, "body").text
            except Exception:
                before_body = ""

            # Type & submit
            textarea = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea[placeholder]"))
            )
            textarea.clear()
            textarea.send_keys(message)
            time.sleep(0.25)
            textarea.send_keys(Keys.RETURN)

            # ── Fast polling loop ─────────────────────────────────────────────
            prev_text  = ""
            stable_cnt = 0
            deadline   = time.time() + 25

            while time.time() < deadline:
                time.sleep(0.35)
                try:
                    msgs = self._get_messages()
                    if msgs:
                        candidate = msgs[-1].text.strip()
                        # Only accept text that wasn't in the page before we sent
                        if candidate and candidate not in before_body:
                            if candidate == prev_text:
                                stable_cnt += 1
                                if stable_cnt >= 2:
                                    response_text = candidate
                                    break
                            else:
                                prev_text  = candidate
                                stable_cnt = 0
                except Exception:
                    pass

            if not response_text and prev_text and prev_text not in before_body:
                response_text = prev_text   # best-effort on timeout

        except Exception as e:
            log.error(f"Pi.ai send() error: {e}")

        return response_text

    # Override send_with_context: context is already sent at init for Pi.ai
    def send_with_context(self, message: str) -> str:
        return self.send(message)

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
