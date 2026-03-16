from __future__ import annotations

from typing import List, Optional

from .base import WordleSource
from .mock_source import MockWordleSource
from .nyt_source import NytWordleSource


def build_source(
    source_mode: str,
    word_list: List[str],
    headless: bool,
    delay_after_guess: float,
    browser_mode: str = "persistent",
    chromium_user_data_dir: str = "~/.config/chromium",
    mock_seed: Optional[int] = None,
    mock_answer: Optional[str] = None,
) -> WordleSource:
    mode = source_mode.strip().lower()
    if mode == "nyt":
        return NytWordleSource(
            headless=headless,
            delay_after_guess=delay_after_guess,
            browser_mode=browser_mode,
            chromium_user_data_dir=chromium_user_data_dir,
        )
    if mode == "mock":
        return MockWordleSource(word_list=word_list, random_seed=mock_seed, forced_answer=mock_answer)
    raise ValueError(f"Unsupported source mode: {source_mode}")
