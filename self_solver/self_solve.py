"""
Wordle Self-Solver Script
Automatically plays NYT Wordle by:
1. Loading sorted word bank (frequency + alphabetical)
2. Making strategic guesses
3. Scraping feedback from the page
4. Filtering candidates based on constraints
5. Repeating until solved
"""

import os
import csv
import time
import re
from collections import Counter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ============= CONFIGURATION =============
STARTING_WORD = "crane"  # None = use first word from sorted list, or set manually (e.g., "soare")
WORDLE_URL = "https://www.nytimes.com/games/wordle/index.html"
HEADLESS = False  # Set to True to hide browser window
DELAY_AFTER_GUESS = 3  # Seconds to wait for tile animations
# =========================================


def load_word_bank():
    """Load pre-sorted word bank (already sorted by frequency, then alphabetically)."""
    # Try to load pre-sorted word bank first (faster)
    sorted_csv_path = os.path.join(os.path.dirname(__file__), 'wordle-word-bank-sorted.csv')
    
    if os.path.exists(sorted_csv_path):
        # Load pre-sorted file
        try:
            with open(sorted_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                words = [row[0].lower().strip() for row in reader if row and row[0].strip()]
            print(f"Loaded {len(words)} pre-sorted words from word bank")
            return words
        except Exception as e:
            print(f"Error loading sorted file: {e}")
    
    # Fallback: load and sort on-the-fly if sorted file doesn't exist
    print("Pre-sorted file not found, sorting on-the-fly...")
    try:
        import nltk
        from nltk.corpus import brown
        
        try:
            brown_freq = Counter(w.lower() for w in brown.words() if w.isalpha())
        except LookupError:
            print("Brown corpus not found, using alphabetical sort only")
            brown_freq = Counter()
    except ImportError:
        print("NLTK not available, using alphabetical sort only")
        brown_freq = Counter()
    
    # Load Wordle word bank
    csv_path = os.path.join(os.path.dirname(__file__), 'wordle-word-bank.csv')
    words = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            words = [row[0].lower().strip() for row in reader if row and row[0].strip()]
    except FileNotFoundError:
        print(f"Error: Word bank file not found at {csv_path}")
        return []
    
    # Sort by frequency (descending), then alphabetically
    sorted_words = sorted(words, key=lambda w: (-brown_freq.get(w, 0), w))
    
    print(f"Loaded {len(sorted_words)} words from word bank")
    print("Tip: Run 'python sort_wordbank_once.py' to create a pre-sorted file for faster loading")
    return sorted_words


def setup_driver():
    """Initialize and configure Selenium WebDriver."""
    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    
    return driver


def click_play_button(driver):
    """Click the Play button on the landing page if present."""
    try:
        # Wait for the Play button to appear
        print("Looking for Play button...")
        wait = WebDriverWait(driver, 5)
        
        # Try to find and click the Play button
        play_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='Play']"))
        )
        play_button.click()
        print("✓ Clicked Play button")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"Play button not found (may already be on game page)")
        return False

def close_modals(driver):
    """Close any popups/modals that might appear."""
    try:
        # Wait a bit for modals to appear
        time.sleep(2)
        
        # Try to close instruction modal
        close_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Close'], button.Modal-module_closeIcon__TcEKb, svg[data-testid='icon-close']")
        for button in close_buttons:
            try:
                if button.is_displayed():
                    button.click()
                    print("✓ Closed modal")
                    time.sleep(0.5)
            except:
                pass
        
        # Sometimes need to click the game area to dismiss overlays
        try:
            game_area = driver.find_element(By.TAG_NAME, "body")
            game_area.click()
        except:
            pass
            
    except Exception as e:
        print(f"Note: Could not close modals: {e}")


def submit_guess(driver, word):
    """Type a word and submit it."""
    try:
        # Find the body or game element to send keys to
        game = driver.find_element(By.TAG_NAME, "body")
        
        # Type each letter
        for letter in word.upper():
            game.send_keys(letter)
            time.sleep(0.1)
        
        # Press Enter
        game.send_keys(Keys.RETURN)
        print(f"Submitted guess: {word.upper()}")
        
        # Wait for animations
        time.sleep(DELAY_AFTER_GUESS)
        
    except Exception as e:
        print(f"Error submitting guess: {e}")
        raise


def get_feedback(driver, row_number):
    """
    Scrape feedback from the specified row.
    Returns list of tuples: [(letter, state), ...]
    where state is 'correct', 'present', or 'absent'
    """
    try:
        # Find all rows
        rows = driver.find_elements(By.CSS_SELECTOR, "div[role='group'][aria-label^='Row']")
        
        if row_number > len(rows):
            raise Exception(f"Row {row_number} not found")
        
        current_row = rows[row_number - 1]
        
        # Find all tiles in this row
        tiles = current_row.find_elements(By.CSS_SELECTOR, "div[data-state]")
        
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


