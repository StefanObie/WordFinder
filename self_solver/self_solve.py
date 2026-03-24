"""Main orchestrator for WordFinder self solver."""

from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from discord.discord_logger import MessageType, send_discord_message
from sources import build_source
from strategy.filter_strategy import first_matching_guess

# ============= CONFIGURATION =============
SOURCE_MODE = "nyt"  # Options: nyt, mock
SCRAPER_NAME = "scrape_nyt"
MAX_ATTEMPTS = 6
HEADLESS = True
DELAY_AFTER_GUESS = 3.0
DEBUG_LOGS = True
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE = LOG_DIR / "self_solver.log"

# NYT browser settings
BROWSER_MODE = "persistent"  # Options: persistent, incognito
CHROMIUM_USER_DATA_DIR = "~/.config/chromium"

# Mock-only settings
MOCK_SEED = None
MOCK_FORCED_ANSWER = None

WORD_BANK_PATH = Path(__file__).resolve().parent / "preprocessing" / "wordle-word-bank-sorted.csv"
# =========================================

Feedback = List[Tuple[str, str]]


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("self_solver")
    logger.setLevel(logging.DEBUG if DEBUG_LOGS else logging.INFO)

    if logger.handlers:
        return

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG if DEBUG_LOGS else logging.INFO)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False


def debug_log(message: str) -> None:
    if DEBUG_LOGS:
        logging.getLogger("self_solver").debug(message)


def load_sorted_word_list(path: Path) -> List[str]:
    debug_log(f"Loading sorted word list from: {path}")
    if not path.exists():
        raise FileNotFoundError(f"Word list not found: {path}")

    words: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        word = line.strip().lower()
        if len(word) == 5 and word.isalpha():
            words.append(word)
    debug_log(f"Loaded {len(words)} candidate words")
    return words


def ensure_answer_in_sorted_word_list(path: Path, words: List[str], answer: str) -> bool:
    if answer in words:
        debug_log(f"Answer {answer.upper()} already present in sorted list")
        return False
    debug_log(f"Answer {answer.upper()} missing from sorted list, appending now")
    words.append(answer)
    path.write_text("\n".join(words) + "\n", encoding="utf-8")
    return True


def feedback_to_base3(feedback: Feedback) -> str:
    state_to_digit = {
        "absent": "0",
        "present": "1",
        "correct": "2",
    }
    return "".join(state_to_digit[state] for _, state in feedback)


def feedback_to_emoji(feedback: Feedback) -> str:
    state_to_emoji = {
        "absent": "⬜",
        "present": "🟨",
        "correct": "🟩",
    }
    return "".join(state_to_emoji[state] for _, state in feedback)


def build_summary_message(stats: Dict) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    title = f"Wordle Solver Result ({today})"
    status = "✅ Solved" if stats["solved"] else "❌ Failed"

    lines = [f"**{title}**", status]
    lines.append(f"Source: {stats['source_name']} ({stats['source_mode']})")
    lines.append(f"Attempts: {stats['attempts']}/6")
    lines.append(f"Answer: `{stats['answer'].upper() if stats['answer'] else 'UNKNOWN'}`")
    lines.append("")
    lines.append("Guesses:")

    for idx, guess_entry in enumerate(stats["guesses"], start=1):
        row = feedback_to_emoji(guess_entry["feedback"])
        forced = " [forced-answer]" if guess_entry.get("forced") else ""
        lines.append(f"{idx}. `{guess_entry['guess'].upper()}` {row}{forced}")

    return "\n".join(lines)


