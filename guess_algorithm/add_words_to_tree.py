"""
Script to add missing words to the decision tree.

Usage:
    python add_words_to_tree.py WORD1 WORD2 WORD3
"""

import json
import os
import sys
from typing import Dict, List

from pattern_utils import calculate_pattern, pattern_to_base3

TREE_FILE = os.path.join(os.path.dirname(__file__), "salet.tree.hard.json")
BACKUP_FILE = os.path.join(os.path.dirname(__file__), "salet.tree.hard.json.backup")


def load_tree() -> Dict:
    with open(TREE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tree(tree: Dict, backup: bool = True) -> None:
    if backup and os.path.exists(TREE_FILE):
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            with open(TREE_FILE, "r", encoding="utf-8") as orig:
                f.write(orig.read())
        print(f"Created backup: {BACKUP_FILE}")
    
    with open(TREE_FILE, "w", encoding="utf-8") as f:
        json.dump(tree, f, indent=2)
    print(f"Saved updated tree: {TREE_FILE}")


def trace_path(tree: Dict, answer: str, verbose: bool = True) -> List[Dict]:
    """
    Trace the path through tree for a given answer word.
    Returns list of steps with guess, pattern, and whether branch exists.
    """
    path = []
    node = tree
    depth = 0
    
    while True:
        guess = node.get("guess")
        if not guess:
            break
        
        pattern_int = calculate_pattern(guess, answer)
        pattern_key = pattern_to_base3(pattern_int)
        
        if verbose:
            print(f"  Depth {depth}: guess={guess.upper()}, pattern={pattern_key} ({pattern_int})")
        
        # Check if this is the answer
        if pattern_int == 242:  # All greens
            path.append({
                "depth": depth,
                "guess": guess,
                "pattern_key": pattern_key,
                "pattern_int": pattern_int,
                "exists": True,
                "is_answer": True
            })
            if verbose:
                print(f"    ✓ Solved!")
            break
        
        map_data = node.get("map", {})
        
        # Check if branch exists
        child = map_data.get(pattern_key)
        exists = child is not None
        
        path.append({
            "depth": depth,
            "guess": guess,
            "pattern_key": pattern_key,
            "pattern_int": pattern_int,
            "exists": exists,
            "is_answer": False
        })
        
        if not exists:
            if verbose:
                print(f"    ✗ Missing branch for pattern {pattern_key}")
            break
        
        # Handle terminal string node
        if isinstance(child, str):
            if child == answer:
                if verbose:
                    print(f"    ✓ Found terminal answer: {child.upper()}")
                path[-1]["is_answer"] = True
            else:
                if verbose:
                    print(f"    ✗ Terminal mismatch: tree has '{child.upper()}' but need '{answer.upper()}'")
            break
        
        # Continue to next level
        node = child
        depth += 1
    
    return path


def add_word_to_tree(tree: Dict, answer: str, verbose: bool = True) -> bool:
    """
    Add a word to the tree by following its pattern path and adding missing branches.
    Returns True if any modification was made.
    """
    if verbose:
        print(f"\nTracing path for: {answer.upper()}")
    
    path = trace_path(tree, answer, verbose=verbose)
    
    # Check if word already fully exists in tree
    if path and path[-1].get("is_answer"):
        if verbose:
            print(f"  Word already in tree!")
        return False
    
    # Find where tree becomes incomplete or hits a terminal mismatch
    missing_start_idx = None
    terminal_mismatch_idx = None
    
    for i, step in enumerate(path):
        if not step["exists"]:
            missing_start_idx = i
            break
    
    # Navigate to the point where we need to add branches
    node = tree
    parent_node = None
    parent_pattern_key = None
    
    for i in range(missing_start_idx if missing_start_idx is not None else len(path)):
        step = path[i]
        parent_node = node
        parent_pattern_key = step["pattern_key"]
        child = node.get("map", {}).get(step["pattern_key"])
        
        if isinstance(child, str):
            # Hit a terminal string that doesn't match our answer
            if child != answer:
                terminal_mismatch_idx = i
                if verbose:
                    print(f"  Found terminal mismatch at depth {i}: tree has '{child.upper()}', need '{answer.upper()}'")
                
                # Calculate pattern from terminal word to our answer
                new_pattern_int = calculate_pattern(child, answer)
                new_pattern_key = pattern_to_base3(new_pattern_int)
                
                if verbose:
                    print(f"\n  Converting terminal to branch node:")
                    print(f"    Old terminal: {child.upper()}")
                    print(f"    New guess node: {child.upper()}")
                    print(f"    New branch pattern: {new_pattern_key}")
                    print(f"    New answer: {answer.upper()}")
                
                # Replace terminal string with branch node
                node["map"][step["pattern_key"]] = {
                    "guess": child,
                    "map": {
                        new_pattern_key: answer.lower()
                    }
                }
                return True
            return False
        
        node = child
    
    if missing_start_idx is None:
        if verbose:
            print(f"  Path complete but no modification needed")
        return False
    
    # Add missing branch
    missing_step = path[missing_start_idx]
    if verbose:
        print(f"\n  Adding branch at depth {missing_step['depth']}:")
        print(f"    Guess: {missing_step['guess'].upper()}")
        print(f"    Pattern: {missing_step['pattern_key']}")
        print(f"    Answer: {answer.upper()}")
    
    if "map" not in node:
        node["map"] = {}
    
    # Add answer as terminal string
    node["map"][missing_step["pattern_key"]] = answer.lower()
    
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python add_words_to_tree.py WORD1 WORD2 WORD3 ...")
        print("   or: python add_words_to_tree.py --file words.txt")
        sys.exit(1)
    
    # Parse arguments
    words = [w.lower().strip() for w in sys.argv[1:]]
    
    # Filter to 5-letter words
    words = [w for w in words if len(w) == 5]
    
    if not words:
        print("Error: No valid 5-letter words provided")
        sys.exit(1)
    
    print(f"Loading tree from: {TREE_FILE}")
    tree = load_tree()
    
    print(f"\nProcessing {len(words)} word(s)...")
    
    modified_count = 0
    for word in words:
        if add_word_to_tree(tree, word, verbose=True):
            modified_count += 1
    
    print(f"\n{'='*60}")
    print(f"Summary: {modified_count} word(s) added to tree")
    print(f"{'='*60}")
    
    if modified_count > 0:
        save_tree(tree, backup=True)
    else:
        print("No changes made to tree.")


if __name__ == "__main__":
    main() 