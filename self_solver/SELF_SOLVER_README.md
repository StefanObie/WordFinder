# Wordle Self-Solver (Decision Tree)

Automatically plays the NYT Wordle puzzle using a pre-computed decision tree for optimal play with Playwright browser automation.

## Features

- ✅ Uses pre-computed decision tree for mathematically optimal guessing strategy
- ✅ Always starts with "SALET" (tree root - statistically optimal first guess)
- ✅ Automated browser interaction with NYT Wordle using Playwright
- ✅ Two modes: Automation profile OR incognito mode
- ✅ Real-time feedback scraping from the page
- ✅ Base3 pattern format throughout processing ("21010" for decision tree navigation)
- ✅ Displays progress (guesses, patterns)
- ✅ Discord notifications for game summary and errors

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

4. The decision tree (`salet.tree.hard.json`) is already included - no additional setup needed

5. **(Optional) Discord Configuration**: To receive game summaries and error notifications:
   - Create a `.env` file in the self_solver directory
   - Add your Discord webhook URL:
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
   DISCORD_USERNAME=Wordle Solver
   ```

## Usage

### Basic Usage

Run the script:
```bash
cd self_solver
python self_solve.py
```

The script will:
1. Open browser (automation profile or incognito)
2. Navigate to NYT Wordle
3. Close any popups/modals
4. Automatically play the puzzle using the decision tree
5. Display progress in the terminal with base3 patterns
6. Show the solution when found (or error if word not in tree)

### Configuration

Edit the configuration section at the top of `self_solve.py`:

```python
# Configuration Options
WORDLE_URL = "https://www.nytimes.com/games/wordle/index.html"
HEADLESS = True  # Set to True to hide the browser window
DELAY_AFTER_GUESS = 3  # Seconds to wait for animations (increase if tiles don't load in time)

# Browser Profile Configuration
USE_AUTOMATION_PROFILE = True  # True = use dedicated automation profile, False = incognito mode
AUTOMATION_PROFILE_PATH = r"C:\Users\steff\AppData\Local\Microsoft\Edge\User Data - Automation"
```

Note: Starting word is always "SALET" (decision tree root) and cannot be configured.

**Profile Modes:**
- **Incognito Mode** (`USE_AUTOMATION_PROFILE = False`): Clean temporary session, no login required
- **Automation Profile** (`USE_AUTOMATION_PROFILE = True`): Uses a dedicated Edge profile that persists
  - Your main Edge browser can stay open
  - Can maintain NYT login if needed
  - Separate from your normal browsing profile

### Example Output

```
==================================================
WORDLE SELF-SOLVER (Decision Tree)
==================================================

Initializing browser...
Using persistent Chromium profile (Raspberry Pi)

Navigating to https://www.nytimes.com/games/wordle/index.html...
✓ Clicked Play button
✓ Closed modal

==================================================
Using decision tree strategy
First guess: SALET (tree root)
==================================================

--- Attempt 1 ---
Decision tree suggests: SALET
Submitted guess: SALET
Pattern: 10012

--- Attempt 2 ---
Decision tree suggests: CREST
Submitted guess: CREST
Pattern: 00221

--- Attempt 3 ---
Decision tree suggests: GUEST
Submitted guess: GUEST
Pattern: 22222

==================================================
✅ Solved in 3 attempt(s)!
Answer: GUEST
==================================================

🎉 Successfully solved today's Wordle!

Sending Discord summary...

