"""
Wordle Self-Solver Script
Automatically plays NYT Wordle by:
1. Using pre-computed decision tree for optimal guesses
2. Scraping feedback from the page
3. Navigating the decision tree based on patterns
4. Repeating until solved or tree path not found
"""

import os
import time
from playwright.sync_api import sync_playwright
from discord.discord_logger import send_discord_message, MessageType

# Import modules
from scraper import click_play_button, close_modals, submit_guess, get_feedback, feedback_to_base3
from strategy.game_strategy import get_next_guess, WordNotInTreeError
from discord.discord_notifier import send_wordle_summary, send_missing_word_error

# ============= CONFIGURATION =============
MAX_ATTEMPTS = 6

# Browser Configuration
HEADLESS = True                 # Set to True to hide browser window
DELAY_AFTER_GUESS = 3           # Seconds to wait for tile animations
USE_AUTOMATION_PROFILE = True  # True = use automation profile, False = incognito mode

WORDLE_URL = "https://www.nytimes.com/games/wordle/index.html"
AUTOMATION_PROFILE_PATH = r"C:\Users\steff\AppData\Local\Microsoft\Edge\User Data - Automation"
# =========================================


def solve_wordle(page):
    """
    Main solving loop using decision tree strategy.
    Returns stats dictionary.
    """
    history = []
    
    print(f"\n{'='*50}")
    print("Using decision tree strategy")
    print("First guess: SALET (tree root)")
    print(f"{'='*50}\n")
    
    # Track stats for feedback
    stats = {
        'solved': False,
        'attempts': 0,
        'answer': None,
        'guesses': []
    }
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n--- Attempt {attempt} ---")
        
        # Get next guess from decision tree
        try:
            current_guess = get_next_guess(history)
            print(f"Decision tree suggests: {current_guess.upper()}")
        except WordNotInTreeError as e:
            print(f"\n⚠️ Word not in decision tree: {e}")
            print("Stopping game and sending Discord notification...")
            stats['attempts'] = attempt - 1
            send_missing_word_error(None, stats['guesses'])
            return stats
        
        # Submit guess
        try:
            submit_guess(page, current_guess, DELAY_AFTER_GUESS)
        except Exception as e:
            print(f"Failed to submit guess: {e}")
            stats['attempts'] = attempt
            return stats
        
        # Get feedback
        feedback = get_feedback(page, attempt)
        
        if not feedback:
            print("Could not read feedback from page")
            stats['attempts'] = attempt
            return stats
        
        # Convert to base3 pattern for decision tree
        pattern_base3 = feedback_to_base3(feedback)
        print(f"Pattern: {pattern_base3}")
        
        # Track this guess
        stats['guesses'].append({
            'guess': current_guess,
            'feedback': feedback,
            'pattern_base3': pattern_base3
        })
        
        # Check if solved (pattern is all 2s = all correct)
        if pattern_base3 == "22222":
            print(f"\n{'='*50}")
            print(f"✅ Solved in {attempt} attempt(s)!")
            print(f"Answer: {current_guess.upper()}")
            print(f"{'='*50}")
            stats['solved'] = True
            stats['attempts'] = attempt
            stats['answer'] = current_guess
            return stats
        
        # Add to history for next iteration
        history.append({
            'guess': current_guess,
            'pattern_base3': pattern_base3
        })
    
    print(f"\n{'='*50}")
    print("Failed to solve within 6 attempts")
    print(f"{'='*50}")
    stats['attempts'] = MAX_ATTEMPTS
    return stats


def main():
    """Main entry point."""
    print("=" * 50)
    print("WORDLE SELF-SOLVER (Decision Tree)")
    print("=" * 50)
    
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
            stats = solve_wordle(page)
            
            if stats['solved']:
                print("\n🎉 Successfully solved today's Wordle!")
            else:
                print("\n😞 Could not solve today's Wordle")
            
            # Send Discord summary
            print("\nSending Discord summary...")
            send_wordle_summary(stats)
            
            # Keep browser open briefly to see result
            print("\nKeeping browser open for 3 seconds...")
            time.sleep(3)
            
        except KeyboardInterrupt:
            send_discord_message("Interrupted by user", MessageType.WARNING)
        except Exception as e:
            send_discord_message("Error occurred in main flow", MessageType.ERROR, exception=e)
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
