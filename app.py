from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# -------------------- ROUTES --------------------

# Landing Page
@app.route('/')
def home():
    return render_template('index.html')  # New landing page

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        
        if User.query.filter_by(username=username).first():
            return "Username already exists! Try another one."

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials! Try again."

    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# Task Management (Requires Login)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    tasks = Task.query.filter_by(user_id=user_id).all()
    return render_template('tasks.html', tasks=tasks)

# Add Task
@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    title = request.form['title']
    description = request.form['description']
    user_id = session['user_id']

    new_task = Task(title=title, description=description, user_id=user_id)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('dashboard'))

# Update Task
@app.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = Task.query.get_or_404(task_id)
    if task.user_id != session['user_id']:
        return "Unauthorized!"

    task.title = request.form['title']
    task.description = request.form['description']
    task.status = request.form['status']
    db.session.commit()
    return redirect(url_for('dashboard'))

# Delete Task
@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = Task.query.get_or_404(task_id)
    if task.user_id != session['user_id']:
        return "Unauthorized!"

    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('dashboard'))

# Run App
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure database tables exist
    app.run(debug=True)
