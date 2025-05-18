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
code_queue = []  # Will store tuples of (socket_id, user_id)
quiz_queue = []  # Will store tuples of (socket_id, user_id)
active_matches = {}
socket_to_user = {}  # Map socket IDs to user IDs

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
@app.route('/user/classic')
@login_required
def user_classic():
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Fetch all levels with their titles and descriptions
        query = "SELECT id, title, description FROM levels"
        db_cursor.execute(query)
        levels = db_cursor.fetchall()
        
        return render_template('user/classic.html', levels=levels)
    except Exception as e:
        print("Database error:", str(e))
        return render_template('user/classic.html', levels=[])
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/user/classic/<level>')
@login_required
def user_chapter_list(level):
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Get level info
        level_query = "SELECT id, title FROM levels WHERE title = %s"
        db_cursor.execute(level_query, (level,))
        level_info = db_cursor.fetchone()
        
        if not level_info:
            return redirect(url_for('user_classic'))
        
        # Get chapters for this level
        chapters_query = """
        SELECT c.*, COALESCE(up.progress, 0) as user_progress, COALESCE(up.completed, FALSE) as is_completed
        FROM chapters c
        LEFT JOIN user_progress up ON c.id = up.chapter_id AND up.user_id = %s
        WHERE c.level_id = %s
        ORDER BY c.order_num
        """
        db_cursor.execute(chapters_query, (session['user_id'], level_info['id']))
        chapters = db_cursor.fetchall()
        
        return render_template('user/chapter_list.html', 
                             level=level_info['title'], 
                             chapters=chapters)
    except Exception as e:
        print("Database error:", str(e))
        return redirect(url_for('user_classic'))
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/user/classic/<level>/<int:chapter_id>')
@login_required
def user_lesson_content(level, chapter_id):
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Get chapter info
        chapter_query = """
        SELECT c.*, l.title as level_title 
        FROM chapters c 
        JOIN levels l ON c.level_id = l.id 
        WHERE c.id = %s
        """
        db_cursor.execute(chapter_query, (chapter_id,))
        chapter = db_cursor.fetchone()
        
        if not chapter:
            return redirect(url_for('user_chapter_list', level=level))
        
        # Get lesson content for this chapter
        content_query = """
        SELECT * FROM lesson_content 
        WHERE chapter_id = %s 
        ORDER BY page_num
        """
        db_cursor.execute(content_query, (chapter_id,))
        lesson_pages = db_cursor.fetchall()
        
        if not lesson_pages:
            return redirect(url_for('user_chapter_list', level=level))
        
        # Get user progress for this chapter
        progress_query = """
        SELECT progress FROM user_progress 
        WHERE user_id = %s AND chapter_id = %s
        """
        db_cursor.execute(progress_query, (session['user_id'], chapter_id))
        progress = db_cursor.fetchone()
        
        current_page = 1
        if progress:
            current_page = min(progress['progress'] + 1, len(lesson_pages))
        
        return render_template('user/lesson-content.html',
                             chapter=chapter,
                             lesson_pages=lesson_pages,
                             current_page=current_page,
                             total_pages=len(lesson_pages))
    except Exception as e:
        print("Database error:", str(e))
        return redirect(url_for('user_chapter_list', level=level))
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/user/classic/<level>/<int:chapter_id>/progress', methods=['POST'])
@login_required
def update_lesson_progress(level, chapter_id):
    try:
        data = request.get_json()
        page_num = data.get('page_num', 1)
        
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor()
        
        # Update or insert progress
        upsert_query = """
        INSERT INTO user_progress (user_id, chapter_id, progress, completed)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
        progress = VALUES(progress),
        completed = VALUES(completed)
        """
        
        # Calculate progress percentage and completion
        progress = (page_num / data.get('total_pages', 1)) * 100
        completed = page_num >= data.get('total_pages', 1)
        
        db_cursor.execute(upsert_query, (session['user_id'], chapter_id, progress, completed))
        db_connection.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        print("Database error:", str(e))
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

# Update the startChapter function in chapter_list.html
@app.route('/user/classic/<level>/<int:chapter_id>/start')
@login_required
def start_chapter(level, chapter_id):
    return redirect(url_for('user_lesson_content', level=level, chapter_id=chapter_id))

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
    socket_to_user[request.sid] = session['user_id']
    print('Client connected:', request.sid, 'User:', session['user_id'])

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected:', request.sid)
    # Remove from socket_to_user mapping
    if request.sid in socket_to_user:
        del socket_to_user[request.sid]
    # Remove from queues if present
    code_queue[:] = [(sid, uid) for sid, uid in code_queue if sid != request.sid]
    quiz_queue[:] = [(sid, uid) for sid, uid in quiz_queue if sid != request.sid]
    # Handle disconnection from active matches
    for match_id, players in active_matches.items():
        if request.sid in players:
            players.remove(request.sid)
            if len(players) == 0:
                del active_matches[match_id]
            else:
                emit('opponent_disconnected', room=match_id)

