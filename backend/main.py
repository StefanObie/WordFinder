import re
import os
import nltk
from nltk.corpus import words
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS # Ensure flask_cors is in your requirements.txt

# Load all English words (lowercase, deduplicated)
# NLTK's 'words' corpus needs to be downloaded the first time.
nltk.data.path.append('/opt/render/nltk_data')
try:
    word_list = sorted(set(w.lower() for w in words.words() if w.isalpha()))
except LookupError:
    print("NLTK 'words' corpus not found. Please download it: `import nltk; nltk.download('words')`")
    word_list = [] # Fallback to empty list if not found.

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