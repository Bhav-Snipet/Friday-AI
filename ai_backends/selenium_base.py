"""
ai_backends/selenium_base.py  —  LTS (Long-Term Support) Base Engine
───────────────────────────────────────────────────────────────────
Robust, auto-recovering Selenium driver base for all web-based AI backends.

LTS Features:
  - Externalized selector resolution (loads from selectors.json with fallback heuristics)
  - Self-healing browser recovery (automatically rebuilds driver if Chrome crashes or disconnects)
  - Multi-strategy element finder (CSS + XPath + generic Tag heuristics)
  - Robust stream completion & stabilization detection
"""
import json
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

_PROJECT_ROOT = pathlib.Path(__file__).parent.parent
_SELECTORS_FILE = pathlib.Path(__file__).parent / "selectors.json"
log = logging.getLogger("FRIDAY-Selenium-LTS")


def _load_lts_selectors(name: str) -> dict:
    """Load selectors from selectors.json with resilient fallback defaults."""
    defaults = {
        "input_selectors": ["div[contenteditable='true']", "textarea", "input[type='text']", "[role='textbox']"],
        "send_selectors": ["button[type='submit']", "button[aria-label*='Send']", "button.send-button"],
        "response_selectors": ["div.markdown", "div.prose", "div[role='region']", "p"]
    }
    if _SELECTORS_FILE.exists():
        try:
            data = json.loads(_SELECTORS_FILE.read_text(encoding="utf-8"))
            if name in data:
                return data[name]
        except Exception as e:
            log.warning(f"Could not load selectors.json: {e}")
    return defaults


class SeleniumBackend(BaseAIBackend):
    """
    Long-Term Support (LTS) resilient Selenium base for AI backends.
    """
    name: str = "selenium_base"
    url:  str = ""
    input_selectors:    list = []
    send_selectors:     list = []
    response_selectors: list = []
    _context_sent:      bool = False

    def __init__(self, headless: bool = True):
        self.driver    = None
        self._headless = headless
        self._session_dir = _PROJECT_ROOT / "sessions" / self.name
        self._session_dir.mkdir(parents=True, exist_ok=True)
        
        # Load external dynamic selectors for LTS resilience
        cfg = _load_lts_selectors(self.name)
        if not self.url and "url" in cfg:
            self.url = cfg["url"]
        if not self.input_selectors and "input_selectors" in cfg:
            self.input_selectors = cfg["input_selectors"]
        if not self.send_selectors and "send_selectors" in cfg:
            self.send_selectors = cfg["send_selectors"]
        if not self.response_selectors and "response_selectors" in cfg:
            self.response_selectors = cfg["response_selectors"]

        self._start_browser()

    def _start_browser(self):
        """Build driver & open site with error handling."""
        try:
            self._build_driver()
            self._open_site()
            self._login()
        except Exception as e:
            log.error(f"[{self.name}] Browser initialization error: {e}")

    def _build_driver(self):
        opts = Options()
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        opts.add_argument(f"user-data-dir={self._session_dir}")
        opts.add_argument("--profile-directory=Default")
        opts.add_argument("--log-level=3")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--disable-notifications")
        opts.add_argument("--disable-popup-blocking")
        opts.add_argument("--no-first-run")
        opts.add_argument("--no-default-browser-check")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        if self._headless:
            opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opts)
        self.driver.set_page_load_timeout(35)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        log.info(f"[{self.name}] Driver ready (headless={self._headless})")

    def _open_site(self):
        if self.url:
            log.info(f"[{self.name}] Opening {self.url} …")
            self.driver.get(self.url)
            time.sleep(2.5)

    def _login(self):
        pass

    def _recover_driver(self):
        """Self-healing: recover browser if connection drops or crashes."""
        log.warning(f"[{self.name}] 🔄 Self-healing: Rebuilding Chrome driver session...")
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
        self.driver = None
        self._start_browser()

    def _find(self, selectors: list, timeout: int = 8):
        """Try CSS selectors then XPath/Tag fallback."""
        if not self.driver:
            self._recover_driver()

        for sel in selectors:
            try:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                return el
            except Exception:
                continue

        # Heuristic fallbacks for LTS resilience
        fallback_heuristics = [
            (By.TAG_NAME, "textarea"),
            (By.XPATH, "//div[@contenteditable='true']"),
            (By.XPATH, "//input[@type='text']"),
            (By.XPATH, "//*[@role='textbox']")
        ]
        for by_type, pattern in fallback_heuristics:
            try:
                el = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((by_type, pattern))
                )
                return el
            except Exception:
                continue

        raise RuntimeError(f"[{self.name}] None of the selectors matched.")

    def _get_response_text(self) -> str:
        if not self.driver:
            return ""
        for sel in self.response_selectors:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    texts = [e.text.strip() for e in els if e.text.strip()]
                    if texts:
                        return texts[-1]
            except Exception:
                continue
        # Fallback to paragraph tag check
        try:
            ps = self.driver.find_elements(By.TAG_NAME, "p")
            texts = [p.text.strip() for p in ps if len(p.text.strip()) > 10]
            if texts:
                return texts[-1]
        except Exception:
            pass
        return ""

    def _is_streaming(self) -> bool:
        if not self.driver:
            return False
        stop_selectors = [
            "button[aria-label*='Stop']",
            "button[title*='Stop']",
            "[data-testid*='stop']",
            "button.stop-button",
        ]
        for sel in stop_selectors:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if any(e.is_displayed() for e in els):
                    return True
            except Exception:
                pass
        return False

    def send(self, message: str) -> str:
        """Send message with self-healing retry loop."""
        for attempt in range(2):
            try:
                return self._send_internal(message)
            except Exception as e:
                log.warning(f"[{self.name}] Send attempt {attempt + 1} failed: {e}")
                self._recover_driver()
                time.sleep(1)

        return f"[{self.name}] Unable to complete query after self-healing retry."

    def _send_internal(self, message: str) -> str:
        response_text = ""
        inp = self._find(self.input_selectors, timeout=3)
        inp.click()
        time.sleep(0.1)

        try:
            inp.clear()
        except Exception:
            inp.send_keys(Keys.CONTROL + "a")
            inp.send_keys(Keys.DELETE)

        inp.send_keys(message)
        time.sleep(0.1)

        if self.send_selectors:
            try:
                btn = self._find(self.send_selectors, timeout=2)
                btn.click()
            except Exception:
                inp.send_keys(Keys.RETURN)
        else:
            inp.send_keys(Keys.RETURN)

        log.info(f"[{self.name}] Query submitted. Awaiting output...")

        prev_text  = ""
        stable_cnt = 0
        deadline   = time.time() + 6.0   # Fast 6s timeout max

        while time.time() < deadline:
            time.sleep(0.15)
            current = self._get_response_text()

            if current and len(current) > len(prev_text.strip()):
                prev_text  = current
                stable_cnt = 0
            elif current and current == prev_text and not self._is_streaming():
                stable_cnt += 1
                if stable_cnt >= 2:   # Stable for 300ms → return immediately!
                    response_text = current
                    break
            elif current:
                prev_text  = current
                stable_cnt = 0

        return response_text or prev_text


    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
        log.info(f"[{self.name}] Driver closed.")
