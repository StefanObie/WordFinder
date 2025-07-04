# Word Finder

A web application for searching and filtering words using regex and keyboard constraints, inspired by games like [Wordle](https://www.nytimes.com/games/wordle/index.html) and [Decipher](https://decipher.wtf/).

The application is [hosted](https://wordfinder-nno8.onrender.com) on Render. Initially, it will take long (up to 60s) to load, due to Render's free plan. All subsequent interactions will be significantly faster.

## Project Structure

- `backend/` — Python backend (Flask API)
- `frontend/` — Frontend static files (HTML, CSS, JS)

## Getting Started

### Backend

1. Install dependencies:
   ```sh
   pip install -r backend/requirements.txt
   ```
2. Run the backend server:
   ```sh
   python backend/main.py
   ```

### Frontend

Open `frontend/index.html` in your browser. The frontend expects the backend to be running at `http://localhost:5000`.

## Requirements
See `backend/requirements.txt` for Python dependencies.