def get_username_by_user_id(user_id):
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        query = "SELECT username FROM users WHERE id = %s"
        db_cursor.execute(query, (user_id,))
        result = db_cursor.fetchone()
        return result['username'] if result else f'Player{user_id}'
    except Exception as e:
        print("Database error:", str(e))
        return f'Player{user_id}'
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@socketio.on('queue')
def handle_queue(data):
    if 'user_id' not in session:
        return False  # Reject the queue request if not logged in
        
    mode = data.get('mode')
    socket_id = request.sid
    user_id = session['user_id']
    
    if mode == 'code':
        if len(code_queue) > 0:
            opponent_socket, opponent_user_id = code_queue.pop(0)
            # Create a unique room for the match
            room = f'match_{socket_id}_{opponent_socket}'
            active_matches[room] = [socket_id, opponent_socket]
            
            join_room(room, socket_id)
            join_room(room, opponent_socket)
            
            # Get opponent's username from database
            opponent_username = get_username_by_user_id(opponent_user_id)
            current_username = get_username_by_user_id(user_id)
            
            # Notify both players with their respective opponent's username
            emit('match_found', {
                'opponent': {
                    'name': opponent_username,
                    'rating': 1500
                }
            }, room=socket_id)
            
            emit('match_found', {
                'opponent': {
                    'name': current_username,
                    'rating': 1500
                }
            }, room=opponent_socket)
        else:
            code_queue.append((socket_id, user_id))
            emit('queue_status', {'status': 'waiting'})
    
    elif mode == 'quiz':
        if len(quiz_queue) > 0:
            opponent_socket, opponent_user_id = quiz_queue.pop(0)
            room = f'match_{socket_id}_{opponent_socket}'
            active_matches[room] = [socket_id, opponent_socket]
            
            join_room(room, socket_id)
            join_room(room, opponent_socket)
            
            # Get opponent's username from database
            opponent_username = get_username_by_user_id(opponent_user_id)
            current_username = get_username_by_user_id(user_id)
            
            # Notify both players with their respective opponent's username
            emit('match_found', {
                'opponent': {
                    'name': opponent_username,
                    'rating': 1500
                }
            }, room=socket_id)
            
            emit('match_found', {
                'opponent': {
                    'name': current_username,
                    'rating': 1500
                }
            }, room=opponent_socket)
        else:
            quiz_queue.append((socket_id, user_id))
            emit('queue_status', {'status': 'waiting'})

@socketio.on('cancel_queue')
def handle_cancel_queue():
    socket_id = request.sid
    # Remove from queues if present
    code_queue[:] = [(sid, uid) for sid, uid in code_queue if sid != socket_id]
    quiz_queue[:] = [(sid, uid) for sid, uid in quiz_queue if sid != socket_id]
    emit('queue_cancelled')

@socketio.on('start_match')
def handle_start_match():
    # Find the room the user is in
    socket_id = request.sid
    for match_id, players in active_matches.items():
        if socket_id in players:
            emit('match_started', room=match_id)
            break

@socketio.on('code_update')
def handle_code_update(data):
    # Find the room the user is in and broadcast to other player
    socket_id = request.sid
    for match_id, players in active_matches.items():
        if socket_id in players:
            emit('code_update', data, room=match_id, skip_sid=socket_id)
            break

# Create chapters table if it doesn't exist
def init_chapters_table():
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor()
        
        # Create chapters table
        create_chapters_table = """
        CREATE TABLE IF NOT EXISTS chapters (
            id INT AUTO_INCREMENT PRIMARY KEY,
            level_id VARCHAR(50),
            name VARCHAR(100) NOT NULL,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            xp_reward INT DEFAULT 0,
            points_reward INT DEFAULT 0,
            order_num INT NOT NULL,
            FOREIGN KEY (level_id) REFERENCES levels(id) ON DELETE CASCADE
        )
        """
        
        db_cursor.execute(create_chapters_table)
        db_connection.commit()
        
        # Create user_progress table to track chapter completion
        create_user_progress_table = """
        CREATE TABLE IF NOT EXISTS user_progress (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            chapter_id INT NOT NULL,
            progress INT DEFAULT 0,
            completed BOOLEAN DEFAULT FALSE,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE,
            UNIQUE KEY unique_user_chapter (user_id, chapter_id)
        )
        """
        
        db_cursor.execute(create_user_progress_table)
        db_connection.commit()
        
    except Exception as e:
        print("Error initializing tables:", str(e))
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

# Call this when the app starts
init_chapters_table()

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)