def solve_game() -> int:
    configure_logging()
    debug_log("Starting solver orchestration")
    debug_log(f"Writing logs to: {LOG_FILE}")
    debug_log(
        f"Configuration: source_mode={SOURCE_MODE}, max_attempts={MAX_ATTEMPTS}, "
        f"headless={HEADLESS}, delay_after_guess={DELAY_AFTER_GUESS}, browser_mode={BROWSER_MODE}"
    )
    words = load_sorted_word_list(WORD_BANK_PATH)
    source = build_source(
        source_mode=SOURCE_MODE,
        word_list=words,
        headless=HEADLESS,
        delay_after_guess=DELAY_AFTER_GUESS,
        browser_mode=BROWSER_MODE,
        chromium_user_data_dir=CHROMIUM_USER_DATA_DIR,
        mock_seed=MOCK_SEED,
        mock_answer=MOCK_FORCED_ANSWER,
    )

    stats = {
        "solved": False,
        "attempts": 0,
        "answer": None,
        "guesses": [],
        "source_mode": SOURCE_MODE,
        "source_name": source.name if SOURCE_MODE == "mock" else SCRAPER_NAME,
    }

    history: List[Dict[str, str]] = []
    used_words = set()

    debug_log(f"Built source implementation: {source.name}")
    debug_log("Setting up source")
    source.setup()
    try:
        debug_log("Scraping answer")
        answer = source.scrape_answer()
        if not answer:
            debug_log("Answer scraping failed, sending Discord error and exiting")
            send_discord_message(
                (
                    "Wordle answer scraping failed. "
                    f"Source mode: {SOURCE_MODE}, scraper: {SCRAPER_NAME}. "
                    "Solver stopped before guessing."
                ),
                MessageType.ERROR,
            )
            return 1

        answer = answer.lower()
        stats["answer"] = answer
        debug_log(f"Scraped answer: {answer.upper()}")

        added = ensure_answer_in_sorted_word_list(WORD_BANK_PATH, words, answer)
        if added:
            debug_log("Answer added to sorted list, sending Discord warning")
            send_discord_message(
                (
                    "Today's answer was missing from sorted word list and has been added: "
                    f"`{answer.upper()}`"
                ),
                MessageType.WARNING,
            )

        for attempt in range(1, MAX_ATTEMPTS + 1):
            force_answer_guess = attempt == MAX_ATTEMPTS and not stats["solved"]
            debug_log(f"Attempt {attempt} started")
            if force_answer_guess:
                guess = answer
                debug_log(f"Attempt {attempt}: forcing answer guess {guess.upper()}")
            else:
                guess = first_matching_guess(words, history, used_words)
                if not guess:
                    debug_log("No matching candidate found, sending Discord error")
                    send_discord_message(
                        (
                            "No candidate matched current filtering constraints before attempt 6. "
                            "Solver stopped."
                        ),
                        MessageType.ERROR,
                    )
                    stats["attempts"] = attempt - 1
                    break
                debug_log(f"Attempt {attempt}: selected candidate {guess.upper()}")

            debug_log(f"Submitting guess {guess.upper()}")
            feedback = source.submit_guess(guess)
            if len(feedback) != 5:
                debug_log(
                    f"Invalid feedback length ({len(feedback)}) for guess {guess.upper()} on attempt {attempt}"
                )
                send_discord_message(
                    (
                        f"Invalid feedback length ({len(feedback)}/5) for guess `{guess.upper()}` "
                        f"on attempt {attempt}. Solver stopped. "
                        f"Check log file: `{LOG_FILE}`"
                    ),
                    MessageType.ERROR,
                )
                stats["attempts"] = attempt
                break

            pattern_base3 = feedback_to_base3(feedback)
            debug_log(f"Attempt {attempt}: feedback pattern {pattern_base3} / {feedback_to_emoji(feedback)}")
            guess_entry = {
                "guess": guess,
                "feedback": feedback,
                "pattern_base3": pattern_base3,
                "forced": force_answer_guess,
            }
            stats["guesses"].append(guess_entry)
            used_words.add(guess)
            stats["attempts"] = attempt

            if pattern_base3 == "22222":
                stats["solved"] = True
                debug_log(f"Puzzle solved on attempt {attempt} with guess {guess.upper()}")
                break

            history.append({"guess": guess, "pattern_base3": pattern_base3})
            debug_log(f"Attempt {attempt} complete; history size now {len(history)}")

        if stats["solved"] and stats["attempts"] <= 5:
            debug_log("Solved on or before attempt 5, sending success summary")
            send_discord_message(build_summary_message(stats), MessageType.SUCCESS)
        elif stats["solved"] and stats["attempts"] == 6:
            debug_log("Solved on attempt 6 via forced answer, sending warning + summary")
            send_discord_message(
                (
                    "Solved on guess 6 using forced answer entry. "
                    f"Entered answer: `{answer.upper()}`."
                ),
                MessageType.WARNING,
            )
            send_discord_message(build_summary_message(stats), MessageType.SUCCESS)
        else:
            debug_log("Puzzle not solved, sending failure summary")
            send_discord_message(build_summary_message(stats), MessageType.ERROR)

        debug_log(f"Run finished with solved={stats['solved']} attempts={stats['attempts']}")
        return 0 if stats["solved"] else 1
    finally:
        debug_log("Closing source")
        source.close()


def main() -> None:
    exit_code = solve_game()
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
