# Wordle Self-Solver (Playwright)

Automatically plays the NYT Wordle puzzle using Playwright browser automation and intelligent word filtering.

## Features

- ✅ Loads Wordle word bank sorted by frequency and alphabetically
- ✅ Configurable starting word
- ✅ Automated browser interaction with NYT Wordle using Playwright
- ✅ Uses your Edge profile (maintains login, extensions, history)
- ✅ Real-time feedback scraping from the page
- ✅ Smart candidate filtering based on green/yellow/gray tiles
- ✅ Displays progress (guesses, attempts, remaining candidates)

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

4. **(Optional but Recommended)** Create a pre-sorted word bank for faster loading:
```bash
python sort_wordbank_once.py
```

This creates `wordle-word-bank-sorted.csv` with words sorted by frequency (most common first), then alphabetically. This only needs to be run once and will speed up the self-solver significantly.

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
STARTING_WORD = "stair"  # Set to a specific word (e.g., "soare") or None to use the first from sorted list
WORDLE_URL = "https://www.nytimes.com/games/wordle/index.html"
HEADLESS = False  # Set to True to hide the browser window
DELAY_AFTER_GUESS = 3  # Seconds to wait for animations (increase if tiles don't load in time)

# Edge Profile Configuration
USE_EDGE_PROFILE = True  # Set to True to use your main Edge profile (with login, extensions, etc.)
EDGE_PROFILE_PATH = r"C:\Users\steff\AppData\Local\Microsoft\Edge\User Data\Profile 3"
```

**Important Notes About Using Your Edge Profile:**
- **Edge must be completely closed** before running the script when `USE_EDGE_PROFILE = True`
- Using your profile means the script will have access to:
  - Your NYT login (if you're signed in)
  - Your Wordle game history and stats
  - Your browser extensions
  - Your cookies and site preferences
- The profile path should point directly to the profile folder (e.g., `Profile 3`)
- To find your profile path, type `edge://version` in Edge and copy the "Profile path"
- Example paths:
  - `C:\Users\YourName\AppData\Local\Microsoft\Edge\User Data\Default`
  - `C:\Users\YourName\AppData\Local\Microsoft\Edge\User Data\Profile 1`
  - `C:\Users\YourName\AppData\Local\Microsoft\Edge\User Data\Profile 3`

### Example Output

```
==================================================
WORDLE SELF-SOLVER (Playwright)
==================================================

Loading word bank...
Loaded 12972 words from word bank

Initializing browser...
Using Edge profile: C:\Users\steff\AppData\Local\Microsoft\Edge\User Data\Profile 3
Note: Make sure Edge is closed before running this script!

Navigating to https://www.nytimes.com/games/wordle/index.html...
Waiting for page to load...
Closed modal

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
```

## How It Works

1. **Word Bank Loading**: Loads all valid Wordle words from `wordle-word-bank.csv` and sorts them by:
   - Frequency (using NLTK Brown corpus)
   - Alphabetically (as secondary sort)

2. **Browser Automation**: Uses Playwright to:
   - Open Edge browser with your profile (maintains login state, extensions, etc.)
   - Navigate to NYT Wordle
   - Close instruction modals
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

## Troubleshooting

### Browser doesn't open
- Ensure Microsoft Edge is installed
- Run `playwright install msedge` to install the Playwright Edge browser
- If you get an error about browsers not installed, run `playwright install`

### "Profile in use" or "Browser context is locked" error
- **Close all Edge browser windows completely** before running the script
- Check Task Manager to ensure no `msedge.exe` processes are running
- Playwright needs exclusive access to the profile directory
- If the error persists, try setting `USE_EDGE_PROFILE = False` to run with a temporary profile

### ImportError: No module named 'playwright'
- Install Playwright: `pip install playwright`
- Then install browsers: `playwright install msedge`

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