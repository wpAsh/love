from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///love.db'
app.config['UPLOAD_FOLDER'] = 'static/images/uploaded'
app.config['ADMIN_USERNAME'] = 'Honey'
app.config['ADMIN_PASSWORD_HASH'] = generate_password_hash('05112024')  # Change this!
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Database Models
class DiaryEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    photos = db.relationship('Photo', backref='entry', lazy=True)

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100))
    caption = db.Column(db.String(200))
    entry_id = db.Column(db.Integer, db.ForeignKey('diary_entry.id'))

# Create database tables
with app.app_context():
    db.create_all()

# Get time-based greeting
def get_greeting():
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        return "Good morning"
    elif 12 <= current_hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"

# Check first visit
def check_first_visit():
    if 'visited' not in session:
        session['visited'] = True
        return True
    return False

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            session['next_url'] = request.url
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    # Redirect to login if not logged in
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    time_greeting = get_greeting()
    love_message = "I love you"
    first_visit = check_first_visit()
    return render_template('index.html', 
                          time_greeting=time_greeting,
                          love_message=love_message,
                          first_visit=first_visit)

@app.route('/diary')
@login_required
def diary():
    entries = DiaryEntry.query.order_by(DiaryEntry.date.desc()).all()
    
    # Group photos by entry
    entries_with_photos = []
    for entry in entries:
        entry_photos = Photo.query.filter_by(entry_id=entry.id).all()
        entries_with_photos.append({
            'entry': entry,
            'photos': entry_photos
        })
    
    # Get images from uploaded folder - DEBUGGING VERSION
    image_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
        print(f"Created folder: {image_folder}")
    
    slider_images = []
    try:
        for f in os.listdir(image_folder):
            full_path = os.path.join(image_folder, f)
            if os.path.isfile(full_path) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                slider_images.append(f)
                print(f"Found image: {f} at {full_path}")
    except Exception as e:
        print(f"Error reading images: {e}")
    
    return render_template('diary.html',
                         entries_with_photos=entries_with_photos,
                         slider_images=slider_images)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to home
    if session.get('admin_logged_in'):
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = request.form.get('remember') == 'on'
        
        if username == app.config['ADMIN_USERNAME'] and \
           check_password_hash(app.config['ADMIN_PASSWORD_HASH'], password):
            # Login successful
            session['admin_logged_in'] = True
            session.permanent = remember  # Make session persistent if "Remember me" checked
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/add_entry', methods=['GET', 'POST'])
@login_required
def add_entry():
    if request.method == 'POST':
        # Add new diary entry
        title = request.form['title']
        content = request.form['content']
        new_entry = DiaryEntry(title=title, content=content)
        db.session.add(new_entry)
        db.session.commit()
        
        # Handle photo uploads
        photos = request.files.getlist('photos')
        for photo in photos:
            if photo.filename != '':
                filename = f"photo_{new_entry.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                new_photo = Photo(filename=filename, entry_id=new_entry.id)
                db.session.add(new_photo)
        
        db.session.commit()
        flash('New memory added to our diary!', 'success')
        return redirect(url_for('diary'))
    
    return render_template('add_entry.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))
@app.route('/our_special_code')
def special_redirect():
    return redirect(url_for('login'))
@app.context_processor
def device_check():
    user_agent = request.headers.get('User-Agent', '').lower()
    return {
        'is_mobile': any(m in user_agent for m in ['mobile', 'android', 'iphone']),
        'is_pc': not any(m in user_agent for m in ['mobile', 'android', 'iphone'])
    }

if __name__ == '__main__':
    app.run(debug=True)
