import re
from nltk.corpus import words

# Load all English words (lowercase, deduplicated)
LOAD_LIMIT = 150
word_list = sorted(set(w.lower() for w in words.words() if w.isalpha()))

def search_words(pattern=None, length=None, allowed=None, disallowed=None):
    """
    Search for words matching the given pattern, length, allowed, and disallowed letters.
    - pattern: regex string (None means match all)
    - length: int or None
    - allowed: iterable of letters that must be present (or None)
    - disallowed: iterable of letters that must NOT be present (or None)
    Returns a list of matching words.
    """
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
            # Otherwise, flatten list of single characters
            return set("".join(val))
        return set(val)

    allowed = normalize_letters(allowed)
    disallowed = normalize_letters(disallowed)

    results = []
    for word in word_list:
        if length and len(word) != length:
            continue
        if regex and not regex.match(word):
            continue
        if allowed and not all(l in word for l in allowed):
            continue
        if disallowed and any(l in word for l in disallowed):
            continue
        results.append(word)
    return results

if __name__ == "__main__":
    # Run as Flask API server
    from flask import Flask, request, jsonify
    from flask_cors import CORS

    app = Flask(__name__)
    CORS(app)

    @app.route("/search", methods=["POST"])
    def api_search():
        data = request.get_json(force=True)
        pattern = data.get("pattern")
        length = data.get("length")
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

    app.run(host="0.0.0.0", port=5000)