def display_feedback(feedback):
    """Display feedback with emoji visualization."""
    visual = ""
    for letter, state in feedback:
        if state == 'correct':
            visual += "🟩"
        elif state == 'present':
            visual += "🟨"
        else:
            visual += "⬜"
    return visual


def filter_candidates(candidates, guess, feedback):
    """
    Filter word list based on feedback from the guess.
    Returns filtered list of candidates.
    """
    # Build constraints
    green_positions = {}  # position -> letter
    yellow_letters = {}  # letter -> set of positions it's NOT in
    gray_letters = set()
    
    # Track letter counts in guess for multi-letter handling
    letter_counts = {}
    for i, (letter, state) in enumerate(feedback):
        if state in ['correct', 'present']:
            letter_counts[letter] = letter_counts.get(letter, 0) + 1
    
    # Process feedback
    for i, (letter, state) in enumerate(feedback):
        if state == 'correct':
            green_positions[i] = letter
        elif state == 'present':
            if letter not in yellow_letters:
                yellow_letters[letter] = set()
            yellow_letters[letter].add(i)
        elif state == 'absent':
            # Only mark as gray if this letter doesn't appear as green/yellow elsewhere
            if letter not in letter_counts:
                gray_letters.add(letter)
    
    # Filter candidates
    filtered = []
    for word in candidates:
        # Check green positions
        valid = True
        for pos, letter in green_positions.items():
            if word[pos] != letter:
                valid = False
                break
        
        if not valid:
            continue
        
        # Check yellow letters (must be in word, but not in excluded positions)
        for letter, excluded_positions in yellow_letters.items():
            if letter not in word:
                valid = False
                break
            # Check it's not in the excluded positions
            for pos in excluded_positions:
                if word[pos] == letter:
                    valid = False
                    break
            if not valid:
                break
        
        if not valid:
            continue
        
        # Check gray letters
        for letter in gray_letters:
            if letter in word:
                valid = False
                break
        
        if not valid:
            continue
        
        filtered.append(word)
    
    return filtered


def solve_wordle(driver, word_bank):
    """Main solving loop."""
    candidates = word_bank.copy()
    
    # Determine starting word
    if STARTING_WORD:
        first_guess = STARTING_WORD.lower()
    else:
        first_guess = candidates[0] if candidates else "soare"
    
    print(f"\n{'='*50}")
    print(f"Starting word: {first_guess.upper()}")
    print(f"Total candidates: {len(candidates)}")
    print(f"{'='*50}\n")
    
    max_attempts = 6
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n--- Attempt {attempt} ---")
        
        # Choose next guess
        if attempt == 1:
            current_guess = first_guess
        else:
            if not candidates:
                print("❌ No valid candidates remaining!")
                return False
            current_guess = candidates[0]
        
        print(f"Guessing: {current_guess.upper()}")
        print(f"Candidates remaining: {len(candidates)}")
        
        # Submit guess
        try:
            submit_guess(driver, current_guess)
        except Exception as e:
            print(f"Failed to submit guess: {e}")
            return False
        
        # Get feedback
        feedback = get_feedback(driver, attempt)
        
        if not feedback:
            print("⚠️ Could not read feedback from page")
            return False
        
        # Display feedback
        visual = display_feedback(feedback)
        print(f"Feedback: {visual}")
        
        # Check if solved
        if all(state == 'correct' for _, state in feedback):
            print(f"\n{'='*50}")
            print(f"✅ Solved in {attempt} attempt(s)!")
            print(f"Answer: {current_guess.upper()}")
            print(f"{'='*50}")
            return True
        
        # Filter candidates for next round
        candidates = filter_candidates(candidates, current_guess, feedback)
        
        # Show remaining top candidates
        if candidates and len(candidates) <= 10:
            print(f"Remaining candidates: {', '.join(c.upper() for c in candidates[:10])}")
    
    print(f"\n{'='*50}")
    print("❌ Failed to solve within 6 attempts")
    print(f"{'='*50}")
    return False


def main():
    """Main entry point."""
    print("=" * 50)
    print("WORDLE SELF-SOLVER")
    print("=" * 50)
    
    # Load word bank
    print("\nLoading word bank...")
    word_bank = load_word_bank()
    
    if not word_bank:
        print("Error: No words loaded. Exiting.")
        return
    
    # Setup browser
    print("\nInitializing browser...")
    driver = setup_driver()
    
    try:
        # Navigate to Wordle
        print(f"\nNavigating to {WORDLE_URL}...")
        driver.get(WORDLE_URL)
        
        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(3)
        
        # Click Play button if present
        click_play_button(driver)
        
        # Close any modals
        close_modals(driver)
        
        # Solve the puzzle
        success = solve_wordle(driver, word_bank)
        
        if success:
            print("\n🎉 Successfully solved today's Wordle!")
        else:
            print("\n😞 Could not solve today's Wordle")
        
        # Keep browser open for a few seconds to see the result
        print("\nKeeping browser open for 5 seconds...")
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nClosing browser...")
        driver.quit()


if __name__ == "__main__":
    main()