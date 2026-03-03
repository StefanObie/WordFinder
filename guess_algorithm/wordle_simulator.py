"""
Wordle Simulator Module
Handles the mechanics of the Wordle game - pattern calculation, game simulation, and visualization.
"""

from typing import Dict, List, Callable
from guess_strategy import calculate_pattern


def pattern_to_string(pattern: int) -> str:
    """
    Convert pattern code to readable emoji string.
    
    Args:
        pattern: Integer pattern code (0-242)
        
    Returns:
        String like "🟩🟨⬜🟩🟩"
    """
    symbols = {0: '⬜', 1: '🟨', 2: '🟩'}
    result = []
    
    for i in range(5):
        digit = (pattern // (3 ** i)) % 3
        result.append(symbols[digit])
    
    return ''.join(result)


def get_remaining_candidates(
    candidates: List[str],
    guess: str,
    pattern: int
) -> List[str]:
    """
    Filter candidates based on pattern feedback.
    
    Args:
        candidates: Current list of possible answers
        guess: The word that was guessed
        pattern: The pattern code returned from the game
        
    Returns:
        Filtered list of candidates that match the pattern
    """
    new_candidates = []
    for candidate in candidates:
        if calculate_pattern(guess, candidate) == pattern:
            new_candidates.append(candidate)
    return new_candidates


def update_constraints(
    constraints: Dict,
    guess: str,
    pattern: int
) -> Dict:
    """
    Update hard mode constraints based on new feedback.
    
    Args:
        constraints: Current constraint dict {'green': {}, 'yellow': {}, 'gray': set()}
        guess: The word that was guessed
        pattern: The pattern code from the game
        
    Returns:
        Updated constraint dict
    """
    if not constraints:
        constraints = {'green': {}, 'yellow': {}, 'gray': set()}
    
    for i in range(5):
        digit = (pattern // (3 ** i)) % 3
        letter = guess[i]
        
        if digit == 2:  # Green
            constraints['green'][i] = letter
        elif digit == 1:  # Yellow
            if letter not in constraints['yellow']:
                constraints['yellow'][letter] = set()
            constraints['yellow'][letter].add(i)
        elif digit == 0:  # Gray
            # Only add to gray if not marked green/yellow elsewhere
            if letter not in constraints['green'].values():
                constraints['gray'].add(letter)
    
    return constraints


def simulate_game(
    answer: str,
    all_words: List[str],
    strategy_function: Callable,
    max_attempts: int = 6,
    verbose: bool = False
) -> Dict:
    """
    Simulate a complete Wordle game with a given strategy.
    
    Args:
        answer: The target word to guess
        all_words: Full word bank for guessing
        strategy_function: Function that returns optimal guess given (candidates, round, constraints, all_words)
        max_attempts: Maximum number of guesses allowed (default 6)
        verbose: If True, print detailed progress
        
    Returns:
        Dictionary with game result:
        {
            'solved': bool,
            'attempts': int,
            'answer': str,
            'guesses': [{'guess': str, 'pattern': int}, ...]
        }
    """
    candidates = all_words.copy()
    constraints = {'green': {}, 'yellow': {}, 'gray': set()}
    guesses = []
    
    if verbose:
        print(f"\nSimulating game with answer: {answer.upper()}")
        print("=" * 50)
    
    for attempt in range(1, max_attempts + 1):
        # Get optimal guess from strategy
        guess = strategy_function(
            remaining_candidate_words=candidates,
            round_num=attempt,
            constraints=constraints if attempt > 1 else None,
            all_words=all_words
        )
        
        # Calculate pattern
        pattern = calculate_pattern(guess, answer)
        
        if verbose:
            visual = pattern_to_string(pattern)
            print(f"Round {attempt}: {guess.upper()} {visual} ({len(candidates)} candidates)")
        
        guesses.append({'guess': guess, 'pattern': pattern})
        
        # Check if solved (all greens: 2+2*3+2*9+2*27+2*81 = 242)
        if pattern == 242:
            if verbose:
                print(f"✅ Solved in {attempt} guesses!")
            return {
                'solved': True,
                'attempts': attempt,
                'answer': answer,
                'guesses': guesses
            }
        
        # Filter candidates based on pattern
        candidates = get_remaining_candidates(candidates, guess, pattern)
        
        # Update constraints for hard mode
        constraints = update_constraints(constraints, guess, pattern)
        
        if not candidates:
            if verbose:
                print(f"❌ No candidates remaining after round {attempt}")
            break
    
    if verbose:
        print(f"❌ Failed to solve in {max_attempts} attempts")
    
    return {
        'solved': False,
        'attempts': max_attempts,
        'answer': answer,
        'guesses': guesses
    }
