from flask import Flask, request, render_template, redirect, url_for, flash,session 
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import PyPDF2
import os
import spacy
from collections import Counter
import warnings
import matplotlib.pyplot as plt
import io
import base64
# import time
import random
import string
from string import ascii_uppercase
from flask_socketio import join_room, leave_room, send, SocketIO
import matplotlib
import pymysql
pymysql.install_as_MySQLdb()
from functools import wraps
from flask import session, redirect, url_for, flash

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



# Suppress all warnings
warnings.filterwarnings("ignore")

# Set matplotlib to use a non-GUI backend

matplotlib.use('Agg')  # Use the Agg backend for non-interactive use
plt.ioff()  # Disable interactive mode explicitly

app = Flask(__name__)

# Set up the database URI (replace with your actual database credentials)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:kanishka@localhost/GET_EED'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

#SocketIO
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app, manage_session=False)

rooms = {}

# Set file upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create uploads folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

# Load spaCy's English model for NLP processing
nlp = spacy.load("en_core_web_sm")

# Define the User model
# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    dob = db.Column(db.String(10), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    skills = db.Column(db.Text)
    education = db.Column(db.Text)
    gender = db.Column(db.Enum('Male', 'Female', 'Other'), nullable=False)
    certificates = db.Column(db.Text)
    about = db.Column(db.Text)
# Create the database tables if they don't exist
with app.app_context():
    db.create_all()

# Function to extract technical terms from job description
def extract_technical_terms(job_description, num_keywords=10):
    doc = nlp(job_description.lower())
    extracted_terms = [
        token.text for token in doc 
        if token.pos_ in {'NOUN', 'PROPN'} and len(token.text) > 2
    ]
    extracted_terms = [term for term in extracted_terms if not nlp.vocab[term].is_stop]
    keyword_counts = Counter(extracted_terms)
    most_common_keywords = [keyword for keyword, _ in keyword_counts.most_common(num_keywords)]
    
    return most_common_keywords

# Function to search terms in PDF
def search_words_in_pdf(pdf_path, search_terms):
    matched_terms = Counter()
    unmatched_terms = set(search_terms)

    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text:
                    words = text.split()  # Split the text into words

                    # Loop through the words and check for matches with search terms
                    for word in words:
                        word_lower = word.lower()
                        for term in search_terms:
                            if term.lower() in word_lower:
                                matched_terms[term] += 1
                                unmatched_terms.discard(term)
                                 
    except FileNotFoundError:
        flash("The specified PDF file was not found.")
        return Counter(), set()
    except Exception as e:
        flash(f"An error occurred while processing the PDF: {e}")
        return Counter(), set()

    return matched_terms, unmatched_terms

# Function to plot pie chart
def plot_pie_chart(matched_percentage):
    matched_count = matched_percentage
    unmatched_count = 100 - matched_percentage
    plt.figure(figsize=(6, 6))
    plt.pie([matched_count, unmatched_count], labels=['Matched Terms', 'Missing Terms'],
            colors=['#4CAF50', '#FF6B6B'], autopct='%1.1f%%', startangle=140)
    plt.title('Resume Match Analysis')

    # Save the plot as a PNG image in-memory
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode()

    plt.close()
    return chart_url

