"""
Discord notification utilities for Wordle self-solver.

This module handles all Discord messaging, including game summaries
and error notifications. It's the only place where emoji conversion happens.
"""

from datetime import datetime
from typing import List, Tuple, Dict
from .discord_logger import send_discord_message, MessageType


def feedback_to_emoji(feedback: List[Tuple[str, str]]) -> str:
    """
    Convert feedback tuples to emoji visualization for Discord.
    
    Args:
        feedback: List of (letter, state) tuples where state is
                  'correct', 'present', or 'absent'
    
    Returns:
        String of emojis (e.g., "🟩🟨⬜🟩⬜")
    """
    visual = ""
    for _, state in feedback:
        if state == 'correct':
            visual += "🟩"
        elif state == 'present':
            visual += "🟨"
        else:  # absent
            visual += "⬜"
    return visual


def send_wordle_summary(stats: Dict):
    """
    Send Wordle solving summary to Discord webhook.
    
    Args:
        stats: Dictionary with keys:
            - 'solved': bool
            - 'attempts': int
            - 'answer': str
            - 'guesses': list of dicts with 'guess', 'feedback', 'remaining_before'
    """
    today = datetime.now().strftime("%B %d, %Y")
    
    if stats['solved']:
        title = f"Wordle Solved - {stats['attempts']}/6 ({today})"
        status = f"✅ SOLVED in {stats['attempts']} attempts"
        msg_type = MessageType.SUCCESS
    else:
        title = f"Wordle Failed ({today})"
        status = f"❌ NOT SOLVED after {stats['attempts']} attempts"
        msg_type = MessageType.ERROR

    # Build Wordle-Style Grid with emojis
    grid_lines = []
    for g in stats['guesses']:
        # Convert feedback tuples to emojis
        visual = feedback_to_emoji(g['feedback'])
        grid_lines.append(visual)
    grid = '\n'.join(grid_lines)

    # Build guess details
    guess_details = []
    for i, g in enumerate(stats['guesses'], 1):
        # Include answer if available, otherwise empty
        answer_str = stats.get('answer', '???').upper()
        guess_details.append(f"Guess {i}: `{g['guess'].upper()}`")

    answer_line = f"**Answer:** `{stats.get('answer', '???').upper()}`"

    message = f"**{title}**\n\n{status}\n{answer_line}\n\n**Guesses:**\n{grid}\n\n" + '\n'.join(guess_details)
    send_discord_message(message, msg_type)


def send_missing_word_error(answer: str, guesses: List[Dict]):
    """
    Send error notification when a word is not in the decision tree.
    
    Args:
        answer: The answer word that was not found (may be None if unknown)
        guesses: List of guess dictionaries with 'guess', 'feedback', 'pattern_base3'
    """
    today = datetime.now().strftime("%B %d, %Y")
    title = f"⚠️ Word Not In Decision Tree ({today})"
    
    # Build guess history with emojis
    grid_lines = []
    guess_details = []
    for i, g in enumerate(guesses, 1):
        visual = feedback_to_emoji(g['feedback'])
        grid_lines.append(visual)
        guess_details.append(f"Guess {i}: `{g['guess'].upper()}` (Pattern: `{g['pattern_base3']}`)")
    
    grid = '\n'.join(grid_lines)
    
    answer_info = f"**Unknown Answer**" if not answer else f"**Likely Answer:** `{answer.upper()}`"
    
    message = (
        f"**{title}**\n\n"
        f"The decision tree does not contain a path for this word.\n"
        f"{answer_info}\n\n"
        f"**Guess History:**\n{grid}\n\n"
        + '\n'.join(guess_details) +
        f"\n\n**Action Required:** Add this word to the tree using:\n"
        f"```\ncd self_solver\npython -m preprocessing.add_words_to_tree {answer.upper() if answer else 'WORD'}\n```"
    )
    
    send_discord_message(message, MessageType.ERROR)
