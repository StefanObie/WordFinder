import re
import os
import nltk
import csv

# Use a local nltk_data directory inside your project
NLTK_DATA_DIR = os.path.join(os.path.dirname(__file__), 'nltk_data')
os.makedirs(NLTK_DATA_DIR, exist_ok=True)
nltk.data.path.insert(0, NLTK_DATA_DIR)

# Download 'words' at runtime if not present
try:
    from nltk.corpus import words, brown
    _ = words.words()
    _ = brown.words()
except LookupError:
    nltk.download('words', download_dir=NLTK_DATA_DIR)
    nltk.download('brown', download_dir=NLTK_DATA_DIR)
    from nltk.corpus import words, brown

# Build frequency distribution from Brown corpus
from collections import Counter
brown_freq = Counter(w.lower() for w in brown.words() if w.isalpha())

# Load priority words from CSV (Wordle word bank)
priority_words = []
csv_path = os.path.join(os.path.dirname(__file__), 'wordle-word-bank.csv')
try:
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        priority_words = [row[0].lower().strip() for row in reader if row and row[0].strip()]
except FileNotFoundError:
    print(f"Priority word file not found: {csv_path}")
    priority_words = []

# Load all English words (lowercase, deduplicated), sorted by frequency
try:
    all_words = set(w.lower() for w in words.words() if w.isalpha())
    
    # Remove priority words from all_words to avoid duplicates
    regular_words = all_words - set(priority_words)
    
    # Sort priority words by frequency (most common first), then alphabetically
    sorted_priority_words = sorted(
        priority_words,
        key=lambda w: (-brown_freq[w], w)
    )
    
    # Sort regular words by frequency (most common first), then alphabetically
    regular_word_list = sorted(
        regular_words,
        key=lambda w: (-brown_freq[w], w)
    )
    
    # Combine: sorted priority words first, then regular words
    word_list = sorted_priority_words + regular_word_list
    
except LookupError:
    print("NLTK 'words' or 'brown' corpus not found. Please download them.")
    word_list = priority_words  # Fallback to just priority words if NLTK fails

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

LOAD_LIMIT = 150

def search_words(pattern=None, length=None, allowed=None, disallowed=None):
    """
    Search for words matching the given pattern, length, allowed, and disallowed letters.
    - pattern: regex string (None means match all)
    - length: int or None
    - allowed: iterable of letters that must be present (or None)
    - disallowed: iterable of letters that must NOT be present (or None)
    Returns a list of matching words.
    """
    # Ensure pattern is a string for re.compile
    regex = re.compile(f"^{pattern}$", re.IGNORECASE) if pattern else None

    # Normalize allowed/disallowed to sets of single characters
    def normalize_letters(val):
        if val is None or val == [""] or val == "":
            return set()
        if isinstance(val, str):
            return set(val)
        if isinstance(val, list):
            # If it's a list of one string, split that string
            if len(val) == 1 and isinstance(val[0], str):
                return set(val[0])
            # Otherwise, flatten list of single characters (e.g., ['a', 'b'] -> {'a', 'b'})
            return set("".join(val))
        return set(val)

    allowed = normalize_letters(allowed)
    disallowed = normalize_letters(disallowed)

    results = []
    for word in word_list:
        if length is not None and len(word) != length: # Use 'is not None' for 0 or None
            continue
        if regex and not regex.match(word):
            continue
        if allowed and not all(l in word for l in allowed):
            continue
        if disallowed and any(l in word for l in disallowed):
            continue
        results.append(word)
    return results

# --- Flask App Setup ---

# Get the absolute path to the directory containing main.py (which is 'backend')
backend_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(os.path.dirname(backend_dir), 'frontend')

app = Flask(
    __name__,
    template_folder=frontend_dir,
    static_folder=frontend_dir
)

CORS(app) # Enable CORS for your API endpoints

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search", methods=["POST"])
def api_search():
    data = request.get_json(force=True) # force=True handles cases where content-type might be missing
    pattern = data.get("pattern")
    length = data.get("length")
    # Ensure length is an integer if provided, otherwise leave as None
    if length is not None:
        try:
            length = int(length)
        except ValueError:
            length = None # Or handle error appropriately

    allowed = data.get("allowed")
    disallowed = data.get("disallowed")
    
    matches = search_words(pattern, length, allowed, disallowed)
    return jsonify({
        "total": len(matches),
        "matches": matches[:LOAD_LIMIT]
    })

@app.route("/stats", methods=["GET"])
def api_stats():
    return jsonify({"total": len(word_list)})

if __name__ == "__main__":
    # For local development, uncomment this line:
    app.run(host="0.0.0.0", port=5000, debug=True)