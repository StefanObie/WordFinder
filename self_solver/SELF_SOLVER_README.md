# Wordle Self Solver

The solver is now orchestrator-first.

- Main orchestration: self_solve.py
- The Discord send function is called only from self_solve.py
- Source mode is swappable through one global constant
- Guesses 1-5 use first matching word from sorted list filters
- Guess 6 always submits the scraped answer as fail-safe

## Run

```bash
source venv/bin/activate
cd self_solver
python self_solve.py
```

## Source Switch

Edit constants in self_solve.py:

- SOURCE_MODE = "nyt" for live NYT scraping
- SOURCE_MODE = "mock" for in-process testing

NYT scraper name used in notifications is scrape_nyt.

## Runtime Flow

1. Scrape answer first.
2. If answer cannot be scraped:
   - send Discord notification
   - exit script immediately
3. Ensure answer exists in preprocessing/wordle-word-bank-sorted.csv.
4. If answer was added to the sorted list, send Discord notification.
5. Attempts 1-5:
   - choose first word in sorted list matching all feedback constraints.
6. Attempt 6:
   - always enter scraped answer.
   - notify that the answer was entered.

## Mock Mode

Mock mode is in-process and picks a random answer from the sorted list by default.

Optional constants in self_solve.py:

- MOCK_SEED for deterministic random choice
- MOCK_FORCED_ANSWER to force a specific answer

## Discord Setup

Create self_solver/.env:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
DISCORD_USERNAME=Wordle Solver
```
