from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
# mysql connector 
import mysql.connector
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
from functools import wraps
import bcrypt

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="capstone_v1"
    )

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active queues and matches
code_queue = []
quiz_queue = []
active_matches = {}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/') 
def home():
    # handle login and registration modal logic, role based admin and user
    
    return render_template('index.html')

@app.route('/check_login')
def check_login():
    return jsonify({'logged_in': 'user_id' in session})

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        query = "SELECT * FROM users WHERE username = %s"
        db_cursor.execute(query, (username,))
        user = db_cursor.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            if user['role'] == 'admin':
                return jsonify({'success': True, 'redirect': '/admin/dashboard'})
            else:
                return jsonify({'success': True, 'redirect': '/'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
    except Exception as e:
        print("Database error:", str(e))
        return jsonify({'success': False, 'message': 'Database error occurred'})
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Check if username already exists
        check_username_query = "SELECT * FROM users WHERE username = %s"
        db_cursor.execute(check_username_query, (username,))
        existing_username = db_cursor.fetchone()
        
        if existing_username:
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        # Check if email already exists
        check_email_query = "SELECT * FROM users WHERE email = %s"
        db_cursor.execute(check_email_query, (email,))
        existing_email = db_cursor.fetchone()
        
        if existing_email:
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        # Hash the password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        # Insert new user with hashed password and default role
        insert_query = "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, 'user')"
        db_cursor.execute(insert_query, (username, email, hashed_password))
        db_connection.commit()
        
        # Log the user in after successful registration
        session['user_id'] = db_cursor.lastrowid
        session['username'] = username
        session['role'] = 'user'
        
        return jsonify({'success': True, 'redirect': '/'})
    except Exception as e:
        print("Registration error:", str(e))
        if 'db_connection' in locals():
            db_connection.rollback()
        return jsonify({'success': False, 'message': 'Registration failed'})
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# playground.html
@app.route('/playground')
def playground():
    return render_template('playground.html')

# -------------------------------------------------------USER--------------------------------------------------------------------#
@app.route('/user/competitive')
@login_required
def user_competitive():
    return render_template('user/competitive.html')

@app.route('/user/competitive/code')
@login_required
def user_competitive_code():
    return render_template('user/competitive_code.html')

@app.route('/user/competitive/quiz')
@login_required
def user_competitive_quiz():
    return render_template('user/competitive_quiz.html')

# -------------------------------------------------------ADMIN------------------------------------------------------------------- #
# admin>dashboard.html
@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@socketio.on('connect')
def handle_connect():
    if 'user_id' not in session:
        return False  # Reject the connection if not logged in
    print('Client connected:', request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected:', request.sid)
    # Remove from queues if present
    if request.sid in code_queue:
        code_queue.remove(request.sid)
    if request.sid in quiz_queue:
        quiz_queue.remove(request.sid)
    # Handle disconnection from active matches
    for match_id, players in active_matches.items():
        if request.sid in players:
            players.remove(request.sid)
            if len(players) == 0:
                del active_matches[match_id]
            else:
                emit('opponent_disconnected', room=match_id)

@socketio.on('queue')
def handle_queue(data):
    if 'user_id' not in session:
        return False  # Reject the queue request if not logged in
        
    mode = data.get('mode')
    user_id = request.sid
    
    if mode == 'code':
        if len(code_queue) > 0:
            opponent = code_queue.pop(0)
            # Create a unique room for the match
            room = f'match_{user_id}_{opponent}'
            active_matches[room] = [user_id, opponent]
            
            join_room(room, user_id)
            join_room(room, opponent)
            
            # Notify both players
            emit('match_found', {
                'opponent': {
                    'name': session.get('username', f'Player{opponent[:4]}'),
                    'rating': 1500
                }
            }, room=room)
        else:
            code_queue.append(user_id)
            emit('queue_status', {'status': 'waiting'})
    
    elif mode == 'quiz':
        if len(quiz_queue) > 0:
            opponent = quiz_queue.pop(0)
            room = f'match_{user_id}_{opponent}'
            active_matches[room] = [user_id, opponent]
            
            join_room(room, user_id)
            join_room(room, opponent)
            
            emit('match_found', {
                'opponent': {
                    'name': session.get('username', f'Player{opponent[:4]}'),
                    'rating': 1500
                }
            }, room=room)
        else:
            quiz_queue.append(user_id)
            emit('queue_status', {'status': 'waiting'})

@socketio.on('cancel_queue')
def handle_cancel_queue():
    user_id = request.sid
    if user_id in code_queue:
        code_queue.remove(user_id)
    if user_id in quiz_queue:
        quiz_queue.remove(user_id)
    emit('queue_cancelled')

@socketio.on('start_match')
def handle_start_match():
    # Find the room the user is in
    user_id = request.sid
    for match_id, players in active_matches.items():
        if user_id in players:
            emit('match_started', room=match_id)
            break

@socketio.on('code_update')
def handle_code_update(data):
    # Find the room the user is in and broadcast to other player
    user_id = request.sid
    for match_id, players in active_matches.items():
        if user_id in players:
            emit('code_update', data, room=match_id, skip_sid=user_id)
            break

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)