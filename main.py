import time
import pathlib
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format="[FRIDAY-MAIN] %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Global driver reference (initialized by configure_driver())
# ─────────────────────────────────────────────────────────────
driver = None


def configure_driver(headless: bool = True):
    """
    Configure and return a Chrome WebDriver instance.
    
    headless=True  → silent background mode (default)
    headless=False → visible browser (for manual login / first-time setup)
    """
    ScriptDir = pathlib.Path(__file__).parent.absolute()
    chrome_options = Options()

    # Mimic a real browser so pi.ai doesn't block us
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # Persist login session between runs
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument(f"user-data-dir={ScriptDir}\\chromedata")

    # Suppress noisy DevTools / automation flags
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # ── Headless toggle ──────────────────────────────────────
    # Comment the next two lines out when doing first-time setup
    # (so you can see the browser, log in, and let Chrome save the session).
    # Uncomment them again once the session is stored in ./chromedata.
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
    # ─────────────────────────────────────────────────────────

    # webdriver-manager automatically downloads the right chromedriver
    service = Service(ChromeDriverManager().install())
    drv = webdriver.Chrome(service=service, options=chrome_options)

    # Hide the webdriver property so sites can't detect automation
    drv.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    log.info("Chrome WebDriver started successfully.")
    return drv


def login(drv):
    """
    Navigate to pi.ai and detect login state.
    If already logged in (session cookie saved in chromedata/) we skip the
    welcome flow; otherwise we click through the onboarding buttons.
    """
    try:
        drv.get("https://pi.ai/talk")
        log.info("Navigating to pi.ai/talk …")

        # Wait up to 15 s for the chat textarea to appear (= logged in)
        WebDriverWait(drv, 15).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "textarea[placeholder]")
            )
        )
        log.info("✅ Already logged in – session restored from chromedata/.")

    except Exception:
        log.warning("Session not found – attempting onboarding flow …")
        try:
            # pi.ai onboarding: click "Next" / "Get started" buttons
            for _ in range(3):
                btn = WebDriverWait(drv, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='button']"))
                )
                btn.click()
                time.sleep(1)
        except Exception as e:
            log.error(f"Onboarding failed: {e}")


def chat(message: str) -> str:
    """
    Type *message* into the pi.ai chat box, submit it, wait for the
    response to finish streaming, then write it to web/response.txt
    (overwriting the file each time so it always contains only the
    latest reply).

    Returns the response text (or an empty string on failure).
    """
    global driver
    if driver is None:
        log.error("Driver not initialized. Call init_driver() first.")
        return ""

    response_text = ""
    try:
        # ── Find the textarea ──────────────────────────────────
        textarea = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea[placeholder]"))
        )
        textarea.clear()
        textarea.send_keys(message)
        time.sleep(0.3)

        # Submit with Enter key (more reliable than clicking the send button)
        textarea.send_keys(Keys.RETURN)
        log.info(f"Sent: {message!r}")

        # ── Wait for the response to appear and stabilise ─────
        # Pi.ai streams the reply; we poll until text stops changing.
        time.sleep(2)
        prev_text = ""
        stable_count = 0
        for _ in range(30):          # max ~30 s wait
            try:
                # Grab all "assistant" message elements and take the last one
                msgs = driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[class*='break-words'], "
                    "div[data-testid*='message'], "
                    "div[class*='response'], "
                    ".prose, "
                    "[class*='ChatMessage'], "
                    "div[class*='msg']"
                )
                if msgs:
                    candidate = msgs[-1].text.strip()
                    if candidate and candidate == prev_text:
                        stable_count += 1
                        if stable_count >= 2:
                            response_text = candidate
                            break
                    else:
                        prev_text = candidate
                        stable_count = 0
            except Exception:
                pass
            time.sleep(1)

        if not response_text and prev_text:
            response_text = prev_text  # Use whatever we collected

        log.info(f"Response: {response_text[:120]}…" if len(response_text) > 120 else f"Response: {response_text}")

        # ── Persist response ───────────────────────────────────
        # Overwrite (not append) so the UI always shows only the latest reply
        import os
        os.makedirs("web", exist_ok=True)
        with open("web/response.txt", "w", encoding="utf-8") as f:
            f.write(response_text)

        # Also write to output.txt (read by Friday.py / eel layer)
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write(response_text)

    except Exception as e:
        log.error(f"chat() error: {e}")

    return response_text


def init_driver(headless: bool = True):
    """Initialize the global driver + login.  Call this once at startup."""
    global driver
    driver = configure_driver(headless=headless)
    login(driver)


def close_driver():
    """Gracefully shut down the browser."""
    global driver
    if driver:
        driver.quit()
        driver = None
        log.info("WebDriver closed.")
