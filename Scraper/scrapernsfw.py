#!/usr/bin/env python3
# ============================================================================
#  WYR Stealth Scraper — scrapernsfw.py
# ============================================================================
#  A stealth web scraper for the NSFW category on https://wouldyourather.app/
#
#  Output: data/questions_nsfw.json  (schema compatible with the Telegram bot)
#
#  Usage:
#      pip install -r requirements.txt
#      python scrapernsfw.py
# ============================================================================

import json
import os
import random
import sys
import time
import logging
from pathlib import Path

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)

from config import (
    PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS,
    HEADLESS_MODE, USER_AGENT,
    TARGET_URL, MAX_QUESTIONS,
    PAGE_LOAD_WAIT, ACTION_DELAY, SCROLL_DELAY, VOTE_REVEAL_WAIT,
)
import subprocess
import re

OUTPUT_FILE = "data/questions_nsfw.json"

# ---------------------------------------------------------------------------
#  Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("wyr-scraper-nsfw")


# ═══════════════════════════════════════════════════════════════════════════
#  1.  HUMAN-LIKE DELAY HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def human_delay(bounds: tuple[float, float], label: str = "") -> None:
    """Sleep for a random duration within *bounds* (min, max) seconds."""
    wait = random.uniform(*bounds)
    if label:
        log.debug("  ⏳ %s — waiting %.2fs", label, wait)
    time.sleep(wait)


