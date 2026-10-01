"""
ai_backends/claude_selenium.py
───────────────────────────────
Anthropic Claude backend — browser-based, NO API key needed.
Uses your Anthropic account session saved in sessions/claude/

ACTIVATION (first time only):
  1. In SETUP_GUIDE.md follow the "First-time login" steps for Claude
  2. Visit https://claude.ai and create a free account if you don't have one
  3. Run Friday.py with headless=False, sign in, then switch back to headless=True
"""
import logging
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .selenium_base import SeleniumBackend

log = logging.getLogger("FRIDAY-Claude-Selenium")


class ClaudeSeleniumBackend(SeleniumBackend):
    name = "claude"
    _context_sent = False

    url = "https://claude.ai/new"

    # ── Input selectors ───────────────────────────────────────────────────────
    input_selectors = [
        "div[contenteditable='true'][data-placeholder]",  # main input
        ".ProseMirror[contenteditable='true']",            # ProseMirror editor
        "div[contenteditable='true']",                     # generic fallback
        "textarea[placeholder]",
        "[data-testid='chat-input']",
    ]

    # ── Send button selectors ─────────────────────────────────────────────────
    send_selectors = [
        "button[aria-label='Send Message']",
        "button[type='submit']",
        "button[data-testid='send-button']",
        ".send-button",
    ]

    # ── Response area selectors ───────────────────────────────────────────────
    response_selectors = [
        "div[data-is-streaming='false'] .prose",   # completed streaming
        ".prose",                                   # all prose blocks
        "[data-message-author-role='assistant'] .prose",
        ".message-content .prose",
        "article.prose",
    ]

    def _login(self):
        """Detect Claude login state."""
        try:
            WebDriverWait(self.driver, 12).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[contenteditable='true']")
                )
            )
            log.info("✅ Claude — already logged in (session restored).")
        except Exception:
            current = self.driver.current_url
            is_login_page = any(x in current for x in ["login", "signin", "auth", "claude.ai/login"])

            if self._headless:
                log.error(
                    "❌ Claude: Not logged in. "
                    "Run with headless=False first to sign in via claude.ai. "
                    "See SETUP_GUIDE.md for instructions."
                )
            else:
                log.info(
                    "🔐 Claude: Login page detected. "
                    "Please sign in manually (claude.ai). "
                    "Waiting up to 120 seconds …"
                )
                try:
                    WebDriverWait(self.driver, 120).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "div[contenteditable='true']")
                        )
                    )
                    time.sleep(2)
                    log.info("✅ Claude sign-in successful!")
                except Exception:
                    log.error("Claude sign-in timeout.")

    def _is_streaming(self) -> bool:
        """Claude shows a streaming indicator or data-is-streaming='true' attribute."""
        streaming_selectors = [
            "[data-is-streaming='true']",
            ".streaming-indicator",
            "div.text-generation-indicator",
        ]
        for sel in streaming_selectors:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if any(e.is_displayed() for e in els):
                    return True
            except Exception:
                pass
        return False
