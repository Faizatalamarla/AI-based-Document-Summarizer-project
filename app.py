from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from io import BytesIO
import bcrypt
import docx
from pdfminer.high_level import extract_text as extract_pdf_text
from langdetect import detect
from googletrans import Translator

# Initialize NLTK
nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}
DATABASE = 'users.db'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

translator = Translator()

# --- Helper Functions ---

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text(filepath, ext):
    text = ""
    try:
        if ext == 'pdf':
            text = extract_pdf_text(filepath)
        elif ext == 'txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
        elif ext == 'docx':
            doc = docx.Document(filepath)
            text = '\n'.join(para.text for para in doc.paragraphs)
    except Exception as e:
        print(f"Error reading file: {e}")
    # Placeholder for image detection
    if '[IMAGE]' in text.upper():
        text += "\n[Image Detected: Diagram/Flowchart detected in the document.]"
    return text

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def detect_language(text):
    try:
        lang = detect(text)
        return lang
    except:
        return 'en'

def translate_text(text, dest='en'):
    try:
        translated = translator.translate(text, dest=dest)
        return translated.text
    except:
        return text

def summarize(text, num_sentences=5):
    text = clean_text(text)
    sentences = sent_tokenize(text)

    if len(sentences) <= num_sentences:
        return sentences

    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    words = [w for w in words if w.isalnum() and w not in stop_words]

    freq = FreqDist(words)
    ranking = {}

    for i, sent in enumerate(sentences):
        for word in word_tokenize(sent.lower()):
            if word in freq:
                ranking[i] = ranking.get(i, 0) + freq[word]

    top_sentences = sorted(ranking, key=ranking.get, reverse=True)[:num_sentences]
    summary = [sentences[i] for i in sorted(top_sentences)]

    return summary

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            summary TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        db.commit()

init_db()

# --- Routes ---

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['username'] = username
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        db = get_db()
        try:
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Username already exists.")
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files['file']
        summary_size = request.form['sentences']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            ext = filename.rsplit('.', 1)[1].lower()
            text = extract_text(filepath, ext)

            lang = detect_language(text)
            if lang != 'en':
                text = translate_text(text, dest='en')

            sentences_count = {'short': 4, 'medium': 7, 'long': 9}.get(summary_size, 5)
            summary = summarize(text, num_sentences=sentences_count)

            if lang != 'en':
                summary = [translate_text(line, dest=lang) for line in summary]

            db = get_db()
            db.execute('INSERT INTO summaries (user_id, filename, summary) VALUES (?, ?, ?)',
                       (session['user_id'], filename, '\n'.join(summary)))
            db.commit()

            os.remove(filepath)

            return render_template('result.html', summary=summary)
    return render_template('upload.html')

@app.route('/paste', methods=['GET', 'POST'])
def paste():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        text = request.form['text']
        summary_size = request.form['sentences']

        lang = detect_language(text)
        if lang != 'en':
            text = translate_text(text, dest='en')

        sentences_count = {'short': 4, 'medium': 7, 'long': 9}.get(summary_size, 5)
        summary = summarize(text, num_sentences=sentences_count)

        if lang != 'en':
            summary = [translate_text(line, dest=lang) for line in summary]

        db = get_db()
        db.execute('INSERT INTO summaries (user_id, filename, summary) VALUES (?, ?, ?)',
                   (session['user_id'], 'pasted_text', '\n'.join(summary)))
        db.commit()

        return render_template('result.html', summary=summary)
    return render_template('paste.html')

@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))
    db = get_db()
    rows = db.execute('SELECT * FROM summaries WHERE user_id = ? ORDER BY timestamp DESC',
                      (session['user_id'],)).fetchall()
    return render_template('history.html', summaries=rows)

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('profile.html', username=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/history/download/<int:id>')
def download_summary(id):
    if 'username' not in session:
        return redirect(url_for('login'))
    db = get_db()
    summary = db.execute('SELECT summary FROM summaries WHERE id = ? AND user_id = ?', (id, session['user_id'])).fetchone()
    if summary:
        content = summary['summary']
        return (
            content,
            200,
            {
                'Content-Type': 'text/plain',
                'Content-Disposition': f'attachment; filename=summary_{id}.txt'
            }
        )
    else:
        return "Summary not found.", 404

if __name__ == '__main__':
    app.run(debug=True)
