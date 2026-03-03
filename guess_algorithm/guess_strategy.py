"""
Guess Strategy Module
Implements various strategies for selecting optimal Wordle guesses.

Strategies:
- Entropy Maximization: Choose guesses that maximize information gain
- Minimax: Choose guesses that minimize worst-case remaining candidates
- Hybrid: Use entropy early, switch to minimax for guaranteed convergence
- Hard Mode: Only suggest guesses that comply with hard mode constraints
"""

import math
from collections import defaultdict, Counter
from typing import List, Dict, Set

# ============= CONFIGURATION =============
# Precomputed optimal first guess (maximizes entropy across all 12,973 words)
OPTIMAL_FIRST_GUESS = "salet"  # Expected avg: ~3.7 guesses

# Strategy switching threshold
MINIMAX_THRESHOLD = 50  # Switch to minimax when candidates <= this number
MAX_GUESS_EVALUATIONS = 100  # Maximum guesses to evaluate (for performance)
FAST_EVALUATION_LIMIT = 20  # For candidates >200, only evaluate this many guesses

# Hard mode enforcement
HARD_MODE = True  # If True, only consider guesses that use all known information
# =========================================


def calculate_pattern(guess: str, answer: str) -> int:
    """
    Calculate the pattern (feedback) for a guess against an answer.
    Returns base-3 encoded integer where:
    - 0 = gray (absent)
    - 1 = yellow (present but wrong position)
    - 2 = green (correct position)
    
    Handles duplicate letters correctly per Wordle rules:
    - Greens are assigned first
    - Yellows only for remaining unmatched letters in answer
    
    Args:
        guess: The guessed word (5 letters)
        answer: The target word (5 letters)
        
    Returns:
        Integer pattern code (0-242, since 3^5 = 243 possible patterns)
    """
    pattern = [0] * 5  # Start with all gray
    answer_letter_counts = Counter(answer)
    
    # First pass: Mark all greens (exact matches) and reduce counts
    for i in range(5):
        if guess[i] == answer[i]:
            pattern[i] = 2  # Green
            answer_letter_counts[guess[i]] -= 1
    
    # Second pass: Mark yellows (present but wrong position)
    for i in range(5):
        if pattern[i] == 0:  # Not already green
            if answer_letter_counts.get(guess[i], 0) > 0:
                pattern[i] = 1  # Yellow
                answer_letter_counts[guess[i]] -= 1
    
    # Convert to base-3 integer (optimized)
    return pattern[0] + pattern[1] * 3 + pattern[2] * 9 + pattern[3] * 27 + pattern[4] * 81


def get_pattern_distribution(guess: str, candidates: List[str]) -> Dict[int, int]:
    """
    Calculate pattern distribution for a guess across all candidates.
    
    Args:
        guess: The word to evaluate
        candidates: List of possible answer words
        
    Returns:
        Dictionary mapping pattern codes to frequency counts
    """
    pattern_counts = defaultdict(int)
    
    for answer in candidates:
        pattern = calculate_pattern(guess, answer)
        pattern_counts[pattern] += 1
    
    return pattern_counts


def calculate_entropy(guess: str, candidates: List[str]) -> float:
    """
    Calculate information entropy (in bits) for a guess.
    Higher entropy = more information gained on average.
    
    Entropy = -Σ(p * log2(p)) where p is probability of each pattern
    
    Args:
        guess: The word to evaluate
        candidates: List of possible answer words
        
    Returns:
        Entropy in bits (higher is better)
    """
    if not candidates:
        return 0.0
    
    pattern_counts = get_pattern_distribution(guess, candidates)
    total = len(candidates)
    entropy = 0.0
    
    for count in pattern_counts.values():
        if count > 0:
            probability = count / total
            entropy -= probability * math.log2(probability)
    
    return entropy


def calculate_minimax_score(guess: str, candidates: List[str]) -> int:
    """
    Calculate worst-case remaining candidates (minimax score).
    Lower score = better worst-case guarantee.
    
    Args:
        guess: The word to evaluate
        candidates: List of possible answer words
        
    Returns:
        Maximum group size (worst case remaining candidates)
    """
    if not candidates:
        return 0
    
    pattern_counts = get_pattern_distribution(guess, candidates)
    
    # Return the size of the largest group (worst case)
    return max(pattern_counts.values()) if pattern_counts else len(candidates)


def calculate_expected_remaining(guess: str, candidates: List[str]) -> float:
    """
    Calculate expected number of remaining candidates after this guess.
    Lower is better.
    
    Args:
        guess: The word to evaluate
        candidates: List of possible answer words
        
    Returns:
        Expected remaining candidates
    """
    if not candidates:
        return 0.0
    
    pattern_counts = get_pattern_distribution(guess, candidates)
    total = len(candidates)
    expected = 0.0
    
    for count in pattern_counts.values():
        probability = count / total
        expected += probability * count
    
    return expected


