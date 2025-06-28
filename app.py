from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import datetime
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash

app = Flask(__name__)
app.secret_key = '9e440d6adb2f3edabd5086bf91549ccb'

DATA_FOLDER = 'data'
USERS_FILE = os.path.join(DATA_FOLDER, 'users.json')
NOTES_FILE = os.path.join(DATA_FOLDER, 'notes.json')

@app.template_filter('format_date')
def format_date(value):
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%B %#d, %Y")
    except Exception:
        return value

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)


def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_notes():
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE, 'r') as f:
        return json.load(f)

def save_notes(notes):
    with open(NOTES_FILE, 'w') as f:
        json.dump(notes, f, indent=4)

def get_user(username):
    users = load_users()
    return next((user for user in users if user['username'] == username), None)

def get_notes_by_user(username):
    notes = load_notes()
    return [note for note in notes if note['username'] == username]

def is_admin(username):
    user = get_user(username)
    return user and user.get('is_admin', False)

# Routes

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if not username or not password:
            return render_template('register.html', error="Username and password are required.")

        users = load_users()
        if any(u['username'] == username for u in users):
            return render_template('register.html', error="Username already exists.")

        new_user = {
            'username': username,
            'password': generate_password_hash(password),  # HASHING here!
            'is_admin': False
        }

        users.append(new_user)
        save_users(users)

        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    admin = is_admin(username)
    notes = load_notes()

    # Get filter and sort query parameters
    search = request.args.get('search', '').lower()
    author = request.args.get('author', '').lower() if admin else ''
    sort_order = request.args.get('sort', 'newest')

    # Filter notes by user (non-admin) or author (admin)
    if not admin:
        notes = [note for note in notes if note['username'] == username]
    elif author:
        notes = [note for note in notes if author in note['username'].lower()]

    # Filter notes by title keyword
    if search:
        notes = [note for note in notes if search in note['title'].lower()]

    # Sort notes by date
    notes.sort(key=lambda n: n['created_at'], reverse=(sort_order == 'newest'))

    # Format date for display
    for note in notes:
        dt = datetime.fromisoformat(note['created_at'])
        note['formatted_date'] = dt.strftime('%B %d, %Y')

    return render_template('dashboard.html', username=username, is_admin=admin, notes=notes)


@app.route('/create_note', methods=['GET', 'POST'])
def create_note():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        if not title or not content:
            return render_template('create_note.html', error="Title and content cannot be empty")
        notes = load_notes()
        new_note = {
            'id': str(uuid4()),
            'username': username,
            'title': title,
            'content': content,
            'created_at': datetime.now().isoformat()
        }
        notes.append(new_note)
        save_notes(notes)
        return redirect(url_for('dashboard'))

    return render_template('create_note.html')

@app.route('/edit_note/<note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    notes = load_notes()
    note = next((n for n in notes if n['id'] == note_id), None)
    if not note:
        return "Note not found", 404

    # Only admin or author can edit
    if not (is_admin(username) or note['username'] == username):
        return "Unauthorized", 403

    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        if not title or not content:
            return render_template('edit_note.html', note=note, error="Title and content cannot be empty")
        note['title'] = title
        note['content'] = content
        save_notes(notes)
        return redirect(url_for('dashboard'))

    return render_template('edit_note.html', note=note)

@app.route('/delete_note/<note_id>', methods=['POST'])
def delete_note(note_id):
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    notes = load_notes()
    note = next((n for n in notes if n['id'] == note_id), None)
    if not note:
        return "Note not found", 404

    # Only admin or author can delete
    if not (is_admin(username) or note['username'] == username):
        return "Unauthorized", 403

    notes = [n for n in notes if n['id'] != note_id]
    save_notes(notes)
    return redirect(url_for('dashboard'))

@app.route('/note/<note_id>')
def view_note(note_id):
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    notes = load_notes()
    note = next((n for n in notes if n['id'] == note_id), None)
    if not note:
        return "Note not found", 404

    # Only admin or author can view
    if not (is_admin(username) or note['username'] == username):
        return "Unauthorized", 403

    dt = datetime.fromisoformat(note['created_at'])
    note['formatted_date'] = dt.strftime('%B %d, %Y')

    return render_template('view_note.html', note=note)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    users = load_users()
    user = next((u for u in users if u['username'] == username), None)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not check_password_hash(user['password'], current_password):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('change_password'))

        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect(url_for('change_password'))

        if len(new_password) < 6:
            flash('New password must be at least 6 characters long.', 'error')
            return redirect(url_for('change_password'))

        user['password'] = generate_password_hash(new_password)
        save_users(users)

        flash('Your password has been updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('change_password.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

