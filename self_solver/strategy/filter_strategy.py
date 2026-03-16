from __future__ import annotations

from typing import Dict, Iterable, Optional, Set

from .pattern_utils import calculate_pattern_base3


def matches_history(candidate: str, history: Iterable[Dict[str, str]]) -> bool:
    for entry in history:
        guess = entry["guess"]
        expected_pattern = entry["pattern_base3"]
        if calculate_pattern_base3(guess, candidate) != expected_pattern:
            return False
    return True


def first_matching_guess(
    sorted_word_list: Iterable[str],
    history: Iterable[Dict[str, str]],
    excluded_words: Optional[Set[str]] = None,
) -> Optional[str]:
    used = excluded_words or set()
    for word in sorted_word_list:
        if word in used:
            continue
        if matches_history(word, history):
            return word
    return None
