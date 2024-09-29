# Python script for Flask backend
#--------------------------------------------------------------------------------------------------------


# Import necessary libraries
from flask import Flask, render_template, request, jsonify, flash, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime as dt
import re
# import harshithfunction

# Instantiate and config app
app = Flask(__name__, static_folder="static")
app.config['SECRET_KEY'] = 'super secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db = SQLAlchemy(app) # To store personalized user data and user login info
# For uploading label images
upload_folder = 'static/uploads'
allowed_ext = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = upload_folder

# Database model for login
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))
        
        login_user(user)
        session['user_id'] = user.id  # Store user ID in session
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)  # Remove user ID from session
    flash('You have been logged out.')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists')
            return redirect(url_for('register'))
        new_user = User(email=email, username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        session['user_id'] = new_user.id  # Store user ID in session
        return redirect(url_for('question', sno=0)) # To ask basic questions to know user better
    return render_template('register.html')

# Default questions
questions = [
    {"sno": 0, "id": "food_intolerance", "text": "Do you have any food intolerances? If yes, please specify"},
    {"sno": 1, "id": "diet_preferred", "text": "What type of diet do you prefer?"},
    {"sno": 2, "id": "allergies", "text": "Do you have any allergies?"}
]
@app.route('/questions/<int:sno>', methods=['GET', 'POST'])
def question(sno):
    # Ensure sno is within the bounds of the questions list
    if sno >= len(questions):
        return "Question not found", 404
    question_id = questions[sno]["id"]
    if request.method == 'POST':
        # Get the answer and store it in the session
        answer = request.form.get('answer')
        session[f'answer_{question_id}'] = answer
        # If there are more default questions
        if sno < len(questions) - 1:
            return redirect(url_for('question', sno=sno + 1))
        # # If all default questions are done, call harshithfunction if needed
        # additional_question = harshithfunction(answer)
        # if additional_question:
        #     return render_template('question.html', question={"id": "additional", "text": additional_question})
        # If no more questions, save answers to DB and redirect home
        save_answers_to_db(session['user_id'])
        return redirect(url_for('home'))
    # Show the current question
    question = questions[sno]['text']
    return render_template('question.html', question=question)
class UserPreferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_intolerance = db.Column(db.String(255))
    diet_preferred = db.Column(db.String(255))
    allergies = db.Column(db.String(255))

    def __init__(self, user_id):
        self.user_id = user_id
def save_answers_to_db(user_id):
    user_preferences = UserPreferences(user_id=user_id)
    user_preferences.food_intolerance = session.get('food_intolerance')
    user_preferences.diet_preferred = session.get('diet_preferred')
    user_preferences.allergies = session.get('allergies')
    db.session.add(user_preferences)
    db.session.commit()



# Main pages
@app.route('/')
def home():
    return render_template('home.html', active_page='home')
@app.route('/chatbot')
def chatbot():
    img_results = session.get('img_results')
    first_message = None
    if img_results:
        first_message = img_results
    return render_template('chatbot.html', first_message=first_message, active_page='chatbot')
@app.route('/about_product')
def about_product():
    return render_template('about_product.html', active_page='about_product')
@app.route('/about_us')
def about_us():
    return render_template('about_us.html', active_page='about_us')
@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            dt_now = dt.now().strftime("%Y%m%d%H%M%S%f")
            filename = dt_now + ".jpg"
            file.save(os.path.join(upload_folder, filename))
            img_dir = upload_folder
            path = img_dir + filename
            if path:
                session['img_path'] = path # Store the image path in the session
                return parse()
        flash('File type not allowed')
        return redirect(request.url)
    return render_template('analyze.html')

def parse():
    img_path = session.get('img_path')
    if img_path:
                # img_results = harshithfunction(session) -  analyze image
                # img_results has output image path and text
                img_results = {"chartImageUrl": url_for('static', filename='images/user_male.jpg', _external=True), 
                               "overviewText": "This is the processed text from the image"}
                session['img_results'] = img_results
                return jsonify(img_results)
@app.route('/contact')
def contact():
    return render_template('contact.html', active_page='contact')

# Other pages
@app.route('/terms')
def terms():
    return render_template('terms.html', active_page='terms')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', active_page='privacy')

# Chatbot query function
@app.route('/get', methods=['POST'])
def query():
    input = request.form["msg"]
    # response = harshithfunction(input)
    # response = f'This is the response'
    response = f"Hey there! You have entered the text: {input}"
    return jsonify({"response": response})

# Contact form
@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    if not name or not email or not message:
        flash('Please fill all the fields')
        return redirect(url_for('contact'))
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash('Invalid email address', 'danger')
        return redirect(url_for('contact'))
    flash('Your message has been sent', 'success')
    return redirect(url_for('contact'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext
def process_image(img_path):
    # output = harshithfunction(img_path)
    output = f"Hey there! Upon reading the label you have uploaded, here's what we found. This is the processed text from the image at {img_path}"
    return output

# Create upload folder initially
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

# Create database initially
@app.before_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
