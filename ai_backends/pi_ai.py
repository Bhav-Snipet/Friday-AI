"""
ai_backends/pi_ai.py
Pi.ai backend — uses Selenium to automate the pi.ai/talk chat interface.
This is the original FRIDAY backend; no API key required.
"""
import logging
import os
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
        self._init_driver(headless)
        self._login()

    def _init_driver(self, headless: bool):
        ScriptDir = _BASE
        opts = Options()
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        opts.add_argument("--profile-directory=Default")
        opts.add_argument(f"user-data-dir={ScriptDir}\\chromedata")
        opts.add_argument("--log-level=3")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        if headless:
            opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opts)
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
                    time.sleep(1)
            except Exception as e:
                log.error(f"Pi.ai onboarding failed: {e}")

    def send(self, message: str) -> str:
        response_text = ""
        try:
            textarea = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea[placeholder]"))
            )
            textarea.clear()
            textarea.send_keys(message)
            time.sleep(0.3)
            textarea.send_keys(Keys.RETURN)

            time.sleep(2)
            prev_text = ""
            stable = 0
            for _ in range(30):
                try:
                    msgs = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        "div[class*='break-words'], div[data-testid*='message'], "
                        ".prose, [class*='ChatMessage'], div[class*='msg']"
                    )
                    if msgs:
                        candidate = msgs[-1].text.strip()
                        if candidate and candidate == prev_text:
                            stable += 1
                            if stable >= 2:
                                response_text = candidate
                                break
                        else:
                            prev_text = candidate
                            stable = 0
                except Exception:
                    pass
                time.sleep(1)

            if not response_text:
                response_text = prev_text

        except Exception as e:
            log.error(f"Pi.ai send() error: {e}")

        return response_text

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
