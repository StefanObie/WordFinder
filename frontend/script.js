BACKEND_URL = 'https://wordfinder-nno8.onrender.com';

// Fetch total word count from backend
async function getStats() {
    try {
        const resp = await fetch(`${BACKEND_URL}/stats`);
        const data = await resp.json();
        return data.total;
    } catch {
        return 0;
    }
}

// Search words via backend API
async function postSearch(pattern, length, allowed, disallowed) {
    try {
        const resp = await fetch(`${BACKEND_URL}/search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                pattern,
                length,
                allowed,
                disallowed
            })
        });
        return await resp.json();
    } catch {
        return [];
    }
}

async function loadWordList() {
    // No-op, just fetch stats
    return await getStats();
}

async function searchWords() {
    const pattern = getPatternFromBoxes();
    const lengthFilter = document.getElementById('lengthFilter').value;
    const errorDiv = document.querySelector('.error');
    if (errorDiv) errorDiv.remove();

    let len = parseInt(lengthFilter);
    if (isNaN(len) || len <= 0) len = null;

    const allowed = Object.entries(keyStates).filter(([l, s]) => s === 'allowed').map(([l]) => l.toLowerCase());
    const disallowed = Object.entries(keyStates).filter(([l, s]) => s === 'disallowed').map(([l]) => l.toLowerCase());

    const data = await postSearch(pattern, len, allowed, disallowed);

    document.getElementById('matchCount').textContent = `Matches: ${data?.total.toLocaleString()}`;
    displayWords(data?.matches, data?.total);
}

// Initialize the application
async function init() {
    document.getElementById('wordList').innerHTML = '<div class="loading">Loading word list from backend...</div>';
    try {
        const total = await loadWordList();
        // Use .stat-item for both wordCount and matchCount
        document.getElementById('wordCount').textContent = `Total words: ${total.toLocaleString()}`;
        document.getElementById('matchCount').textContent = 'Matches: 0';
        renderKeyboard();
        renderLetterBoxes();
        await searchWords(); // Await here to ensure results are shown after loading
    } catch (error) {
        console.error('Failed to initialize word list:', error);
        document.getElementById('wordList').innerHTML = '<div style="text-align: center; padding: 40px; color: #dc3545;">Failed to load word list. Is the backend running?</div>';
    }
}

function clearSearch() {
    // Clear letter boxes
    const boxes = document.querySelectorAll('#letterBoxes input');
    boxes.forEach(box => box.value = '');
    // Reset keyboard state
    Object.keys(keyStates).forEach(l => keyStates[l] = 'neutral');
    renderKeyboard();
    // Reset matches and stats
    currentMatches = [];
    renderLetterBoxes();
    init();
}

function displayWords(words, totalMatches) {
    const wordList = document.getElementById('wordList');
    
    if (words.length === 0) {
        wordList.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">No words match your criteria.</div>';
        return;
    }

    const wordGrid = document.createElement('div');
    wordGrid.className = 'word-grid';
    
    words.forEach(word => {
        const wordItem = document.createElement('div');
        wordItem.className = 'word-item';
        wordItem.textContent = word;
        
        // Highlight 5-letter words for Wordle
        if (word.length === 5) {
            wordItem.classList.add('highlight');
        }
        
        wordGrid.appendChild(wordItem);
    });
    
    wordList.innerHTML = '';
    wordList.appendChild(wordGrid);

    // Show note if total matches exceed load limit
    if (typeof totalMatches === "number" && totalMatches > words.length) {
        const note = document.createElement('div');
        note.style.textAlign = "center";
        note.style.color = "#888";
        note.style.marginTop = "10px";
        note.textContent = `Showing first ${words.length} of ${totalMatches.toLocaleString()} matches.`;
        wordList.appendChild(note);
    }
}

// --- Add these stubs before init() is called ---

// Simple QWERTY keyboard layout for demo
const KEYBOARD_ROWS = [
    "QWERTYUIOP".split(""),
    "ASDFGHJKL".split(""),
    "ZXCVBNM".split("")
];

// Track key states: allowed/disallowed/neutral/inline
const keyStates = {};
"ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("").forEach(l => keyStates[l.toLowerCase()] = "neutral");

// Render the on-screen keyboard (stub)
function renderKeyboard() {
    const keyboardDiv = document.getElementById('keyboard');
    if (!keyboardDiv) return;
    keyboardDiv.innerHTML = '';
    KEYBOARD_ROWS.forEach(row => {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'keyboard-row';
        row.forEach(letter => {
            const l = letter.toLowerCase();
            // If the letter is present in any letter box, force 'inline' state
            let state = keyStates[l];
            const boxes = document.querySelectorAll('#letterBoxes input');
            const allBoxVals = Array.from(boxes).map(b => b.value.trim().toLowerCase());
            if (allBoxVals.includes(l)) {
                state = 'inline';
            }
            const key = document.createElement('div');
            key.className = `keyboard-key ${state}`;
            key.textContent = letter;
            key.onclick = () => {
                // Only allow cycling if not 'inline'
                const boxes = document.querySelectorAll('#letterBoxes input');
                const allBoxVals = Array.from(boxes).map(b => b.value.trim().toLowerCase());
                if (allBoxVals.includes(l)) return; // Don't cycle if inline
                const states = ['neutral', 'allowed', 'disallowed'];
                let idx = states.indexOf(keyStates[l]);
                idx = (idx + 1) % states.length;
                keyStates[l] = states[idx];
                renderKeyboard();
                searchWords();
            };
            rowDiv.appendChild(key);
        });
        keyboardDiv.appendChild(rowDiv);
    });
}

// Render letter boxes for pattern input (stub)
function renderLetterBoxes() {
    const letterBoxesDiv = document.getElementById('letterBoxes');
    if (!letterBoxesDiv) return;
    let length = parseInt(document.getElementById('lengthFilter').value) || 5;
    if (length > 15) length = 15; // Enforce max 15
    letterBoxesDiv.innerHTML = '';
    for (let i = 0; i < length; i++) {
        const input = document.createElement('input');
        input.type = 'text';
        input.maxLength = 1;
        input.className = 'letter-box';
        input.oninput = function() {
            // Always capitalize the entered letter
            if (input.value) {
                input.value = input.value.toUpperCase();
            }
            // Add or remove 'filled' class based on value
            const val = input.value.trim().toLowerCase();
            if (val) {
                input.classList.add('filled');
                if (keyStates.hasOwnProperty(val)) {
                    keyStates[val] = 'inline';
                    renderKeyboard();
                }
                // Move to next input if exists and current input is filled
                const boxes = document.querySelectorAll('#letterBoxes input');
                const idx = Array.from(boxes).indexOf(input);
                if (idx < boxes.length - 1) {
                    boxes[idx + 1].focus();
                }
            } else {
                input.classList.remove('filled');
                // If the letter was removed, check if it still exists in any other box
                // If not, reset its state to neutral
                const boxes = document.querySelectorAll('#letterBoxes input');
                const allBoxVals = Array.from(boxes).map(b => b.value.trim().toLowerCase());
                Object.keys(keyStates).forEach(l => {
                    if (!allBoxVals.includes(l) && keyStates[l] === 'inline') {
                        keyStates[l] = 'neutral';
                    }
                });
                renderKeyboard();
            }
            searchWords();
        };
        input.onkeydown = function(e) {
            if (e.key === "Backspace" && !input.value) {
                const boxes = document.querySelectorAll('#letterBoxes input');
                const idx = Array.from(boxes).indexOf(input);
                if (idx > 0) {
                    boxes[idx - 1].focus();
                    // Optionally, clear previous box if you want:
                    // boxes[idx - 1].value = '';
                }
            }
        };
        // If already filled (e.g., after rerender), keep class
        if (input.value && input.value.trim()) {
            input.classList.add('filled');
        }
        letterBoxesDiv.appendChild(input);
    }
}

// Get regex pattern from letter boxes (stub)
function getPatternFromBoxes() {
    const boxes = document.querySelectorAll('#letterBoxes input');
    let pattern = '';
    let count = 0;
    boxes.forEach(box => {
        if (count >= 15) return; // Do not allow more than 15 chars
        const val = box.value.trim();
        pattern += val ? val : '.';
        count++;
    });
    return pattern || null;
}

// Event listeners
document.getElementById('lengthFilter').addEventListener('input', function() {
    // Prevent more than 15
    let val = parseInt(this.value);
    if (val > 15) this.value = 15;
    renderLetterBoxes();
    searchWords();
});

// Attach clear button event
document.getElementById('clearBtn').addEventListener('click', clearSearch);

// Initialize the app
init();