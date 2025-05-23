# AI-based-Document-Summarizer-project

A web application that uses **Natural Language Processing (NLP)** to summarize large documents intelligently. Upload files or paste text to get accurate, concise summaries—powered by Python, Flask, and NLTK.

---

## 🚀 Features

- 📄 Upload `.pdf`, `.docx`, or `.txt` files
- 🌐 Multilingual text support (auto-detect + translate)
- 🧠 AI-powered text summarization (extractive method)
- 🧾 Summary history (view, copy, or download)
- 🔐 Secure login and registration
- 🎨 Neon-glow themed responsive UI

---

## 🛠 Tech Stack

| Layer      | Technology             |
|------------|------------------------|
| Frontend   | HTML5, CSS3, Bootstrap |
| Backend    | Python (Flask)         |
| NLP        | NLTK, langdetect, Googletrans |
| Database   | SQLite                 |
| Auth       | bcrypt (hashed passwords) |

---
## 📂 Project Structure

```document-summarizer/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── README.md               # Project description
├── LICENSE                 # MIT license
├── .gitignore              # Files Git should ignore

├── uploads/                # Temporary upload folder
│   └── .gitkeep            # Keeps empty folder tracked by Git

├── static/                 # Static assets like CSS or JS
│   └── style.css           # Your neon-glow theme styles

├── templates/              # All HTML templates
│   ├── dashboard.html
│   ├── history.html
│   ├── login.html
│   ├── paste.html
│   ├── profile.html
│   ├── register.html
│   ├── result.html
│   └── upload.html
```

## 📦 Installation

```bash
git clone https://github.com/your-username/document-summarizer.git
cd document-summarizer
pip install -r requirements.txt
python app.py
