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
from datetime import datetime
from playwright.sync_api import sync_playwright

# ============= CONFIGURATION =============
STARTING_WORD = "stair"     # None = use first word from sorted list, or set manually.
WORDLE_URL = "https://www.nytimes.com/games/wordle/index.html"
HEADLESS = True            # Set to True to hide browser window
DELAY_AFTER_GUESS = 3      # Seconds to wait for tile animations

# Browser Profile Configuration
USE_AUTOMATION_PROFILE = True  # True = use automation profile, False = incognito mode
AUTOMATION_PROFILE_PATH = r"C:\Users\steff\AppData\Local\Microsoft\Edge\User Data - Automation"
# =========================================

def load_word_bank():
    """Load pre-sorted word bank (already sorted by frequency, then alphabetically)."""
    sorted_csv_path = os.path.join(os.path.dirname(__file__), 'wordle-word-bank-sorted.csv')
    
    with open(sorted_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        words = [row[0].lower().strip() for row in reader if row and row[0].strip()]
    
    print(f"Loaded {len(words)} pre-sorted words from word bank")
    return words

def click_play_button(page):
    """Click the Play button on the landing page if present."""
    try:
        print("Looking for Play button...")
        # Wait for Play button and click it
        play_button = page.locator("button[data-testid='Play']")
        if play_button.is_visible(timeout=5000):
            # Use click with no_wait_after to prevent page navigation issues
            play_button.click(no_wait_after=False)
            print("✓ Clicked Play button")
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
                        print("✓ Closed modal")
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

def submit_guess(page, word):
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
        time.sleep(DELAY_AFTER_GUESS)
        
    except Exception as e:
        print(f"Error submitting guess: {e}")
        raise

def get_feedback(page, row_number):
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

def solve_wordle(page, word_bank):
    """Main solving loop. Returns stats dictionary."""
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
    
    # Track stats for email
    stats = {
        'solved': False,
        'attempts': 0,
        'answer': None,
        'guesses': []  # List of {'guess': str, 'feedback': list, 'remaining': int, 'visual': str}
    }
    
    max_attempts = 6
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n--- Attempt {attempt} ---")
        
        # Choose next guess
        if attempt == 1:
            current_guess = first_guess
        else:
            if not candidates:
                print("❌ No valid candidates remaining!")
                return stats
            current_guess = candidates[0]
        
        print(f"Guessing: {current_guess.upper()}")
        print(f"Candidates remaining: {len(candidates)}")
        
        # Submit guess
        try:
            submit_guess(page, current_guess)
        except Exception as e:
            print(f"Failed to submit guess: {e}")
            return stats
        
        # Get feedback
        feedback = get_feedback(page, attempt)
        
        if not feedback:
            print("⚠️ Could not read feedback from page")
            return stats
        
        # Display feedback
        visual = display_feedback(feedback)
        print(f"Feedback: {visual}")
        
        # Track this guess
        stats['attempts'] = attempt
        stats['guesses'].append({
            'guess': current_guess.upper(),
            'feedback': feedback,
            'visual': visual,
            'remaining_before': len(candidates)
        })
        
        # Check if solved
        if all(state == 'correct' for _, state in feedback):
            print(f"\n{'='*50}")
            print(f"✅ Solved in {attempt} attempt(s)!")
            print(f"Answer: {current_guess.upper()}")
            print(f"{'='*50}")
            stats['solved'] = True
            stats['answer'] = current_guess.upper()
            return stats
        
        # Filter candidates for next round
        candidates = filter_candidates(candidates, current_guess, feedback)
        
        # Show remaining top candidates
        if candidates and len(candidates) <= 10:
            print(f"Remaining candidates: {', '.join(c.upper() for c in candidates[:10])}")
    
    print(f"\n{'='*50}")
    print("❌ Failed to solve within 6 attempts")
    print(f"{'='*50}")
    return stats

def send_wordle_summary(stats):
    """Send Wordle solving summary via ZeptoMail."""
    try:
        import requests
        from dotenv import load_dotenv
        load_dotenv()
        
        # ZeptoMail configuration
        zepto_token = os.getenv("ZEPTOMAIL_TOKEN")
        from_email = os.getenv("EMAIL_FROM")
        to_email = os.getenv("EMAIL_TO")
        
        if not all([zepto_token, from_email, to_email]):
            print("⚠️ Email configuration missing (ZEPTOMAIL_TOKEN, EMAIL_FROM, EMAIL_TO)")
            return
        
        # Build email content
        today = datetime.now().strftime("%B %d, %Y")
        
        if stats['solved']:
            subject = f"Wordle Solved - {stats['attempts']}/6 ({today})"
            status = f"SOLVED in {stats['attempts']} attempts"
        else:
            subject = f"Wordle Failed ({today})"
            status = f"NOT SOLVED after {stats['attempts']} attempts"
        
        # Build guess details
        guess_details = []
        for i, g in enumerate(stats['guesses'], 1):
            guess_details.append(f"Guess {i}: {g['guess']} {g['visual']}")
            guess_details.append(f"  Remaining candidates before guess: {g['remaining_before']}")
        
        message = f"""Wordle Summary - {today}

{status}
{f"Answer: {stats['answer']}" if stats['solved'] else ""}

Guesses:
{chr(10).join(guess_details)}

---
Auto-generated by Wordle Self-Solver
"""
        
        # ZeptoMail API request
        url = "https://api.zeptomail.com/v1.1/email"
        headers = {
            "Authorization": zepto_token,
            "Content-Type": "application/json"
        }
        payload = {
            "from": {"address": from_email},
            "to": [{"email_address": {"address": to_email}}],
            "subject": subject,
            "textbody": message
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("✅ Email summary sent successfully")
        else:
            print(f"⚠️ Email failed: {response.status_code} - {response.text}")
            
    except ImportError:
        print("⚠️ Install 'requests' and 'python-dotenv' to enable email: pip install requests python-dotenv")
    except Exception as e:
        print(f"⚠️ Email error: {e}")

def main():
    """Main entry point."""
    print("=" * 50)
    print("WORDLE SELF-SOLVER (Playwright)")
    print("=" * 50)
    
    # Load word bank
    print("\nLoading word bank...")
    word_bank = load_word_bank()
    
    if not word_bank:
        print("Error: No words loaded. Exiting.")
        return
    
    # Setup Playwright
    print("\nInitializing browser...")
    
    with sync_playwright() as p:
        try:
            # Launch Chrome (Raspberry Pi)
            chromium_path = "/usr/bin/chromium-browser" if os.path.exists("/usr/bin/chromium-browser") else "/usr/bin/chromium"
            if USE_AUTOMATION_PROFILE:
                print("Using persistent Chromium profile (Raspberry Pi)")
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=os.path.expanduser("~/.config/chromium"),
                    headless=HEADLESS,
                    executable_path=chromium_path,
                    args=["--disable-blink-features=AutomationControlled"],
                    no_viewport=True
                )
                page = browser.pages[0] if browser.pages else browser.new_page()
            else:
                print("Using incognito mode (no profile)")
                browser = p.chromium.launch(headless=HEADLESS, executable_path=chromium_path)
                context = browser.new_context()
                page = context.new_page()
            
            # Navigate to Wordle
            print(f"\nNavigating to {WORDLE_URL}...")
            page.goto(WORDLE_URL)
            
            # Wait for page to load
            time.sleep(1)
            
            # Click Play button and close modals
            click_play_button(page)
            close_modals(page)
            
            # Solve the puzzle
            stats = solve_wordle(page, word_bank)
            
            if stats['solved']:
                print("\n🎉 Successfully solved today's Wordle!")
            else:
                print("\n😞 Could not solve today's Wordle")
            
            # Send email summary
            print("\nSending email summary...")
            send_wordle_summary(stats)
            
            # Keep browser open briefly to see result
            print("\nKeeping browser open for 3 seconds...")
            time.sleep(3)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        except Exception as e:
            print(f"\n❌ Error occurred: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("\nClosing browser...")
            browser.close()

if __name__ == "__main__":
    main()