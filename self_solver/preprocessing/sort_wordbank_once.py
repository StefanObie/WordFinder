"""
One-time script to sort the Wordle word bank by frequency then alphabetically.
Run this once to create a pre-sorted CSV file for faster loading.
"""

import os
import csv
from collections import Counter

def sort_wordbank():
    """Sort word bank by frequency (most common first), then alphabetically."""
    
    # Try to get frequency data from Brown corpus
    try:
        import nltk
        from nltk.corpus import brown
        
        try:
            print("Loading Brown corpus for frequency analysis...")
            brown_freq = Counter(w.lower() for w in brown.words() if w.isalpha())
            print(f"Loaded frequency data for {len(brown_freq)} words")
        except LookupError:
            print("Brown corpus not found. Attempting to download...")
            nltk.download('brown')
            from nltk.corpus import brown
            brown_freq = Counter(w.lower() for w in brown.words() if w.isalpha())
            print(f"Downloaded and loaded frequency data for {len(brown_freq)} words")
    except ImportError:
        print("NLTK not available. Using alphabetical sort only.")
        brown_freq = Counter()
    
    # Load original word bank
    csv_path = os.path.join(os.path.dirname(__file__), 'wordle-word-bank.csv')
    words = []
    
    try:
        print(f"\nReading words from {csv_path}...")
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            words = [row[0].lower().strip() for row in reader if row and row[0].strip()]
        print(f"Loaded {len(words)} words")
    except FileNotFoundError:
        print(f"Error: Word bank file not found at {csv_path}")
        return
    
    # Sort by frequency (descending), then alphabetically
    print("\nSorting words by frequency (most common first), then alphabetically...")
    sorted_words = sorted(words, key=lambda w: (-brown_freq.get(w, 0), w))
    
    # Save to new sorted file
    output_path = os.path.join(os.path.dirname(__file__), 'wordle-word-bank-sorted.csv')
    
    print(f"\nSaving sorted words to {output_path}...")
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for word in sorted_words:
            writer.writerow([word])
    
    print(f"✅ Successfully saved {len(sorted_words)} sorted words")
    
    # Show top 20 most common words
    print("\n" + "="*50)
    print("Top 20 words (most common first):")
    print("="*50)
    for i, word in enumerate(sorted_words[:20], 1):
        freq = brown_freq.get(word, 0)
        print(f"{i:2d}. {word.upper():8s} (frequency: {freq})")
    
    print("\n" + "="*50)
    print("Bottom 20 words (least common):")
    print("="*50)
    for i, word in enumerate(sorted_words[-20:], len(sorted_words)-19):
        freq = brown_freq.get(word, 0)
        print(f"{i:5d}. {word.upper():8s} (frequency: {freq})")
    
    print("\n✅ Done! Use 'wordle-word-bank-sorted.csv' for faster loading.")

if __name__ == "__main__":
    sort_wordbank()