def satisfies_hard_mode(guess: str, constraints: Dict) -> bool:
    """
    Check if a guess satisfies hard mode constraints.
    In hard mode, must use all known green letters in correct positions
    and include all known yellow letters.
    
    Args:
        guess: Word to check
        constraints: Dictionary with 'green', 'yellow', 'gray' constraints
        
    Returns:
        True if guess satisfies hard mode rules
    """
    if not constraints:
        return True
    
    green = constraints.get('green', {})
    yellow = constraints.get('yellow', {})
    
    # Check all green positions are satisfied
    for pos, letter in green.items():
        if guess[pos] != letter:
            return False
    
    # Check all yellow letters are included (but not in excluded positions)
    for letter, excluded_positions in yellow.items():
        if letter not in guess:
            return False
        # Ensure letter is not in any excluded position
        for pos in excluded_positions:
            if pos < len(guess) and guess[pos] == letter:
                return False
    
    return True


def filter_hard_mode_guesses(all_words: List[str], constraints: Dict) -> List[str]:
    """
    Filter word list to only include valid hard mode guesses.
    
    Args:
        all_words: Full word list to filter
        constraints: Dictionary with 'green', 'yellow', 'gray' constraints
        
    Returns:
        Filtered list of words satisfying hard mode
    """
    if not constraints:
        return all_words
    
    return [word for word in all_words if satisfies_hard_mode(word, constraints)]


def get_optimal_guess(
    remaining_candidate_words: List[str],
    round_num: int = 1,
    constraints: Dict = None,
    all_words: List[str] = None
) -> str:
    """
    Get the optimal next guess using hybrid entropy-minimax strategy.
    
    Strategy:
    - Round 1: Return precomputed optimal first guess
    - Many candidates (>50) or early game: Use entropy maximization
    - Few candidates (≤50) or late game: Use minimax for guaranteed convergence
    - Hard mode: Only consider guesses that satisfy all constraints
    
    Args:
        remaining_candidate_words: List of words that could still be the answer
        round_num: Current round number (1-6), default 1
        constraints: Optional dict with 'green', 'yellow', 'gray' constraints for hard mode
        all_words: Optional full word list for guess pool (defaults to candidates)
        
    Returns:
        Optimal guess word
    """
    if not remaining_candidate_words:
        raise ValueError("No remaining candidates")
    
    # Round 1: Use precomputed optimal opener
    if round_num == 1 and not constraints:
        return OPTIMAL_FIRST_GUESS
    
    # If only one candidate left, guess it
    if len(remaining_candidate_words) == 1:
        return remaining_candidate_words[0]
    
    # Special case: If very few candidates (<=6) in late game, just guess from candidates
    # This handles hard mode edge cases where all candidates share same pattern
    if len(remaining_candidate_words) <= 6 and round_num >= 3:
        return remaining_candidate_words[0]
    
    # Determine guess pool (all words vs just candidates)
    if all_words is None:
        guess_pool = remaining_candidate_words
    else:
        guess_pool = all_words
    
    # Apply hard mode filter if enabled
    if HARD_MODE and constraints:
        guess_pool = filter_hard_mode_guesses(guess_pool, constraints)
        # Fallback if no valid guesses found (shouldn't happen)
        if not guess_pool:
            guess_pool = remaining_candidate_words
    
    # Decide strategy based on candidate count and round number
    # Switch to minimax earlier to guarantee convergence within 6 attempts
    use_minimax = (
        len(remaining_candidate_words) <= MINIMAX_THRESHOLD or 
        round_num >= 3 or  # Switch to minimax by round 3
        round_num >= 2 and len(remaining_candidate_words) <= 200  # Or round 2 with <200 candidates
    )
    
    best_guess = None
    best_score = float('inf') if use_minimax else float('-inf')
    
    # For efficiency, limit evaluation pool size based on candidate count
    if len(remaining_candidate_words) > 200:
        # Very large pool: only evaluate top frequency words and first few candidates
        max_eval = min(FAST_EVALUATION_LIMIT, len(remaining_candidate_words))
        # Take first 5 candidates plus top frequency words
        evaluation_pool = remaining_candidate_words[:5] + guess_pool[:max_eval]
    elif len(remaining_candidate_words) > 50:
        # Medium pool: evaluate candidates + sample of other words
        candidates_set = set(remaining_candidate_words)
        other_words = [w for w in guess_pool[:MAX_GUESS_EVALUATIONS] if w not in candidates_set]
        evaluation_pool = remaining_candidate_words + other_words
    else:
        # Small pool: Can afford to evaluate more, but still limit to some  
        evaluation_pool = guess_pool[:MAX_GUESS_EVALUATIONS] if len(guess_pool) > MAX_GUESS_EVALUATIONS else guess_pool
    
    # Remove duplicates while preserving order
    seen = set()
    evaluation_pool = [x for x in evaluation_pool if not (x in seen or seen.add(x))]
    
    # Evaluate each potential guess
    for guess in evaluation_pool:
        if use_minimax:
            # Minimax: minimize worst case
            score = calculate_minimax_score(guess, remaining_candidate_words)
            # Strong tiebreaker: prefer words in candidate list (helps solve faster)
            if guess in remaining_candidate_words:
                score -= 0.01  # Significant bonus
            
            if score < best_score or (score == best_score and guess in remaining_candidate_words):
                best_score = score
                best_guess = guess
        else:
            # Entropy: maximize information gain
            score = calculate_entropy(guess, remaining_candidate_words)
            # Strong tiebreaker: prefer words in candidate list
            if guess in remaining_candidate_words:
                score += 0.01  # Significant bonus
            
            if score > best_score or (score == best_score and guess in remaining_candidate_words):
                best_score = score
                best_guess = guess
    
    return best_guess if best_guess else remaining_candidate_words[0]