Keeping browser open for 3 seconds...
```

## How It Works

1. **Decision Tree Navigation**: Uses a pre-computed decision tree (`salet.tree.hard.json`) built from optimal Wordle solving strategies:
   - Tree starts with "SALET" as the mathematically optimal first guess
   - Each node contains the best next guess based on previous patterns
   - Tree was pre-computed for ~2,300 common Wordle answers

2. **Browser Automation**: Uses Playwright to:
   - Open browser (Chromium/Edge, incognito or automation profile)
   - Navigate to NYT Wordle
   - Click Play button and close modals
   - Type guesses letter by letter
   - Submit with Enter key

3. **Feedback Scraping** (`scraper.py`): Parses the DOM to extract:
   - `data-state="correct"` → state 'correct' (green tile)
   - `data-state="present"` → state 'present' (yellow tile)
   - `data-state="absent"` → state 'absent' (gray tile)
   - Converts to base3 pattern: "21010" where 2=correct, 1=present, 0=absent

4. **Pattern-Based Navigation** (`game_strategy.py`):
   - Maintains history of guesses with base3 patterns
   - Navigates decision tree using pattern keys
   - Each pattern leads to the next optimal guess
   - If tree path doesn't exist → raises `WordNotInTreeError`

5. **Error Handling**: When answer is not in tree:
   - Stops the game immediately
   - Sends Discord error notification with guess history
   - Provides instructions to add word to tree using preprocessing tools

6. **Discord Notifications** (`discord_notifier.py`): Sends summaries with:
   - Solved status and number of attempts
   - Each guess with visual emoji feedback (🟩🟨⬜)
   - Base3 patterns for debugging
   - Final answer if solved

## Module Architecture

The codebase is organized into separate modules with single responsibilities:

- **`self_solve.py`**: Main coordinator - browser setup, game loop
- **`scraper.py`**: Browser interaction - clicking, typing, scraping feedback
- **`strategy/`**: Decision tree strategy modules
  - **`game_strategy.py`**: High-level strategy - gets next guess from tree
  - **`guess_strategy.py`**: Core tree logic - loads and traverses tree
  - **`pattern_utils.py`**: Pattern conversion - base3 calculations
- **`discord/`**: Discord messaging modules
  - **`discord_notifier.py`**: High-level messaging - formats game summaries and errors (only place emojis are used)
  - **`discord_logger.py`**: Low-level Discord API - webhook integration
- **`preprocessing/`**: Tools for maintaining the decision tree
  - **`add_words_to_tree.py`**: Script to add missing words to the tree
  - **`salet.tree.hard.json`**: Pre-computed decision tree (10,560 lines)
  - **`sort_wordbank_once.py`**: Legacy word bank sorting script
  - **`wordle-word-bank-sorted.csv`**: Legacy sorted word list

## Preprocessing Tools

If a word is not in the decision tree, you can add it manually:

```bash
cd self_solver
python -m preprocessing.add_words_to_tree WORDHERE
```

This will:
1. Trace the optimal path for the word through simulated guesses
2. Add missing branches to the tree
3. Create a backup before modifying
4. Save the updated tree

The tree file is located at `preprocessing/salet.tree.hard.json` (10,560 lines, ~350KB).

## Limitations

⚠️ **Important**: The decision tree does NOT contain all possible 5-letter words.

- Tree was built from ~2,300 words in the Wordle solution bank
- NYT occasionally uses words not in the original solution set
- When an unknown word is encountered:
  - Game stops immediately
  - Discord error message sent with failure details
  - You must manually add the word using preprocessing tools
  - Re-run for the next day's puzzle

- If you want better coverage, you can pre-emptively add common words to the tree
- The solver is optimized for speed and known Wordle solutions, not all English words

## Troubleshooting

### Browser doesn't open
- Ensure Microsoft Edge is installed
- Run `playwright install msedge` to install the Playwright Edge browser
- If you get an error about browsers not installed, run `playwright install`

### ImportError: No module named 'playwright' or 'requests'
- Install dependencies: `pip install -r requirements.txt`
- Then install browsers: `playwright install msedge`

### Discord not sending
- Ensure `.env` file exists with valid Discord webhook URL
- Install dependencies: `pip install requests python-dotenv`
- Check webhook URL is valid and not expired
- Verify you have permission to post to the Discord channel

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
- First word is always "SALET" (decision tree root - non-configurable)
- Decision tree contains ~2,300 Wordle solution paths
- Base3 pattern format used throughout: "21010" (2=green, 1=yellow, 0=gray)
- Emojis (🟩🟨⬜) only used in Discord messages, not in processing logic

## License

This is for educational purposes only.