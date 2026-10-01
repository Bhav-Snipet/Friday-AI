"""
ai_backends/chatgpt_selenium.py
────────────────────────────────
OpenAI ChatGPT backend — browser-based, NO API key needed.
Uses your OpenAI account session saved in sessions/chatgpt/

ACTIVATION (first time only):
  1. Follow SETUP_GUIDE.md → ChatGPT section
  2. Visit https://chat.openai.com and create an account (free) if needed
  3. Run Friday.py with headless=False, sign in, then switch back to headless=True
"""
import logging
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .selenium_base import SeleniumBackend

log = logging.getLogger("FRIDAY-ChatGPT-Selenium")


class ChatGPTSeleniumBackend(SeleniumBackend):
    name = "chatgpt"
    _context_sent = False

    url = "https://chat.openai.com/"

    # ── Input selectors ───────────────────────────────────────────────────────
    input_selectors = [
        "#prompt-textarea",                    # main textarea (most reliable)
        "div#prompt-textarea[contenteditable]",# contenteditable variant
        "textarea[data-id='root']",
        "textarea[placeholder]",
        ".chat-input textarea",
    ]

    # ── Send button selectors ─────────────────────────────────────────────────
    send_selectors = [
        "button[data-testid='send-button']",
        "button[aria-label='Send message']",
        "button.send-button",
        "form button[type='submit']",
    ]

    # ── Response area selectors ───────────────────────────────────────────────
    response_selectors = [
        "div[data-message-author-role='assistant'] .markdown",
        "div[data-message-author-role='assistant']",
        ".group\\/conversation-turn .markdown",
        "[data-testid*='assistant'] .markdown",
        ".text-message .markdown",
    ]

    def _login(self):
        """Detect ChatGPT login state — handles both chatgpt.com and openai auth pages."""
        try:
            # ChatGPT input visible = logged in
            WebDriverWait(self.driver, 12).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#prompt-textarea, textarea[placeholder], div[contenteditable]")
                )
            )
            log.info("✅ ChatGPT — already logged in (session restored).")
        except Exception:
            current = self.driver.current_url
            is_auth = any(x in current for x in ["auth0", "auth.", "login", "signin", "accounts.google"])

            if self._headless:
                log.error(
                    "❌ ChatGPT: Not logged in. "
                    "Run with headless=False first to sign in. "
                    "See SETUP_GUIDE.md for instructions."
                )
            else:
                log.info(
                    "🔐 ChatGPT: Login page detected. "
                    "Please sign in manually (chat.openai.com). "
                    "Waiting up to 120 seconds …"
                )
                try:
                    WebDriverWait(self.driver, 120).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "#prompt-textarea, textarea[placeholder]")
                        )
                    )
                    time.sleep(2)
                    log.info("✅ ChatGPT sign-in successful!")
                except Exception:
                    log.error("ChatGPT sign-in timeout.")

    def _is_streaming(self) -> bool:
        """ChatGPT shows a Stop button while generating."""
        stop_selectors = [
            "button[data-testid='stop-button']",
            "button[aria-label='Stop generating']",
            "button[aria-label*='Stop']",
        ]
        for sel in stop_selectors:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if any(e.is_displayed() for e in els):
                    return True
            except Exception:
                pass
        return False
