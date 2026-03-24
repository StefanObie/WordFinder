from __future__ import annotations

import re
import time
from datetime import datetime
import logging
from typing import Optional

import requests
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright  # type: ignore

from .base import Feedback, WordleSource


class NytWordleSource(WordleSource):
    """Wordle source backed by the NYT website via Playwright."""

    name = "scrape_nyt"

    @staticmethod
    def _log(message: str) -> None:
        logging.getLogger("self_solver").debug(f"[nyt_source] {message}")

    def __init__(
        self,
        headless: bool = True,
        delay_after_guess: float = 3.0,
        feedback_timeout: float = 8.0,
        feedback_poll_interval: float = 0.2,
        browser_mode: str = "persistent",
        chromium_user_data_dir: str = "~/.config/chromium",
        wordle_url: str = "https://www.nytimes.com/games/wordle/index.html",
    ):
        self.headless = headless
        self.delay_after_guess = delay_after_guess
        self.feedback_timeout = feedback_timeout
        self.feedback_poll_interval = feedback_poll_interval
        self.browser_mode = browser_mode.strip().lower()
        self.chromium_user_data_dir = chromium_user_data_dir
        self.wordle_url = wordle_url
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.attempt = 0

    def setup(self) -> None:
        self._log("Starting Playwright setup")
        self.playwright = sync_playwright().start()
        chromium_path = (
            "/usr/bin/chromium-browser" if self._exists("/usr/bin/chromium-browser") else "/usr/bin/chromium"
        )

        if self.browser_mode == "incognito":
            self._log("Launching NYT in incognito mode")
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                executable_path=chromium_path,
                args=["--disable-blink-features=AutomationControlled"],
            )
            self.context = self.browser.new_context(no_viewport=True)
            self.page = self.context.new_page()
        else:
            if self.browser_mode != "persistent":
                self._log(
                    f"Unknown browser_mode '{self.browser_mode}', falling back to persistent mode"
                )
            self._log("Launching NYT with persistent profile mode")
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self._expanduser(self.chromium_user_data_dir),
                headless=self.headless,
                executable_path=chromium_path,
                args=["--disable-blink-features=AutomationControlled"],
                no_viewport=True,
            )
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()

        self._log(f"Navigating to NYT Wordle page: {self.wordle_url}")
        self.page.goto(self.wordle_url)
        time.sleep(1)
        self._click_play_button()
        self._close_modals()
        self._log("NYT page setup complete")

    def scrape_answer(self) -> Optional[str]:
        today = datetime.now()
        month = today.strftime("%B").lower()
        day = today.day
        year = today.year
        url = f"https://lifehacker.com/entertainment/wordle-nyt-hint-today-{month}-{day}-{year}"
        self._log(f"Fetching answer from Lifehacker: {url}")

        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                self._log(f"Lifehacker request failed with status {response.status_code}")
                return None
            html = response.text
        except Exception:
            self._log("Lifehacker request raised an exception")
            return None

        # Typical phrase on the page is along the lines of: "Today's word is XXXXX"
        phrase_patterns = [
            r"today(?:'s)?\s+word\s+is\s+([a-z]{5})\b",
            r"word\s+is\s+([a-z]{5})\b",
        ]
        for pattern in phrase_patterns:
            match = re.search(pattern, html, flags=re.IGNORECASE)
            if match:
                self._log("Extracted answer using primary regex pattern")
                return match.group(1).lower()

        # Fallback: parse paragraph text and look for the answer sentence.
        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html, flags=re.IGNORECASE | re.DOTALL)
        for paragraph in paragraphs:
            text = re.sub(r"<[^>]+>", " ", paragraph)
            text = re.sub(r"\s+", " ", text).strip().lower()
            if "word is" not in text:
                continue
            match = re.search(r"word\s+is\s+([a-z]{5})\b", text)
            if match:
                self._log("Extracted answer using paragraph fallback parser")
                return match.group(1)

        self._log("Unable to extract answer from Lifehacker content")
        return None

    def submit_guess(self, guess: str) -> Feedback:
        if not self.page:
            raise RuntimeError("NYT source is not initialized")

        self.attempt += 1
        self._log(f"Submitting guess {self.attempt}: {guess.upper()}")

        for letter in guess.upper():
            self.page.keyboard.press(letter)
            time.sleep(0.08)
        self.page.keyboard.press("Enter")
        time.sleep(self.delay_after_guess)

        return self._wait_for_feedback(self.attempt)

    def close(self) -> None:
        self._log("Closing NYT source resources")
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def _click_play_button(self) -> None:
        if not self.page:
            return
        try:
            play_button = self.page.locator("button[data-testid='Play']")
            if play_button.is_visible(timeout=5000):
                play_button.click(no_wait_after=False)
                self.page.wait_for_load_state("networkidle")
                time.sleep(0.4)
        except Exception:
            return

    def _close_modals(self) -> None:
        if not self.page:
            return
        selectors = [
            "button[aria-label='Close']",
            "button.Modal-module_closeIcon__TcEKb",
            "svg[data-testid='icon-close']",
        ]
        for selector in selectors:
            try:
                close_buttons = self.page.locator(selector).all()
                for button in close_buttons:
                    if button.is_visible():
                        button.click()
                        time.sleep(0.15)
            except Exception:
                continue
        try:
            self.page.locator("body").click()
        except Exception:
            return

    def _get_feedback(self, row_number: int) -> Feedback:
        if not self.page:
            return []
        try:
            row_label = f"Row {row_number}"
            current_row = self.page.locator(f"div[role='group'][aria-label='{row_label}']")
            if current_row.count() == 0:
                rows = self.page.locator("div[role='group'][aria-label^='Row']").all()
                if row_number > len(rows):
                    return []
                row = rows[row_number - 1]
            else:
                row = current_row.first

            tiles = row.locator("div[data-state]").all()

            feedback: Feedback = []
            for tile in tiles:
                state = tile.get_attribute("data-state")
                if state not in {"correct", "present", "absent"}:
                    continue

                letter = (tile.text_content() or "").strip().lower()
                if not letter:
                    aria_label = tile.get_attribute("aria-label") or ""
                    parts = [part.strip().lower() for part in aria_label.split(",") if part.strip()]
                    if parts:
                        letter = parts[0][:1]

                if not letter:
                    continue

                feedback.append((letter, state))

            self._log(f"Row {row_number} feedback captured ({len(feedback)} tiles)")
            return feedback
        except Exception:
            self._log(f"Failed to scrape feedback for row {row_number}")
            return []

    def _wait_for_feedback(self, row_number: int) -> Feedback:
        deadline = time.time() + self.feedback_timeout
        best_feedback: Feedback = []

        while time.time() < deadline:
            feedback = self._get_feedback(row_number)
            if len(feedback) == 5:
                return feedback
            if len(feedback) > len(best_feedback):
                best_feedback = feedback
            time.sleep(self.feedback_poll_interval)

        self._log(
            f"Timed out waiting for full row feedback on row {row_number}; "
            f"best length was {len(best_feedback)}"
        )
        return best_feedback

    @staticmethod
    def _exists(path: str) -> bool:
        import os

        return os.path.exists(path)

    @staticmethod
    def _expanduser(path: str) -> str:
        import os

        return os.path.expanduser(path)
