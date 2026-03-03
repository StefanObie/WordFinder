"""
Browser interaction and web scraping utilities for Wordle.

This module handles all direct browser interactions using Playwright,
extracts feedback from the game page, and converts it to base3 format
for use with the decision tree strategy.
"""

import time
from typing import List, Tuple


def click_play_button(page):
    """Click the Play button on the landing page if present."""
    try:
        print("Looking for Play button...")
        # Wait for Play button and click it
        play_button = page.locator("button[data-testid='Play']")
        if play_button.is_visible(timeout=5000):
            # Use click with no_wait_after to prevent page navigation issues
            play_button.click(no_wait_after=False)
            print("Clicked Play button")
            # Wait for navigation to complete
            page.wait_for_load_state("networkidle")
            time.sleep(0.5)
            return True
    except Exception as e:
        print(f"Play button not found (may already be on game page): {e}")
    return False


def close_modals(page):
    """Close any popups/modals that might appear."""
    try:
        time.sleep(0.5)
        
        # Try multiple close button selectors
        close_selectors = [
            "button[aria-label='Close']",
            "button.Modal-module_closeIcon__TcEKb",
            "svg[data-testid='icon-close']"
        ]
        
        for selector in close_selectors:
            try:
                close_buttons = page.locator(selector).all()
                for button in close_buttons:
                    if button.is_visible():
                        button.click()
                        print("Closed modal")
                        time.sleep(0.2)
            except:
                pass
        
        # Click game area to dismiss overlays
        try:
            page.locator("body").click()
        except:
            pass
            
    except Exception as e:
        print(f"Note: Could not close modals: {e}")


def submit_guess(page, word: str, delay_after_guess: float = 3.0):
    """Type a word and submit it."""
    try:
        # Type each letter
        for letter in word.upper():
            page.keyboard.press(letter)
            time.sleep(0.1)
        
        # Press Enter
        page.keyboard.press("Enter")
        print(f"Submitted guess: {word.upper()}")
        
        # Wait for animations
        time.sleep(delay_after_guess)
        
    except Exception as e:
        print(f"Error submitting guess: {e}")
        raise


def get_feedback(page, row_number: int) -> List[Tuple[str, str]]:
    """
    Scrape feedback from the specified row.
    Returns list of tuples: [(letter, state), ...]
    where state is 'correct', 'present', or 'absent'
    """
    try:
        # Find all rows
        rows = page.locator("div[role='group'][aria-label^='Row']").all()
        
        if row_number > len(rows):
            raise Exception(f"Row {row_number} not found")
        
        current_row = rows[row_number - 1]
        
        # Find all tiles in this row
        tiles = current_row.locator("div[data-state]").all()
        
        feedback = []
        for tile in tiles:
            state = tile.get_attribute("data-state")
            aria_label = tile.get_attribute("aria-label")
            
            # Extract letter from aria-label (e.g., "1st letter, S, correct")
            letter = None
            if aria_label:
                parts = aria_label.split(',')
                if len(parts) >= 2:
                    letter = parts[1].strip().lower()
            
            if letter and state in ['correct', 'present', 'absent']:
                feedback.append((letter, state))
        
        return feedback
        
    except Exception as e:
        print(f"Error getting feedback: {e}")
        return []


def feedback_to_base3(feedback: List[Tuple[str, str]]) -> str:
    """
    Convert feedback tuples to base3 pattern string for decision tree.
    
    Args:
        feedback: List of (letter, state) tuples where state is
                  'correct', 'present', or 'absent'
    
    Returns:
        5-character base3 string (e.g., "21010")
        - '2' = correct (green)
        - '1' = present (yellow)
        - '0' = absent (gray)
    """
    pattern = []
    for _, state in feedback:
        if state == 'correct':
            pattern.append('2')
        elif state == 'present':
            pattern.append('1')
        else:  # absent
            pattern.append('0')
    
    return ''.join(pattern)
