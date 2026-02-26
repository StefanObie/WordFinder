# Wordle Self-Solver (Playwright)

Automatically plays the NYT Wordle puzzle using Playwright browser automation and intelligent word filtering.

## Features

- ✅ Loads pre-sorted Wordle word bank (by frequency and alphabetically)
- ✅ Configurable starting word
- ✅ Automated browser interaction with NYT Wordle using Playwright
- ✅ Two modes: Automation profile OR incognito mode
- ✅ Real-time feedback scraping from the page
- ✅ Smart candidate filtering based on green/yellow/gray tiles
- ✅ Displays progress (guesses, attempts, remaining candidates)
- ✅ Email summary via ZeptoMail with detailed stats

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers (including Edge):
```bash
playwright install msedge
```

3. Make sure you have Microsoft Edge installed on your system

4. **Create pre-sorted word bank** (required):
```bash
python sort_wordbank_once.py
```

This creates `wordle-word-bank-sorted.csv` with words sorted by frequency (most common first), then alphabetically. This only needs to be run once.

5. **(Optional) Email Configuration**: To receive summary emails via ZeptoMail:
   - Copy `.env.example` to `.env`
   - Get your ZeptoMail API token from https://www.zoho.com/zeptomail/
   - Edit `.env` and add your credentials:
   ```
   ZEPTOMAIL_TOKEN=your_api_token_here
   EMAIL_FROM=noreply@yourdomain.com
   EMAIL_TO=your.email@example.com
   ```

## Usage

### Basic Usage

Run the script:
```bash
cd self_solver
python self_solve.py
```

The script will:
1. Open Edge browser with your Profile 3
2. Navigate to NYT Wordle
3. Close any popups/modals
4. Automatically play the puzzle
5. Display progress in the terminal
6. Show the solution when found

### Configuration

Edit the configuration section at the top of `self_solve.py`:

```python
# Configuration Options
STARTING_WORD = "stair"  # Set to a specific word (e.g., "soare") or None to use first from sorted list
WORDLE_URL = "https://www.nytimes.com/games/wordle/index.html"
HEADLESS = False  # Set to True to hide the browser window
DELAY_AFTER_GUESS = 3  # Seconds to wait for animations (increase if tiles don't load in time)

# Browser Profile Configuration
USE_AUTOMATION_PROFILE = False  # True = use dedicated automation profile, False = incognito mode
AUTOMATION_PROFILE_PATH = r"C:\Users\steff\AppData\Local\Microsoft\Edge\User Data - Automation"
```

**Profile Modes:**
- **Incognito Mode** (`USE_AUTOMATION_PROFILE = False`): Clean temporary session, no login required
- **Automation Profile** (`USE_AUTOMATION_PROFILE = True`): Uses a dedicated Edge profile that persists
  - Your main Edge browser can stay open
  - Can maintain NYT login if needed
  - Separate from your normal browsing profile

### Example Output

```
==================================================
WORDLE SELF-SOLVER (Playwright)
==================================================

Loading word bank...
Loaded 12972 pre-sorted words from word bank

Initializing browser...
Using incognito mode (no profile)

Navigating to https://www.nytimes.com/games/wordle/index.html...
Waiting for page to load...
✓ Clicked Play button
✓ Closed modal

==================================================
Starting word: STAIR
Total candidates: 12972
==================================================

--- Attempt 1 ---
Guessing: STAIR
Candidates remaining: 12972
Submitted guess: STAIR
Feedback: 🟩⬜🟨⬜🟩

--- Attempt 2 ---
Guessing: SHALE
Candidates remaining: 47
Submitted guess: SHALE
Feedback: 🟩🟩🟩⬜🟩
Remaining candidates: SHAKE, SHAVE, SHADE

--- Attempt 3 ---
Guessing: SHAKE
Candidates remaining: 3
Submitted guess: SHAKE
Feedback: 🟩🟩🟩🟩🟩

==================================================
✅ Solved in 3 attempt(s)!
Answer: SHAKE
==================================================

🎉 Successfully solved today's Wordle!

Sending email summary...
✅ Email summary sent successfully

Keeping browser open for 3 seconds...
```

## How It Works

1. **Word Bank Loading**: Loads all valid Wordle words from `wordle-word-bank-sorted.csv` (pre-sorted by frequency and alphabetically)

2. **Browser Automation**: Uses Playwright to:
   - Open Edge browser (incognito or automation profile)
   - Navigate to NYT Wordle
   - Click Play button and close modals
   - Type guesses letter by letter
   - Submit with Enter key

3. **Feedback Scraping**: Parses the DOM to extract:
   - `data-state="correct"` → 🟩 Green (correct letter, correct position)
   - `data-state="present"` → 🟨 Yellow (correct letter, wrong position)
   - `data-state="absent"` → ⬜ Gray (letter not in word)

4. **Candidate Filtering**: After each guess, filters the word list by:
   - **Green constraints**: Letter must be in that exact position
   - **Yellow constraints**: Letter must be in word but not in that position
   - **Gray constraints**: Letter must not be in word (unless already green/yellow)

5. **Next Guess Selection**: Picks the first word from the filtered candidates (already sorted optimally)

6. **Email Summary**: Sends a ZeptoMail summary with:
   - Solved status and number of attempts
   - Each guess with visual feedback (🟩🟨⬜)
   - Remaining candidates before each guess
   - Final answer if solved

## Troubleshooting

### Browser doesn't open
- Ensure Microsoft Edge is installed
- Run `playwright install msedge` to install the Playwright Edge browser
- If you get an error about browsers not installed, run `playwright install`

### ImportError: No module named 'playwright' or 'requests'
- Install dependencies: `pip install -r requirements.txt`
- Then install browsers: `playwright install msedge`

### Email not sending
- Ensure `.env` file exists with valid ZeptoMail credentials
- Install email dependencies: `pip install requests python-dotenv`
- Check ZeptoMail API token is valid
- Verify EMAIL_FROM domain is configured in ZeptoMail

### Can't close modals
- Increase delay times in the code
- Manually close the modal and let the script continue

### Feedback not reading correctly
- Increase `DELAY_AFTER_GUESS` to allow more time for tile animations
- Check browser console for any JavaScript errors

### Script fails midway
- Check your internet connection
- NYT may have updated their HTML structure (update selectors in code)
- Some days may require manual intervention for edge cases

## Why Playwright?

Playwright offers several advantages over Selenium:
- ✅ Better profile handling - no network/driver download issues
- ✅ More reliable element interactions
- ✅ Built-in browser installation (`playwright install`)
- ✅ Better error handling and debugging
- ✅ Modern, actively maintained
- ✅ No separate driver executables needed

## Notes

- The script plays only **today's Wordle** puzzle
- You can only play once per day (NYT limitation)
- First word is configurable - popular choices: "soare", "roate", "raise", "arise", "stair"
- The word bank contains 12,972+ valid 5-letter words

## License

This is for educational purposes only.