"""
ai_backends/gemini_selenium.py
──────────────────────────────
Google Gemini backend — browser-based, NO API key needed.
Uses your Google account session saved in sessions/gemini/

ACTIVATION (first time only):
  1. In logic_brain.py set headless=False when loading this backend
  2. python Friday.py  → Chrome opens to gemini.google.com
  3. Sign in with your Google account
  4. Once on the chat page, close FRIDAY
  5. Set headless=True again — session is saved forever in sessions/gemini/
"""
import logging
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .selenium_base import SeleniumBackend

log = logging.getLogger("FRIDAY-Gemini-Selenium")


class GeminiSeleniumBackend(SeleniumBackend):
    name = "gemini"
    _context_sent = False

    # ── Target URL ────────────────────────────────────────────────────────────
    url = "https://gemini.google.com/app"

    # ── Input box selectors (tried in order) ─────────────────────────────────
    input_selectors = [
        "rich-textarea .ql-editor",          # main editor div
        "div[contenteditable='true']",        # fallback contenteditable
        "textarea[placeholder]",              # plain textarea fallback
        ".input-area-container [contenteditable]",
        "p.ql-editor",
    ]

    # ── Send button selectors ─────────────────────────────────────────────────
    send_selectors = [
        "button.send-button",
        "button[aria-label*='Send']",
        "button[mattooltip*='Send message']",
        "button[data-mat-icon-name='send']",
        ".send-button-container button",
    ]

    # ── Response area selectors ───────────────────────────────────────────────
    response_selectors = [
        "model-response .markdown",
        "model-response .response-content",
        ".model-response-text",
        "message-content .markdown",
        "[data-message-id] .markdown",
        "response-container .text-content",
    ]

    def _login(self):
        """
        Detect login state:
          - If input box appears → already logged in
          - If Google sign-in page appears → need manual login (headless=False mode)
        """
        try:
            # Check for the chat input — means we're logged in
            WebDriverWait(self.driver, 12).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ", ".join(self.input_selectors[:3]))
                )
            )
            log.info("✅ Gemini — already logged in (session restored).")
        except Exception:
            # Check if we're on a sign-in page
            if "accounts.google.com" in self.driver.current_url or \
               "signin" in self.driver.current_url.lower():
                if self._headless:
                    log.error(
                        "❌ Gemini: Not logged in. "
                        "Run with headless=False first to sign in. "
                        "See SETUP_GUIDE.md for instructions."
                    )
                else:
                    log.info(
                        "🔐 Gemini: Google sign-in page detected. "
                        "Please sign in manually in the browser window. "
                        "FRIDAY will wait up to 120 seconds …"
                    )
                    try:
                        # Wait for user to complete sign-in
                        WebDriverWait(self.driver, 120).until(
                            EC.url_contains("gemini.google.com")
                        )
                        time.sleep(3)
                        log.info("✅ Gemini sign-in successful!")
                    except Exception:
                        log.error("Gemini sign-in timeout.")
            else:
                log.warning(f"Gemini: Unexpected page: {self.driver.current_url}")

    def _is_streaming(self) -> bool:
        """Gemini shows a loading spinner while generating."""
        streaming_indicators = [
            "loading-indicator",
            ".loading-spinner",
            "[data-is-loading='true']",
            "response-loading",
            ".typing-indicator",
            ".shimmer",
        ]
        for sel in streaming_indicators:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if any(e.is_displayed() for e in els):
                    return True
            except Exception:
                pass
        return False
