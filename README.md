# Word Finder

A web application for searching and filtering words using regex and keyboard constraints — inspired by games like [Wordle](https://www.nytimes.com/games/wordle/index.html) and [Decipher](https://decipher.wtf/).  

🔗 Live App: [words.crossland.co.za](https://words.crossland.co.za)  
🌐 Backup Hosting: [wordfinder-nno8.onrender.com](https://wordfinder-nno8.onrender.com)  
🛠 Render Dashboard: [dashboard.render.com](https://dashboard.render.com/)  

> ⚠️ Note: The app is now self-hosted on a Raspberry Pi for faster response times and no cold starts. The Render-hosted version remains available as a backup, but may take up to 60 seconds to spin up initially.  

## Project Structure  

### Python Backend  
- Flask API  
- Uses the [Wordle word list](https://github.com/seanpatlan/wordle-words.git), which contains the official daily words.  
- Incorporates NLTK word list, sorted by how commonly it is found in the English language.  

### Static Frontend  
- HTML, CSS, and JavaScript  


<!-- ## Getting Started

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
See `backend/requirements.txt` for Python dependencies. -->
