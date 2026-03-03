"""
Optimal Wordle Solver - Main Entry Point
Uses hybrid entropy-minimax strategy to solve Wordle in 6 or fewer guesses.

Architecture:
- guess_strategy.py: Core algorithms (entropy, minimax, pattern calculation)
- wordle_simulator.py: Game mechanics and simulation
- wordle_player.py: Player logic and testing
- algo.py: Main CLI interface (this file)
"""

import sys
from guess_strategy import (
    get_optimal_guess,
    calculate_entropy,
    calculate_minimax_score,
    calculate_expected_remaining,
)
from wordle_player import (
    load_word_bank,
    WordlePlayer,
    suggest_guess,
    test_player,
)




def main():
    """CLI interface for the Wordle solver."""
    
    if len(sys.argv) > 1:
        # Command-line mode: provide remaining words as arguments
        # Usage: python algo.py word1 word2 word3
        remaining_words = [word.lower().strip() for word in sys.argv[1:]]
        remaining_words = [w for w in remaining_words if len(w) == 5]
        
        if not remaining_words:
            print("Error: No valid 5-letter words provided")
            print("Usage: python algo.py word1 word2 word3 ...")
            return
        
        print(f"\nRemaining candidates: {len(remaining_words)}")
        print(f"Words: {', '.join(remaining_words[:10])}" + 
              (f" ... (+{len(remaining_words)-10} more)" if len(remaining_words) > 10 else ""))
        
        # Get optimal guess
        try:
            result = suggest_guess(remaining_words)
            
            print(f"\n{'='*50}")
            print(f"OPTIMAL GUESS: {result['guess'].upper()}")
            print(f"{'='*50}")
            print(f"Entropy (information gain): {result['entropy']:.2f} bits")
            print(f"Worst case remaining: {result['worst_case']} words")
            print(f"Expected remaining: {result['expected_remaining']:.1f} words")
            print()
        except ValueError as e:
            print(f"Error: {e}")
    
    else:
        # Interactive test mode: run full test harness
        print("\nNo arguments provided. Running test harness...\n")
        test_player(num_tests=100, verbose=False)


if __name__ == "__main__":
    main()