# Route for ATS Analysis page
@app.route('/ats.html', methods=['GET', 'POST'])
@login_required
def ats():
    if request.method == 'POST':
        job_description = request.form['job_description']
        if 'resume' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['resume']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # Extract technical terms and search for them in the resume PDF
            technical_terms = extract_technical_terms(job_description)
            matched_terms, unmatched_terms = search_words_in_pdf(file_path, technical_terms)

            matched_count = sum(matched_terms.values())
            total_terms = len(technical_terms)
            match_percentage = (matched_count / total_terms) * 100 if total_terms > 0 else 0

            # Plot pie chart with matched percentage
            chart_url = plot_pie_chart(match_percentage)

            # Identify strong points (frequently occurring terms) and weak points (missing terms)
            strong_points = {term: count for term, count in matched_terms.items() if count > 1}
            weak_points = list(unmatched_terms)

            # Flash the matched terms with their occurrences
            flash(f'Your resume matches {match_percentage:.2f}% of key skills.')

            # Display the matched terms and their occurrences
            matched_info = [f"{term}: {count} occurrence(s)" for term, count in matched_terms.items()]
            flash("Matched Terms and Occurrences: " + ", ".join(matched_info))

            return render_template('ats.html', 
                                   chart_url=chart_url, 
                                   matched_terms=matched_terms, 
                                   matched_count=matched_count, 
                                   match_percentage=match_percentage, 
                                   technical_terms=technical_terms, 
                                   strong_points=strong_points, 
                                   weak_points=weak_points)

    return render_template('ats.html')
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    errors = {}
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        dob = request.form['dob']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        skills = request.form['skills']
        education = request.form['education']
        gender = request.form['gender']
        certificates = request.form['certificates']
        about = request.form['about']

        # Validation
        if not name or len(name) < 3:
            errors['name'] = "Name is required and must be at least 3 characters."
        if not username or len(username) < 3:
            errors['username'] = "Username is required and must be at least 3 characters."
        if not email or "@" not in email:
            errors['email'] = "Valid email is required."
        if not dob:
            errors['dob'] = "Date of birth is required."
        if not password or len(password) < 6:
            errors['password'] = "Password must be at least 6 characters."
        if password != confirm_password:
            errors['confirm_password'] = "Passwords do not match."
        if not gender:
            errors['gender'] = "Gender is required."
        
        # If no errors, save to the database
        if not errors:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(name=name, username=username, email=email, dob=dob, password=hashed_password,
                            skills=skills, education=education, gender=gender, certificates=certificates, about=about)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))  # Redirect to login page after successful registration

    return render_template('register.html', errors=errors)
     
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to home.html
        else:
            flash('Invalid username or password!', 'danger')
    return render_template('login.html')

# Home/Dashboard route, accessible after login
@app.route('/home.html')
def dashboard():
    if 'user_id' in session:
        return render_template('home.html')
    flash('Please log in to access the dashboard.', 'warning')
    return redirect(url_for('login'))

# Profile route
@app.route('/profile.html')
def profile():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return render_template('profile.html', user=user)
    flash('Please log in to view your profile.', 'warning')
    return render_template('profile.html')

#Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Clear session data
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# Add Resume Route
@app.route('/resume.html', methods=['GET', 'POST'])
def resume():
    if request.method == 'POST':
        file = request.files['resume']
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            flash('Resume uploaded successfully!', 'success')
            return redirect(url_for('resume'))

    return render_template('resume.html')

# Irrelevant Responses by the Chatbot
neg_responses = ["I'm a bot!", "Not Possible, because I'm a bot.", "Sorry for that, if I were a human I could have done that!"]

# Unnecessary words for searching algorithm
finding = ["look", "search", "find", "get", "what", "how", "define", "example", "explain"]

# Welcome greetings
greetings = ["hi", "hello", "sup", "hey", "namaste", "greetings"]

# Thanks greetings that might be entered by users
thanks_patterns = ["Thanks", "Thank", "helpful", "Thank's"]

# Leaving greetings
leave = ["bye", "see", "goodbye"]

# How are you doing types
asking = ['are', 'you', 'doing', 'good', 'eating', 'sleeping', 'playing', 'watching', 'love', 'eat', 'sleep', 'crush', 'games']

# Function to remove punctuation from the user input
def remove_punctuation(user_input):
    translator = str.maketrans('', '', string.punctuation)
    return user_input.translate(translator)

# Function to detect if the input matches a greeting pattern
def greetings_pattern(temp):
    list_greetings = ["hello", "hi", "hey", "greetings", "salutations", "howdy", "hola", "bonjour", "ciao", "aloha"]
    return sum(1 for word in temp if word in list_greetings)

# Function to detect if the input matches a goodbye pattern
def goodbye_pattern(temp):
    list_goodbye = ["goodbye", "bye", "farewell", "adieu", "seeya", "later", "ciao", "adios", "au revoir", "take care"]
    return sum(1 for word in temp if word in list_goodbye)

# Function to detect if the input matches a negative pattern
def negative_pattern(temp):
    list_negative = ["i", "love", "age", "you", "your", "name", "gender", "height", "weight", "hate", "kiss", "hug", "slap"]
    return sum(1 for word in temp if word in list_negative)

