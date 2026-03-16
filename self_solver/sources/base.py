from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

Feedback = List[Tuple[str, str]]


class WordleSource(ABC):
    """Interface for a playable Wordle source."""

    name: str

    @abstractmethod
    def setup(self) -> None:
        """Initialize the source before gameplay."""

    @abstractmethod
    def scrape_answer(self) -> Optional[str]:
        """Return today's answer if available."""

    @abstractmethod
    def submit_guess(self, guess: str) -> Feedback:
        """Submit one guess and return feedback tuples."""

    @abstractmethod
    def close(self) -> None:
        """Clean up resources for this source."""
