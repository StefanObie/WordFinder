# Wordle Self-Solver (Decision Tree)

Automatically plays the NYT Wordle puzzle using a pre-computed decision tree with optimal strategy and Playwright browser automation.

## Run Self-Solver

```bash
source venv/bin/activate
cd self_solver
python self_solve.py
```

The solver will:
1. Open Microsoft Edge browser
2. Navigate to NYT Wordle
3. Play the puzzle automatically using the decision tree
4. Send Discord notification with results (optional)

## How It Works: Decision Tree

The solver uses a pre-computed decision tree (`salet.tree.hard.json`) for mathematically optimal play:

- **Starts with SALET**: Always the first guess (root of tree, statistically optimal)
- **Base3 Patterns**: After each guess, feedback is converted to base3:
  - `2` = correct (green tile)
  - `1` = present (yellow tile)
  - `0` = absent (gray tile)
  - Example: `"21010"` means [green, yellow, absent, yellow, absent]
- **Tree Navigation**: Each pattern points to the next optimal guess
  - The tree contains ~2,300 Wordle solution paths
  - Each guess eliminates the most possible answers
  - This guarantees solving in ≤6 attempts

## Adding Words to the Tree

If the solver encounters a word not in the tree, add it manually:

```bash
cd self_solver
python -m preprocessing.add_words_to_tree WORDHERE
```

This will:
1. Simulate optimal play for that word
2. Add missing branches to the tree
3. Backup the tree before modifying
4. Save the updated tree to `preprocessing/salet.tree.hard.json`

## Discord Notifications

To receive game summaries and error alerts:

1. Create `.env` file in `self_solver/`:
```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
DISCORD_USERNAME=Wordle Solver
```

2. The solver will send:
   - ✅ Success notification with attempt count and answer
   - ❌ Error notification if word is not in tree
   - 🟩🟨⬜ Visual feedback for each guess
   - Base3 patterns for debugging

## License

Educational purposes only.