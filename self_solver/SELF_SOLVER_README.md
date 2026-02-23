# Wordle Self-Solver

Automatically plays the NYT Wordle puzzle using browser automation and intelligent word filtering.

## Features

- ✅ Loads Wordle word bank sorted by frequency and alphabetically
- ✅ Configurable starting word
- ✅ Automated browser interaction with NYT Wordle
- ✅ Real-time feedback scraping from the page
- ✅ Smart candidate filtering based on green/yellow/gray tiles
- ✅ Displays progress (guesses, attempts, remaining candidates)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have Google Chrome installed on your system (Selenium will use Chrome WebDriver)

3. **(Optional but Recommended)** Create a pre-sorted word bank for faster loading:
```bash
python sort_wordbank_once.py
```

This creates `wordle-word-bank-sorted.csv` with words sorted by frequency (most common first), then alphabetically. This only needs to be run once and will speed up the self-solver significantly.

## Usage

### Basic Usage

Run the script from the backend directory:
```bash
python self_solve.py
```

The script will:
1. Open Chrome browser
2. Navigate to NYT Wordle
3. Close any popups/modals
4. Automatically play the puzzle
5. Display progress in the terminal
6. Show the solution when found

### Configuration

Edit the configuration section at the top of `self_solve.py`:

```python
# Configuration Options
STARTING_WORD = None  # Set to a specific word (e.g., "soare") or None to use the first from sorted list
WORDLE_URL = "https://www.nytimes.com/games/wordle/index.html"
HEADLESS = False  # Set to True to hide the browser window
DELAY_AFTER_GUESS = 3  # Seconds to wait for animations (increase if tiles don't load in time)
```

### Example Output

```
==================================================
WORDLE SELF-SOLVER
==================================================

Loading word bank...
Loaded 12972 words from word bank

Initializing browser...

Navigating to https://www.nytimes.com/games/wordle/index.html...
Waiting for page to load...
Closed modal

==================================================
Starting word: SOARE
Total candidates: 12972
==================================================


--- Attempt 1 ---
Guessing: SOARE
Candidates remaining: 12972
Submitted guess: SOARE
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

2. **Browser Automation**: Uses Selenium to:
   - Open Chrome browser
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
- Ensure Chrome is installed
- `webdriver-manager` will auto-download ChromeDriver on first run

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

## Notes

- The script plays only **today's Wordle** puzzle
- You can only play once per day (NYT limitation)
- First word is configurable - popular choices: "soare", "roate", "raise", "arise"
- The word bank contains 12,972+ valid 5-letter words

## License

This is for educational purposes only.