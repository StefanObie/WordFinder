import json
import os
import sys
from typing import Dict, List, Optional

from .pattern_utils import pattern_to_base3

TREE_FILE = os.path.join(os.path.dirname(__file__), "..", "preprocessing", "salet.tree.hard.json")


def _load_tree_or_exit() -> Dict:
    if not os.path.exists(TREE_FILE):
        print(
            "Error: decision tree file not found: salet.tree.hard.json",
            file=sys.stderr,
        )
        raise SystemExit(1)

    try:
        with open(TREE_FILE, "r", encoding="utf-8") as file_handle:
            tree = json.load(file_handle)
    except Exception as exc:
        print(f"Error: failed to load decision tree json: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if not isinstance(tree, dict) or "guess" not in tree or "map" not in tree:
        print("Error: invalid tree format in salet.tree.hard.json", file=sys.stderr)
        raise SystemExit(1)

    return tree


DECISION_TREE = _load_tree_or_exit()


def _pattern_key(pattern: int) -> str:
    return pattern_to_base3(pattern)


def _pattern_keys(pattern: int) -> List[str]:
    forward = _pattern_key(pattern)
    reverse = forward[::-1]
    if forward == reverse:
        return [forward]
    return [forward, reverse]


def _step(node: Dict, guess: str, pattern_base3: str) -> Dict:
    expected_guess = node.get("guess")
    if expected_guess and expected_guess != guess:
        raise KeyError(
            f"Tree history mismatch: expected guess '{expected_guess}', got '{guess}'"
        )

    map_data = node.get("map", {})
    if not map_data:
        return node

    keys = [pattern_base3, pattern_base3[::-1]]
    if keys[0] == keys[1]:
        keys = [keys[0]]
    child = None
    for key in keys:
        if key in map_data:
            child = map_data[key]
            break

    if child is None:
        return node

    if isinstance(child, str):
        return {"guess": child, "map": {"22222": child}}

    if not isinstance(child, dict) or "guess" not in child:
        raise KeyError("Invalid branch node in decision tree")

    return child


def get_optimal_guess(history: Optional[List[Dict]] = None) -> str:
    node = DECISION_TREE
    if history:
        for entry in history:
            pattern_value = entry.get("pattern")
            pattern_base3 = entry.get("pattern_base3")

            if pattern_base3 is None:
                if pattern_value is None:
                    raise KeyError("History entry missing both 'pattern_base3' and 'pattern'")
                pattern_base3 = _pattern_key(pattern_value)

            node = _step(node, entry["guess"], pattern_base3)

    guess = node.get("guess")
    if not guess:
        raise KeyError("Current decision tree state does not contain a guess")
    return guess
