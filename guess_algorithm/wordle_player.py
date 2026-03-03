"""
Wordle Player Module
Handles player logic, word bank management, and testing/evaluation of the solver.
"""

import os
import csv
import random
from collections import defaultdict
from typing import List, Dict

from guess_strategy import get_optimal_guess
from wordle_simulator import simulate_game, pattern_to_string


def load_word_bank(sorted: bool = True) -> List[str]:
    """
    Load word bank from CSV file.
    
    Args:
        sorted: If True, loads pre-sorted word bank by frequency
        
    Returns:
        List of 5-letter words (lowercased)
    """
    if sorted:
        csv_path = os.path.join(os.path.dirname(__file__), 'wordle-word-bank-sorted.csv')
    else:
        csv_path = os.path.join(os.path.dirname(__file__), 'wordle-word-bank.csv')
    
    # Fallback to parent backend folder if not found in current directory
    if not os.path.exists(csv_path):
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                'backend', 'wordle-word-bank.csv')
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        words = [row[0].lower().strip() for row in reader if row and row[0].strip()]
    
    # Filter to 5-letter words only
    words = [w for w in words if len(w) == 5]
    
    return words


class WordlePlayer:
    """
    Represents a player that solves Wordle using an optimal strategy.
    """
    
    def __init__(self, word_bank: List[str], strategy_function=None):
        """
        Initialize the player.
        
        Args:
            word_bank: List of valid words
            strategy_function: Function to use for selecting guesses 
                             (defaults to get_optimal_guess)
        """
        self.word_bank = word_bank
        self.strategy = strategy_function or get_optimal_guess
    
    def play(self, answer: str, max_attempts: int = 6, verbose: bool = False) -> Dict:
        """
        Play a single Wordle game.
        
        Args:
            answer: The target word
            max_attempts: Maximum guesses allowed
            verbose: If True, print progress
            
        Returns:
            Game result dictionary
        """
        return simulate_game(
            answer=answer,
            all_words=self.word_bank,
            strategy_function=self.strategy,
            max_attempts=max_attempts,
            verbose=verbose
        )
    
    def play_batch(
        self,
        answers: List[str],
        max_attempts: int = 6,
        verbose: bool = False
    ) -> Dict[str, any]:
        """
        Play multiple games and collect statistics.
        
        Args:
            answers: List of target words to play
            max_attempts: Maximum guesses per game
            verbose: If True, print each game
            
        Returns:
            Statistics dictionary with solved count, attempts distribution, etc.
        """
        stats = {
            'total': len(answers),
            'solved': 0,
            'failed': 0,
            'attempts_distribution': defaultdict(int),
            'total_attempts': 0,
            'max_attempts': 0,
            'games': []
        }
        
        for i, answer in enumerate(answers, 1):
            result = self.play(answer, max_attempts=max_attempts, verbose=verbose)
            stats['games'].append(result)
            
            if result['solved']:
                stats['solved'] += 1
                stats['attempts_distribution'][result['attempts']] += 1
                stats['total_attempts'] += result['attempts']
                stats['max_attempts'] = max(stats['max_attempts'], result['attempts'])
            else:
                stats['failed'] += 1
        
        return stats
    
    @staticmethod
    def print_stats(stats: Dict) -> None:
        """
        Print formatted statistics from a batch of games.
        
        Args:
            stats: Statistics dictionary from play_batch()
        """
        print(f"\n{'='*60}")
        print("SOLVER PERFORMANCE SUMMARY")
        print(f"{'='*60}")
        print(f"Total games: {stats['total']}")
        print(f"Solved: {stats['solved']} ({stats['solved']/stats['total']*100:.1f}%)")
        print(f"Failed: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
        
        if stats['solved'] > 0:
            avg_attempts = stats['total_attempts'] / stats['solved']
            print(f"\nAverage attempts: {avg_attempts:.2f}")
            print(f"Maximum attempts: {stats['max_attempts']}")
            
            print(f"\nAttempts distribution:")
            for attempts in sorted(stats['attempts_distribution'].keys()):
                count = stats['attempts_distribution'][attempts]
                percentage = (count / stats['solved'] * 100) if stats['solved'] > 0 else 0
                bar = '█' * int(percentage / 2)
                print(f"  {attempts} guesses: {count:3d} ({percentage:5.1f}%) {bar}")
        
        print(f"{'='*60}\n")


def suggest_guess(remaining_candidate_words: List[str]) -> Dict:
    """
    Suggest the optimal guess for a given set of remaining candidates.
    
    Args:
        remaining_candidate_words: List of possible answers
        
    Returns:
        Dictionary with guess and scoring information
    """
    from guess_strategy import (
        calculate_entropy,
        calculate_minimax_score,
        calculate_expected_remaining
    )
    
    if not remaining_candidate_words:
        raise ValueError("No remaining candidates")
    
    optimal = get_optimal_guess(remaining_candidate_words)
    
    # Calculate scores
    entropy = calculate_entropy(optimal, remaining_candidate_words)
    minimax = calculate_minimax_score(optimal, remaining_candidate_words)
    expected = calculate_expected_remaining(optimal, remaining_candidate_words)
    
    return {
        'guess': optimal,
        'entropy': entropy,
        'worst_case': minimax,
        'expected_remaining': expected
    }


def test_player(num_tests: int = 100, verbose: bool = False) -> Dict:
    """
    Test the player on random words from word bank.
    
    Args:
        num_tests: Number of random words to test
        verbose: If True, print each game
        
    Returns:
        Statistics dictionary
    """
    print(f"\n{'='*60}")
    print(f"Testing Wordle Player on {num_tests} random words")
    print(f"{'='*60}")
    
    word_bank = load_word_bank()
    test_words = random.sample(word_bank, min(num_tests, len(word_bank)))
    
    player = WordlePlayer(word_bank)
    
    print(f"\nStarting {len(test_words)} games...")
    stats = player.play_batch(test_words, max_attempts=12, verbose=verbose)
    
    # Print progress
    if not verbose:
        for i, word in enumerate(test_words, 1):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(test_words)}")
    
    WordlePlayer.print_stats(stats)
    return stats

if __name__ == "__main__":
    test_player(num_tests=100, verbose=False)