# Function to detect if the input matches a search pattern
def search_pattern(temp):
    list_question = [
        "search", "find", "look", "explore", "browse", "seek", "investigate", "query", "research", "discover", "lookup",
        "scan", "examine", "track", "identify", "uncover", "check", "survey", "probe", "assess", "what"
    ]
    return sum(1 for word in temp if word in list_question)

# Function to select a random greeting response
def greetings_response():
    g_response = ["Hello!", "Hi there!", "Hey!", "Greetings!", "Salutations!", "Howdy!", "Hola!", "Bonjour!", "Ciao!", "Aloha!"]
    return random.choice(g_response)

# Function to select a random goodbye response
def goodbye_response():
    g_response = ["Goodbye!", "Bye!", "Farewell!", "Adieu!", "See you!", "Later!", "Ciao!", "Adios!", "Au revoir!", "Take care!"]
    return random.choice(g_response)

# Function to select a negative response (default for certain inputs)
def negative_response():
    g_response = ["Sorry, I'm a BOT!"]
    return random.choice(g_response)

# Function to split the user input into a list of words
def spliter(user_input):
    return user_input.lower().split()

@app.route("/nebot.html", methods=["GET", "POST"])
@login_required
def chatbot():
    if request.method == "POST":
        user_input = request.form["user_input"]
        cleaned_text = remove_punctuation(user_input)
        temp = spliter(cleaned_text)
        
        # Detect if the input matches any pattern
        count_greetings = greetings_pattern(temp)
        count_goodbye = goodbye_pattern(temp)
        count_negative = negative_pattern(temp)
        count_search = search_pattern(temp)

        max_count = max(count_goodbye, count_greetings, count_negative, count_search)
        
        if max_count >= 1:
            if count_greetings == max_count:
                bot_response = greetings_response()
                
            elif count_goodbye == max_count:
                bot_response = goodbye_response()
                
            elif count_negative == max_count:
                bot_response = negative_response()
            
            elif count_search == max_count:
                search_url = f"https://www.google.com/search?q={cleaned_text}"
                return redirect(search_url)
        else:
            bot_response = "I don't understand!"
        
        return render_template("nebot.html", bot_response=bot_response)
    
    return render_template("nebot.html", bot_response="")

#CHATROOM CODE
def generate_unique_code(length):
    while True:
        code = "".join(random.choice(ascii_uppercase) for _ in range(length))
        if code not in rooms:
            break
    return code

@app.route("/home_chatroom.html", methods=["POST", "GET"])
@login_required
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        create = request.form.get("create")
        join = request.form.get("join")

        if not name:
            return render_template("home_chatroom.html", error="Please enter a name.", code=code, name=name)

        if join and not code:
            return render_template("home_chatroom.html", error="Please enter a room code to join.", code=code, name=name)

        room = None
        if create:  # If the create button was pressed
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif join and code in rooms:  # If the join button was pressed and the room exists
            room = code
        else:
            return render_template("home_chatroom.html", error="Room does not exist.", code=code, name=name)

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home_chatroom.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    
    messages = rooms[room]["messages"]
    return render_template("room.html", code=room, messages=messages)

@socketio.on("message")
def handle_message(data):
    room = session.get("room")
    if room not in rooms:
        return
    
    message_data = {
        "name": session.get("name"),
        "message": data["data"]
    }
    
    rooms[room]["messages"].append(message_data)
    send(message_data, to=room)
    print(f"Message from {session.get('name')}: {data['data']}")

@socketio.on("connect")
def handle_connect():
    room = session.get("room")
    name = session.get("name")
    
    if not room or not name:
        return
    
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def handle_disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")

# Main Route
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/wishlist.html')
def wishlist():
    return render_template('wishlist.html')

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/interview1.html')
@login_required
def interview():
    return render_template('interview1.html')
@app.route('/alljobs.html')
def jobs():
    return render_template('alljobs.html')
@app.route('/contact_us.html')
def contact_us():
    return render_template('contact_us.html')
@app.route('/team.html')
def team():
    return render_template('team.html')
if __name__ == '__main__':
    with app.app_context():  # Ensure app context is active
        db.create_all()  # Create tables if they don't exist

    # Run the app with SocketIO support
    socketio.run(app, debug=True)

