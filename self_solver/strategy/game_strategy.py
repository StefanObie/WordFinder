"""
Wordle game strategy using pre-computed decision tree.

This module provides the core game strategy by navigating the decision tree
based on game history. It raises custom exceptions when words are not found
in the tree.
"""

from typing import List, Dict
from .guess_strategy import get_optimal_guess


class WordNotInTreeError(Exception):
    """Raised when the current game state is not in the decision tree."""
    pass


def get_next_guess(history: List[Dict]) -> str:
    """
    Get the optimal next guess based on game history using the decision tree.
    
    Args:
        history: List of previous guesses with format:
                 [{'guess': str, 'pattern_base3': str}, ...]
                 Empty list for first guess.
    
    Returns:
        The next word to guess (lowercase)
    
    Raises:
        WordNotInTreeError: If the current game state is not in the tree
    """
    try:
        # Call the decision tree strategy
        # Pass empty candidates list since tree doesn't use it
        guess = get_optimal_guess(
            remaining_candidate_words=[],
            history=history
        )
        return guess.lower()
    
    except KeyError as e:
        # Tree doesn't contain this path
        raise WordNotInTreeError(f"Decision tree path not found: {e}")
    
    except ValueError as e:
        # Some other value error
        raise WordNotInTreeError(f"Strategy error: {e}")
