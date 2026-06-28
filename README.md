# 🎓 GET-EED — Career Development & Job Preparation Platform

A full-stack career development web application built with Flask, MySQL, spaCy, and Socket.IO. GET-EED helps students and job seekers prepare for careers through ATS resume analysis, an AI-powered chatbot, real-time group chat rooms, and interview preparation resources — all behind a secure user authentication system.

---

## ✨ Features

### 🔐 User Authentication
- Secure registration with full profile creation (name, username, email, DOB, gender, skills, education, certificates)
- Password hashing using `werkzeug` (`pbkdf2:sha256`)
- Session-based login/logout with `@login_required` route protection

### 📄 ATS Resume Analyzer
- Upload a PDF resume and paste a job description
- spaCy NLP extracts top technical keywords from the job description
- PyPDF2 scans the resume for keyword matches
- Calculates a **match percentage score**
- Identifies **strong points** (frequently matched terms) and **weak points** (missing keywords)
- Generates a **pie chart visualisation** of matched vs missing terms using matplotlib

### 🤖 Rule-Based Chatbot (NEBot)
- Detects greetings, farewells, negative/personal queries, and search intents
- Redirects search queries directly to Google
- Pattern matching with randomised responses for natural conversation

### 💬 Real-Time Chat Rooms
- Create or join rooms using a unique 4-character code
- Real-time messaging powered by **Flask-SocketIO**
- Tracks room members and message history
- Live join/leave notifications

### 👤 User Profile
- View and manage personal profile including skills, education, certificates, and about section

### 📋 Additional Pages
- Job listings (`/alljobs.html`)
- Interview preparation resources (`/interview1.html`)
- Wishlist, About, Contact Us, and Team pages

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | MySQL (via SQLAlchemy + PyMySQL) |
| NLP Engine | spaCy (`en_core_web_sm`) |
| PDF Parsing | PyPDF2 |
| Visualisation | matplotlib |
| Real-Time | Flask-SocketIO |
| Auth | werkzeug (password hashing), Flask sessions |
| Frontend | HTML, CSS, Jinja2 Templates |

---

## 📁 Project Structure

```
GET-EED/
├── app.py              # Main Flask application (523 lines)
├── get-pip.py          # pip bootstrap script
├── static/             # CSS, JS, images
└── templates/          # Jinja2 HTML templates
    ├── index.html          # Landing page
    ├── login.html          # Login page
    ├── register.html       # Registration page
    ├── home.html           # Dashboard
    ├── profile.html        # User profile
    ├── ats.html            # ATS resume analyser
    ├── nebot.html          # Chatbot interface
    ├── home_chatroom.html  # Chat room lobby
    ├── room.html           # Chat room
    ├── resume.html         # Resume upload
    ├── interview1.html     # Interview prep
    ├── alljobs.html        # Job listings
    ├── wishlist.html       # Wishlist
    ├── about.html          # About page
    ├── contact_us.html     # Contact page
    └── team.html           # Team page
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/malikKanishka/GET-EED.git
cd GET-EED
```

### 2. Install Dependencies

```bash
pip install flask flask-sqlalchemy flask-socketio werkzeug spacy PyPDF2 matplotlib pymysql
python -m spacy download en_core_web_sm
```

### 3. Set Up MySQL Database

Create a MySQL database named `GET_EED`:

```sql
CREATE DATABASE GET_EED;
```

Update the database URI in `app.py` if needed:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:<your_password>@localhost/GET_EED'
```

### 4. Run the App

```bash
python app.py
```

Open your browser at:
```
http://localhost:5000
```

Database tables are created automatically on first run via `db.create_all()`.

---

## 🔄 How It Works

### ATS Analysis Flow
```
Upload PDF + Paste Job Description
→ spaCy extracts top 10 technical keywords
→ PyPDF2 scans PDF for keyword matches
→ Match % calculated
→ Pie chart generated
→ Strong & weak points displayed
```

### Chatbot Flow
```
User types message
→ Remove punctuation → Split into words
→ Pattern detection (greeting / goodbye / negative / search)
→ Matched response returned or Google redirect triggered
```

### Chat Room Flow
```
Create room (unique 4-char code) or Join with code
→ Socket.IO connects user to room
→ Real-time messages broadcast to all members
→ Join/leave events tracked live
```

---

## 🗄️ Database Model

**User Table** (`GET_EED.user`)

| Field | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| name | String(100) | Full name |
| username | String(150) | Unique |
| email | String(150) | Unique |
| dob | String(10) | Date of birth |
| password | String(150) | Hashed (pbkdf2:sha256) |
| skills | Text | Comma-separated skills |
| education | Text | Education background |
| gender | Enum | Male / Female / Other |
| certificates | Text | Certifications |
| about | Text | Bio / about section |

---

## 📄 License

This project is open source and available for educational and personal use.
