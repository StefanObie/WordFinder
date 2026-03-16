from __future__ import annotations

import random
from typing import List, Optional

from strategy.pattern_utils import calculate_pattern_base3

from .base import Feedback, WordleSource


class MockWordleSource(WordleSource):
    """In-process mock Wordle source used for testing solver behavior."""

    name = "mock_wordle"

    @staticmethod
    def _log(message: str) -> None:
        print(f"[DEBUG][mock_source] {message}")

    def __init__(
        self,
        word_list: List[str],
        random_seed: Optional[int] = None,
        forced_answer: Optional[str] = None,
    ):
        if not word_list:
            raise ValueError("Mock source requires a non-empty word list")
        self.word_list = word_list
        self.random_seed = random_seed
        self.forced_answer = forced_answer.lower() if forced_answer else None
        self.answer: Optional[str] = None

    def setup(self) -> None:
        if self.forced_answer:
            self.answer = self.forced_answer
            self._log(f"Using forced mock answer: {self.answer.upper()}")
            return
        rng = random.Random(self.random_seed)
        self.answer = rng.choice(self.word_list)
        self._log(f"Selected random mock answer: {self.answer.upper()}")

    def scrape_answer(self) -> Optional[str]:
        return self.answer

    def submit_guess(self, guess: str) -> Feedback:
        if not self.answer:
            raise RuntimeError("Mock source has no active answer")

        pattern = calculate_pattern_base3(guess, self.answer)
        self._log(f"Guess {guess.upper()} produced pattern {pattern}")
        states = {
            "0": "absent",
            "1": "present",
            "2": "correct",
        }
        return [(guess[i], states[pattern[i]]) for i in range(5)]

    def close(self) -> None:
        return