# ═══════════════════════════════════════════════════════════════════════════
#  2.  BROWSER FACTORY  (undetected-chromedriver + proxy)
# ═══════════════════════════════════════════════════════════════════════════
def detect_chrome_version() -> int | None:
    """
    Auto-detect the installed Chrome major version on Windows.
    Queries the registry first, then falls back to checking common install paths.
    Returns the major version number (e.g. 151) or None if detection fails.
    """
    # Method 1: Windows Registry query
    reg_paths = [
        r"HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon",
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Google\Chrome\BLBeacon",
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Google\Chrome\BLBeacon",
    ]
    for reg_path in reg_paths:
        try:
            result = subprocess.run(
                ["reg", "query", reg_path, "/v", "version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                match = re.search(r"(\d+)\.\d+\.\d+\.\d+", result.stdout)
                if match:
                    ver = int(match.group(1))
                    log.info("🔍 Detected Chrome version %d (via registry)", ver)
                    return ver
        except Exception:
            continue

    # Method 2: Run chrome.exe --version directly
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for path in chrome_paths:
        if os.path.exists(path):
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True, text=True, timeout=10
                )
                match = re.search(r"(\d+)\.\d+\.\d+\.\d+", result.stdout)
                if match:
                    ver = int(match.group(1))
                    log.info("🔍 Detected Chrome version %d (via executable)", ver)
                    return ver
            except Exception:
                continue

    log.warning("⚠️  Could not auto-detect Chrome version")
    return None


def create_stealth_browser() -> uc.Chrome:
    """
    Launch a Chrome instance via undetected-chromedriver.
    All common automation fingerprints (navigator.webdriver, CDP flags,
    cdc_ variables) are automatically stripped by the library.
    """
    options = uc.ChromeOptions()

    # ── Headless toggle ────────────────────────────────────────────────
    if HEADLESS_MODE:
        options.add_argument("--headless=new")          # Chrome 109+ headless
        options.add_argument("--window-size=1920,1080")
    else:
        options.add_argument("--start-maximized")

    # ── Standard stealth flags ─────────────────────────────────────────
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-first-run")
    options.add_argument("--no-service-autorun")
    options.add_argument("--password-store=basic")
    options.add_argument(f"--user-agent={USER_AGENT}")

    # ── Proxy routing (residential proxy) ──────────────────────────────
    if PROXY_HOST and PROXY_PORT:
        proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
        # undetected-chromedriver handles authenticated proxies via a
        # background extension; we pass the string and let it manage.
        options.add_argument(f"--proxy-server=http://{PROXY_HOST}:{PROXY_PORT}")
        log.info("🌐 Proxy enabled → %s:%s", PROXY_HOST, PROXY_PORT)
    else:
        log.info("🌐 Proxy disabled — using direct connection")

    # ── Detect Chrome version to avoid driver mismatch ─────────────────
    chrome_major = detect_chrome_version()

    # ── Launch ─────────────────────────────────────────────────────────
    log.info("🚀 Launching stealth browser (headless=%s) …", HEADLESS_MODE)
    driver = uc.Chrome(
        options=options,
        use_subprocess=True,
        version_main=chrome_major,   # Pin ChromeDriver to actual browser version
    )

    # Extra stealth: override navigator.webdriver at the JS level
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                // Mask chrome.runtime to look non-automated
                window.chrome = { runtime: {} };
                // Spoof plugins array length
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                // Spoof language
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """
        },
    )

    return driver


# ═══════════════════════════════════════════════════════════════════════════
#  3.  DOM PARSING — extract question data from rendered HTML
# ═══════════════════════════════════════════════════════════════════════════
def parse_visible_statements(page_source: str) -> list[dict]:
    """
    Parse the fully-rendered DOM and extract every visible question
    (called a "statement" in the WYR markup).
    """
    soup = BeautifulSoup(page_source, "lxml")
    results: list[dict] = []

    statements = soup.select("div.statement, .statement")
    if not statements:
        # Fallback: try generic option containers
        statements = soup.select("[class*='statement']")

    for stmt in statements:
        try:
            # ── Extract option texts ──────────────────────────────────
            option_els = stmt.select(".option-text-wrapper h2")
            if len(option_els) < 2:
                # Try alternate selectors
                option_els = stmt.select(".option h2")
            if len(option_els) < 2:
                option_els = stmt.select("h2")
            if len(option_els) < 2:
                continue  # Skip malformed / ad / section-row blocks

            option_blue = option_els[0].get_text(strip=True)
            option_red  = option_els[1].get_text(strip=True)

            # Skip empty or obviously non-question blocks
            if not option_blue or not option_red:
                continue

            # ── Extract vote percentages ──────────────────────────────
            pct_els = stmt.select(".percentage")
            votes_blue = _parse_percentage(pct_els[0]) if len(pct_els) > 0 else 0
            votes_red  = _parse_percentage(pct_els[1]) if len(pct_els) > 1 else 0

            # ── Build record ──────────────────────────────────────────
            question_text = f"Would you rather {option_blue} or {option_red}?"
            record = {
                "id": f"nsfw_{random.randint(1000, 9999)}",
                "question": question_text,
                "option_blue": option_blue,
                "option_red": option_red,
                "global_votes_blue": votes_blue,
                "global_votes_red": votes_red,
            }
            results.append(record)
            log.info("   ✅ Parsed: %s…", option_blue[:50])

        except Exception as exc:
            log.warning("   ⚠️  Skipping malformed statement: %s", exc)
            continue

    return results


def _parse_percentage(el) -> int:
    """
    Extract a numeric vote value from a percentage element.
    The site renders percentages like "62%" inside the element;
    we strip the '%' and return the integer, falling back to 0.
    """
    if el is None:
        return 0
    text = el.get_text(strip=True).replace("%", "").replace(",", "").strip()
    try:
        return int(text)
    except (ValueError, TypeError):
        return 0


# ═══════════════════════════════════════════════════════════════════════════
#  4.  INTERACTION HELPERS — clicking & scrolling like a human
# ═══════════════════════════════════════════════════════════════════════════
def vote_on_current_question(driver: uc.Chrome) -> bool:
    """
    Click a random option on the currently visible question to reveal
    the vote percentages.  Returns True if the vote succeeded.
    """
    try:
        # Wait until at least one option is present and clickable
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".statement.active .option"))
        )

        options = driver.find_elements(By.CSS_SELECTOR, ".statement.active .option")
        if not options:
            options = driver.find_elements(By.CSS_SELECTOR, ".option")

        if len(options) < 2:
            log.warning("   ⚠️  Could not locate two votable options")
            return False

        # Pick a random option to click (mimics human indecision)
        target = random.choice(options[:2])
        human_delay(ACTION_DELAY, "pre-vote pause")

        # Scroll the option into view and click via JavaScript to bypass UI overlays
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
        human_delay((0.3, 0.8), "micro-pause before click")
        driver.execute_script("arguments[0].click();", target)

        # Wait for the percentage reveal animation
        human_delay(VOTE_REVEAL_WAIT, "waiting for percentages")
        return True

    except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
        log.warning("   ⚠️  Vote interaction failed: %s", e)
        return False


def scroll_to_next_question(driver: uc.Chrome) -> bool:
    """
    Scroll down to snap to the next question in the vertical scroll
    container.  The site uses CSS scroll-snap on .statements-wrapper.
    Returns True if the scroll succeeded.
    """
    try:
        human_delay(SCROLL_DELAY, "pre-scroll pause")

        # Method 1: Scroll the wrapper element
        driver.execute_script("""
            const wrapper = document.querySelector('.statements-wrapper');
            if (wrapper) {
                wrapper.scrollBy({ top: window.innerHeight, behavior: 'smooth' });
            } else {
                window.scrollTo(0, document.body.scrollHeight);
            }
        """)

        # Let the scroll-snap animation settle and wait for API to fetch new questions
        human_delay((2.0, 4.0), "scroll settle and wait for API to fetch new questions")
        return True

    except WebDriverException as e:
        log.warning("   ⚠️  Scroll failed: %s", e)
        return False


def dismiss_overlays(driver: uc.Chrome) -> None:
    """
    Dismiss any cookie banners, app-download banners, or overlay modals
    that might block interaction.
    """
    selectors = [
        ".banner",               # App install banner
        "[class*='cookie']",     # Cookie consent
        "[class*='consent']",
        "[class*='overlay']",
        ".modal",
    ]
    for sel in selectors:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in els:
                if el.is_displayed():
                    driver.execute_script("arguments[0].remove();", el)
                    log.debug("   🗑️  Dismissed overlay: %s", sel)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════
#  5.  MAIN SCRAPER LOOP
# ═══════════════════════════════════════════════════════════════════════════
def scrape_wyr() -> list[dict]:
    """
    Main orchestration:
      1. Launch stealth browser
      2. Navigate to target
      3. For each question: vote → parse → scroll to next
      4. Collect until MAX_QUESTIONS reached or no more questions
      5. Return collected records
    """
    all_questions: list[dict] = []
    seen_options: set[str] = set()        # De-duplicate by option text
    driver: uc.Chrome | None = None
    consecutive_failures = 0
    MAX_CONSECUTIVE_FAILURES = 8

    try:
        driver = create_stealth_browser()

        # ── Navigate to target ─────────────────────────────────────────
        log.info("🌍 Navigating to %s …", TARGET_URL)
        driver.get(TARGET_URL)
        human_delay(PAGE_LOAD_WAIT, "initial page load")

        # Wait for the main content container to appear
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".statements-wrapper"))
            )
            log.info("✅ Page loaded — statements wrapper detected")
        except TimeoutException:
            log.error("❌ Timed out waiting for page content. "
                       "Possible Cloudflare challenge or network issue.")
            # Save debug screenshot
            driver.save_screenshot("debug_timeout.png")
            return all_questions

        # ── Dismiss any overlays / banners ─────────────────────────────
        dismiss_overlays(driver)

        # ── Navigate to NSFW Category ──────────────────────────────────
        log.info("🌶️ Navigating to NSFW category...")
        try:
            # Click burger menu
            burger_menu = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".burger-menu"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", burger_menu)
            human_delay((0.5, 1.0), "waiting before opening menu")
            driver.execute_script("arguments[0].click();", burger_menu)
            human_delay((1.0, 2.0), "waiting for category overlay")
            
            # Click NSFW option
            nsfw_option = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//li[contains(., 'NSFW') or contains(., '🌶️')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", nsfw_option)
            human_delay((0.5, 1.0), "waiting before selecting NSFW")
            driver.execute_script("arguments[0].click();", nsfw_option)
            
            # Wait for the new NSFW deck to mount
            human_delay((2.0, 3.0), "waiting for NSFW deck to mount")
            log.info("✅ NSFW category loaded")
            
        except Exception as e:
            log.error("❌ Failed to navigate to NSFW category: %s", e)
            driver.save_screenshot("debug_nsfw_nav.png")
            return all_questions

        # ── Scrape loop ────────────────────────────────────────────────
        log.info("🔄 Starting scrape loop (target: %d questions) …", MAX_QUESTIONS)

        while len(all_questions) < MAX_QUESTIONS:
            round_num = len(all_questions) + 1
            log.info("── Round %d / %d ──", round_num, MAX_QUESTIONS)

            # Vote to reveal percentages
            voted = vote_on_current_question(driver)
            if not voted:
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    log.error("❌ Too many consecutive failures — aborting")
                    break
                scroll_to_next_question(driver)
                continue

            # Parse the current page state
            page_source = driver.page_source
            parsed = parse_visible_statements(page_source)

            # Add only new, unique questions
            new_count = 0
            for q in parsed:
                dedup_key = f"{q['option_blue']}||{q['option_red']}"
                if dedup_key not in seen_options:
                    seen_options.add(dedup_key)
                    all_questions.append(q)
                    new_count += 1

            if new_count > 0:
                consecutive_failures = 0
                log.info("   📥 Added %d new question(s) — total: %d",
                         new_count, len(all_questions))
            else:
                consecutive_failures += 1
                log.info("   ♻️  No new questions this round (dup or parse miss)")

            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                log.error("❌ Too many consecutive failures — aborting")
                break

            # Scroll to next question
            scroll_to_next_question(driver)

        log.info("🏁 Scraping complete — collected %d questions", len(all_questions))

    except KeyboardInterrupt:
        log.info("⛔ Interrupted by user — saving what we have …")

    except Exception as exc:
        log.exception("💥 Unexpected error: %s", exc)

    finally:
        if driver:
            try:
                driver.quit()
                log.info("🛑 Browser closed")
            except OSError as e:
                # Suppress [WinError 6] The handle is invalid when uc.Chrome.__del__ crashes
                pass
            except Exception as e:
                log.warning("⚠️  Suppressed error during browser teardown: %s", e)

    return all_questions


# ═══════════════════════════════════════════════════════════════════════════
#  6.  SAVE TO JSON
# ═══════════════════════════════════════════════════════════════════════════
def save_to_json(questions: list[dict], filepath: str) -> None:
    """Write the questions list to a JSON file, creating dirs if needed."""
    output_path = Path(filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Re-index IDs sequentially for clean output
    for idx, q in enumerate(questions, start=1):
        q["id"] = f"nsfw_{idx:04d}"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    log.info("💾 Saved %d questions → %s", len(questions), output_path.resolve())


# ═══════════════════════════════════════════════════════════════════════════
#  7.  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════
def main() -> None:
    log.info("=" * 60)
    log.info("  WYR Stealth Scraper (NSFW)")
    log.info("  Target : %s", TARGET_URL)
    log.info("  Max Qs : %d", MAX_QUESTIONS)
    log.info("  Output : %s", OUTPUT_FILE)
    log.info("=" * 60)

    questions = scrape_wyr()

    if questions:
        save_to_json(questions, OUTPUT_FILE)
    else:
        log.warning("⚠️  No questions were scraped. Check the logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
