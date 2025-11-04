import os
# Enable eventlet monkey patching only when explicitly requested via env
try:
    _use_eventlet = os.getenv('USE_EVENTLET', '0').strip()
    if _use_eventlet in ('1', 'true', 'True'):
        import eventlet  # type: ignore
        eventlet.monkey_patch()
except Exception:
    pass

from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, flash, jsonify
# mysql connector 
import mysql.connector
from mysql.connector import errors as mysql_errors
from mysql.connector.pooling import MySQLConnectionPool
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
from functools import wraps
import bcrypt
import requests 
import base64
from urllib.parse import quote, unquote
from werkzeug.utils import secure_filename
import math
import time
import random
import subprocess
import re
from datetime import datetime
from html import escape, unescape
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, Dimension, RunReportRequest
import calendar
from threading import Lock

# Load environment variables from a local .env file if present (useful for local dev)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# Google Analytics Measurement ID
GA_MEASUREMENT_ID = 'G-8N1JFLPGQ0'  # Measurement ID

# Configure upload settings
UPLOAD_FOLDER = 'static/uploads/lesson_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

HTML_BREAK_RE = re.compile(r'<\s*br\s*/?>', re.IGNORECASE)
HTML_BLOCK_RE = re.compile(r'</?(p|li|div|h[1-6])\s*>', re.IGNORECASE)
HTML_TAG_RE = re.compile(r'<[^>]+>')
CODE_TAG_RE = re.compile(r'<code[^>]*>(.*?)</code>', re.IGNORECASE | re.DOTALL)
BACKTICK_CODE_RE = re.compile(r'`([^`]+)`')


def _format_duration_short(total_seconds):
    try:
        seconds = int(total_seconds or 0)
    except (TypeError, ValueError):
        seconds = 0
    if seconds <= 0:
        return "0m"
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def _format_relative_time(moment):
    if not moment:
        return ''
    if not hasattr(moment, 'tzinfo'):
        return ''
    if moment.tzinfo is not None:
        moment = moment.replace(tzinfo=None)
    now = datetime.utcnow()
    delta = now - moment
    total_seconds = max(int(delta.total_seconds()), 0)
    days = total_seconds // 86400
    if days > 0:
        if days == 1:
            return "1 day ago"
        if days < 7:
            return f"{days} days ago"
        weeks = days // 7
        if weeks == 1:
            return "1 week ago"
        return f"{weeks} weeks ago"
    hours = total_seconds // 3600
    if hours > 0:
        return f"{hours}h ago"
    minutes = total_seconds // 60
    if minutes > 0:
        return f"{minutes}m ago"
    if total_seconds > 0:
        return f"{total_seconds}s ago"
    return "just now"


def render_inline_code_spans(value: str) -> str:
    """Replace backtick-delimited segments with escaped inline code blocks."""
    if not value:
        return ''

    def replace(match: re.Match) -> str:
        inner = match.group(1)
        return f'<code class="inline-code">{escape(inner)}</code>'

    return BACKTICK_CODE_RE.sub(replace, value)


def strip_html_to_text(value: str) -> str:
    """Convert HTML content into a readable plain-text summary."""
    if not value:
        return ''

    # Normalize backtick-wrapped inline code before stripping
    captured_codes: list[str] = []

    def extract_code(match: re.Match) -> str:
        inner = match.group(1)
        # Inner may already contain escaped entities; preserve by unescaping later
        captured_codes.append(unescape(inner))
        return f'`__CODE_SNIPPET_{len(captured_codes) - 1}__`'

    value = CODE_TAG_RE.sub(extract_code, value)

    # Normalize common block-level tags into line breaks before stripping everything else
    text = HTML_BREAK_RE.sub('\n', value)
    text = HTML_BLOCK_RE.sub('\n', text)
    text = HTML_TAG_RE.sub('', text)
    text = unescape(text)

    # Restore captured inline code snippets
    for index, snippet in enumerate(captured_codes):
        placeholder = f'`__CODE_SNIPPET_{index}__`'
        text = text.replace(placeholder, f'`{snippet}`')

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return '\n'.join(lines)

DEFAULT_RATING = max(int(os.getenv('DEFAULT_RATING', '100')), 0)
RATING_XP_DIVISOR = max(int(os.getenv('RATING_XP_DIVISOR', '20')), 1)
RATING_POINTS_DIVISOR = max(int(os.getenv('RATING_POINTS_DIVISOR', '10')), 1)
RATING_CHAPTER_BONUS = max(int(os.getenv('RATING_CHAPTER_BONUS', '15')), 0)
MATCHMAKING_MAX_DELTA = max(int(os.getenv('MATCHMAKING_MAX_DELTA', '0')), 0)
MATCHMAKING_FORCE_MATCH_SIZE = max(int(os.getenv('MATCHMAKING_FORCE_MATCH_SIZE', '4')), 1)


def calculate_rating(xp_total: int, points_total: int, completed_chapters: int) -> int:
    """Compute a deterministic rating based on a user's overall progress."""
    rating = DEFAULT_RATING
    rating += max(xp_total, 0) // RATING_XP_DIVISOR
    rating += max(points_total, 0) // RATING_POINTS_DIVISOR
    rating += max(completed_chapters, 0) * RATING_CHAPTER_BONUS
    return int(max(rating, DEFAULT_RATING))


def get_completed_chapter_count(db_cursor, user_id: int) -> int:
    db_cursor.execute(
        "SELECT COUNT(*) FROM user_progress WHERE user_id = %s AND completed = 1",
        (user_id,),
    )
    row = db_cursor.fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def recalculate_all_user_ratings() -> None:
    """Ensure legacy rows receive an up-to-date rating on startup."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, xp, points FROM user_stats")
        rows = cursor.fetchall() or []
        for user_id, xp_total, points_total in rows:
            try:
                completed = get_completed_chapter_count(cursor, user_id)
                total_xp = int(xp_total or 0)
                total_points = int(points_total or 0)
                new_rating = calculate_rating(total_xp, total_points, completed)
                cursor.execute(
                    "UPDATE user_stats SET rating = %s WHERE user_id = %s",
                    (new_rating, user_id),
                )
            except Exception as inner_err:
                print(f"Rating recalculation failed for user {user_id}: {inner_err}")
        conn.commit()
    except Exception as e:
        print("Rating recalculation error:", str(e))
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


def get_user_rating(user_id: int) -> int:
    """Fetch a user's current rating, defaulting when no stats are present."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT rating FROM user_stats WHERE user_id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        if row and row[0] is not None:
            return int(row[0])
    except Exception as e:
        print("Rating fetch error:", str(e))
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
    return DEFAULT_RATING


def fetch_leaderboard(limit: int = 100):
    """Return leaderboard rows (sorted) and the latest stats timestamp."""
    conn = None
    cursor = None
    last_refresh = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        leaderboard_query = """
            SELECT
                u.id AS user_id,
                u.username,
                COALESCE(MAX(us.points), 0) AS points,
                COALESCE(MAX(us.rating), %s) AS rating,
                COALESCE(MAX(us.xp), 0) AS xp,
                COALESCE(MAX(us.level), 1) AS user_level,
                COUNT(DISTINCT ub.badge_id) AS badges
            FROM users u
            LEFT JOIN user_stats us ON u.id = us.user_id
            LEFT JOIN user_badges ub ON u.id = ub.user_id
            GROUP BY u.id, u.username
            ORDER BY points DESC, rating DESC, xp DESC, u.username ASC
            LIMIT %s
        """
        cursor.execute(leaderboard_query, (DEFAULT_RATING, limit))
        rows = cursor.fetchall() or []
        for index, row in enumerate(rows, start=1):
            row["rank"] = index
            row["badges"] = int(row.get("badges", 0) or 0)
            row["points"] = int(row.get("points", 0) or 0)
            row["rating"] = int(row.get("rating", DEFAULT_RATING) or DEFAULT_RATING)
            row["xp"] = int(row.get("xp", 0) or 0)
            row["user_level"] = int(row.get("user_level", 1) or 1)

        cursor.execute("SELECT MAX(last_updated) AS last_refresh FROM user_stats")
        meta = cursor.fetchone()
        if meta and meta.get("last_refresh"):
            last_refresh = meta["last_refresh"]

        return rows, last_refresh
    except Exception as e:
        print("Leaderboard fetch error:", str(e))
        return [], last_refresh
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


def _pop_best_match(queue: list, target_rating: int):
    """Return the closest-rated opponent from the queue while honoring tolerance."""
    if not queue:
        return None

    best_index = 0
    best_diff = abs(queue[0][2] - target_rating)
    for idx in range(1, len(queue)):
        diff = abs(queue[idx][2] - target_rating)
        if diff < best_diff:
            best_index = idx
            best_diff = diff

    if MATCHMAKING_MAX_DELTA and best_diff > MATCHMAKING_MAX_DELTA and len(queue) < MATCHMAKING_FORCE_MATCH_SIZE:
        return None

    return queue.pop(best_index)

_db_pool = None  # MySQLConnectionPool instance
_db_pool_config = None  # Cached config dict used to build the pool
_db_pool_lock = Lock()


def _build_db_config() -> dict:
    """Build connection keyword arguments based on environment variables."""
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "3306"))
    db_user = os.getenv("DB_USER", "root")
    # Support both DB_PASSWORD and DB_PASS (Render screenshot shows DB_PASS)
    db_password = os.getenv("DB_PASSWORD", os.getenv("DB_PASS", ""))
    db_name = os.getenv("DB_NAME", "capstone_v1")

    ssl_ca = os.getenv("DB_SSL_CA")
    ssl_disabled_env = os.getenv("DB_SSL_DISABLED", "0").strip()
    ssl_disabled = ssl_disabled_env in ("1", "true", "True")

    connect_kwargs = {
        "host": db_host,
        "port": db_port,
        "user": db_user,
        "password": db_password,
        "database": db_name,
        "autocommit": False,
        "connection_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
    }

    # Configure SSL for Aiven if provided
    if ssl_disabled:
        connect_kwargs["ssl_disabled"] = True
    elif ssl_ca:
        connect_kwargs["ssl_ca"] = ssl_ca

    return connect_kwargs


def _get_db_pool(config: dict) -> MySQLConnectionPool:
    """Create or reuse a global connection pool."""
    global _db_pool, _db_pool_config
    if _db_pool is not None and _db_pool_config == config:
        return _db_pool

    with _db_pool_lock:
        if _db_pool is not None and _db_pool_config == config:
            return _db_pool

        pool_size = max(int(os.getenv("DB_POOL_SIZE", "10")), 1)
        pool_name = os.getenv("DB_POOL_NAME", "webscape_pool")
        _db_pool = MySQLConnectionPool(
            pool_name=pool_name,
            pool_size=pool_size,
            pool_reset_session=True,
            **config,
        )
        _db_pool_config = config.copy()
        return _db_pool


def get_db_connection():
    """Get a pooled database connection (falls back to direct connection)."""
    config = _build_db_config()
    try:
        pool = _get_db_pool(config)
        connection = pool.get_connection()
    except mysql_errors.PoolError as pool_error:
        print("DB pool issue, falling back to direct connection:", str(pool_error))
        connection = mysql.connector.connect(**config)

    # Ensure autocommit stays disabled for compatibility with existing code
    if connection.autocommit:
        connection.autocommit = False
    return connection

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'lux')
socketio = SocketIO(app, cors_allowed_origins="*")

# Add Google Analytics context processor
@app.context_processor
def inject_ga():
    return {
        'ga_measurement_id': GA_MEASUREMENT_ID,
        'ga_script': f'''
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', '{GA_MEASUREMENT_ID}');
        </script>
        '''
    }

# Expose Google Client ID to templates (for Google Identity Services)
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')

@app.context_processor
def inject_google_client_id():
    return {
        'google_client_id': GOOGLE_CLIENT_ID
    }

# Store active queues and matches
code_queue = []  # Will store tuples of (socket_id, user_id, rating)
quiz_queue = []  # Will store tuples of (socket_id, user_id, rating)
active_matches = {}  # room_id -> { players: [sid1, sid2], mode: 'code'|'quiz' }
socket_to_user = {}  # Map socket IDs to user IDs

# Default challenge used if the database has no PvP challenges configured
DEFAULT_CODE_CHALLENGE = {
    "id": 0,
    "title": "Sum of Two Numbers",
    "description": "Write a JavaScript function that returns the sum of two numbers.",
    "function_name": "sumTwoNumbers",
    "language": "javascript",
    "starter_code": "function sumTwoNumbers(a, b) {\n  // Your code here\n}\n",
    "time_limit": 300,
    "test_cases": [
        {"input": [1, 2], "output": "3"},
        {"input": [5, 7], "output": "12"},
        {"input": [-1, 1], "output": "0"},
    ],
}

DEFAULT_QUIZ_QUESTION = {
    "id": 0,
    "question": "Which HTML tag creates the largest heading on a page?",
    "choices": [
        "<title>",
        "<h1>",
        "<heading>",
        "<h6>",
    ],
    "correct_index": 1,
    "time_limit": 45,
    "explanation": "<h1> renders the highest-level heading and is the largest by default.",
}

# Store ongoing code matches: {room_id: {...}}
code_matches = {}
quiz_matches = {}


def _finalize_match(match_id: str) -> None:
    """Remove all in-memory state for a completed or cancelled match."""
    active_matches.pop(match_id, None)
    code_matches.pop(match_id, None)
    quiz_matches.pop(match_id, None)

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

# Ensure DB has columns required for Google auth
def init_google_auth_columns():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("ALTER TABLE users ADD COLUMN google_id VARCHAR(255) NULL")
            conn.commit()
        except Exception:
            pass
        try:
            cur.execute("CREATE UNIQUE INDEX idx_users_google_id ON users(google_id)")
            conn.commit()
        except Exception:
            pass
    except Exception as e:
        print("init_google_auth_columns error:", str(e))
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

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

@app.route('/auth/google', methods=['POST'])
def auth_google():
    try:
        data = request.get_json(force=True)
        id_token = data.get('credential') or data.get('id_token')
        if not id_token:
            return jsonify({'success': False, 'message': 'Missing credential'}), 400

        # Verify token via Google tokeninfo endpoint
        verify_resp = requests.get('https://oauth2.googleapis.com/tokeninfo', params={'id_token': id_token}, timeout=10)
        if verify_resp.status_code != 200:
            return jsonify({'success': False, 'message': 'Invalid Google token'}), 400
        payload = verify_resp.json()

        aud = payload.get('aud') or payload.get('azp')
        if GOOGLE_CLIENT_ID and aud != GOOGLE_CLIENT_ID:
            return jsonify({'success': False, 'message': 'Token audience mismatch'}), 400

        google_sub = payload.get('sub')
        email = payload.get('email')
        name = payload.get('name') or (payload.get('given_name') or 'User')
        picture = payload.get('picture')
        if not google_sub:
            return jsonify({'success': False, 'message': 'Invalid token payload'}), 400

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # Prefer lookup by google_id
        cur.execute("SELECT * FROM users WHERE google_id = %s", (google_sub,))
        user = cur.fetchone()

        # If not found, try by email then link
        if not user and email:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
            if user:
                try:
                    cur2 = conn.cursor()
                    cur2.execute("UPDATE users SET google_id = %s WHERE id = %s", (google_sub, user['id']))
                    conn.commit()
                    cur2.close()
                except Exception:
                    conn.rollback()

        # If still not found, create
        if not user:
            base_username = (name or (email.split('@')[0] if email else 'user')).strip().lower().replace(' ', '')
            if not base_username:
                base_username = 'user'
            username = base_username
            suffix = 1
            while True:
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                exists = cur.fetchone()
                if not exists:
                    break
                suffix += 1
                username = f"{base_username}{suffix}"

            try:
                cur.execute(
                    "INSERT INTO users (username, email, password, role, avatar_path, google_id) VALUES (%s, %s, %s, %s, %s, %s)",
                    (username, email or '', '', 'student', picture, google_sub)
                )
                conn.commit()
                new_user_id = cur.lastrowid
                user = {'id': new_user_id, 'username': username, 'email': email or '', 'role': 'student'}
            except Exception as e:
                conn.rollback()
                print('Google auth insert error:', str(e))
                return jsonify({'success': False, 'message': 'Failed to create account'}), 500

        # Start session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user.get('role', 'student')

        redirect_url = '/admin/dashboard' if session.get('role') == 'admin' else '/'
        return jsonify({'success': True, 'redirect': redirect_url})
    except Exception as e:
        print('auth_google error:', str(e))
        return jsonify({'success': False, 'message': 'Authentication failed'}), 500

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
        insert_query = "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, 'student')"
        db_cursor.execute(insert_query, (username, email, hashed_password))
        db_connection.commit()
        
        # Log the user in after successful registration
        session['user_id'] = db_cursor.lastrowid
        session['username'] = username
        session['role'] = 'student'
        
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

@app.route('/options')
def options():
    return render_template('options.html')

@app.route('/rankings')
def rankings():
    leaderboard_rows, last_refresh = fetch_leaderboard(limit=100)
    current_user_id = session.get('user_id')

    for row in leaderboard_rows:
        row["is_current"] = current_user_id is not None and row["user_id"] == current_user_id

    top_three = leaderboard_rows[:3]
    total_players = len(leaderboard_rows)
    formatted_refresh = None
    if last_refresh:
        try:
            formatted_refresh = last_refresh.strftime("%b %d, %Y %I:%M %p")
        except Exception:
            formatted_refresh = str(last_refresh)

    return render_template(
        'rankings.html',
        top_three=top_three,
        leaderboard=leaderboard_rows,
        total_players=total_players,
        last_refreshed=formatted_refresh,
    )

# -------------------------------------------------------USER--------------------------------------------------------------------#
@app.route('/user/classic')
@login_required
def user_classic():
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Fetch all levels with their titles, descriptions, and image URLs
        query = "SELECT id, title, description, image_url FROM levels"
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
    level = unquote(level)
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
    level = unquote(level)
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
        # For quiz pages, fetch choices from lesson_choices
        for page in lesson_pages:
            page['content'] = render_inline_code_spans(page.get('content', '') or '')
            page['notes'] = render_inline_code_spans(page.get('notes', '') or '')
            if page.get('page_type') == 'quiz':
                db_cursor.execute("SELECT id, choice_text, is_correct FROM lesson_choices WHERE lesson_content_id = %s", (page['id'],))
                page['choices'] = db_cursor.fetchall()
        if not lesson_pages:
            return redirect(url_for('user_chapter_list', level=level))
        # Get user progress for this chapter
        progress_query = """
        SELECT progress FROM user_progress 
        WHERE user_id = %s AND chapter_id = %s
        """
        db_cursor.execute(progress_query, (session['user_id'], chapter_id))
        progress = db_cursor.fetchone()
        # Get the requested page number from URL parameter
        requested_page = request.args.get('page', type=int)
        # Calculate current page
        if requested_page is not None:
            # If a specific page was requested, use it (but validate it)
            current_page = min(max(1, requested_page), len(lesson_pages))
        else:
            # Always start at page 1 if progress is 100
            current_page = 1
            if progress and progress.get('progress') is not None:
                prog_val = progress['progress']
                if prog_val is None or prog_val <= 0:
                    current_page = 1
                elif prog_val >= 100:
                    current_page = 1
                else:
                    progress_page = math.ceil((prog_val / 100) * len(lesson_pages))
                    current_page = min(max(1, progress_page + 1), len(lesson_pages))
        # Get the current page content
        current_page_content = next((page for page in lesson_pages if page['page_num'] == current_page), None)
        if not current_page_content:
            return redirect(url_for('user_chapter_list', level=level))
        return render_template('user/lesson-content.html',
                             chapter=chapter,
                             lesson_pages=lesson_pages,
                             current_page=current_page,
                             current_page_content=current_page_content,
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

        # Get total number of pages for this chapter
        db_cursor.execute("""
            SELECT COUNT(*) 
            FROM lesson_content 
            WHERE chapter_id = %s
        """, (chapter_id,))
        total_pages = db_cursor.fetchone()[0]

        # Calculate progress percentage based on current page and total pages
        progress = (page_num / total_pages) * 100 if total_pages > 0 else 0
        completed = page_num >= total_pages

        # Fetch current progress and completed status
        db_cursor.execute("SELECT progress, completed FROM user_progress WHERE user_id = %s AND chapter_id = %s", (session['user_id'], chapter_id))
        current = db_cursor.fetchone()
        current_progress = current[0] if current else 0
        was_completed = bool(current[1]) if current and len(current) > 1 else False

        # Only update if new progress is greater
        if progress > current_progress:
            upsert_query = """
            INSERT INTO user_progress (user_id, chapter_id, progress, completed)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            progress = VALUES(progress),
            completed = VALUES(completed)
            """
            db_cursor.execute(upsert_query, (session['user_id'], chapter_id, progress, completed))
            db_connection.commit()
            updated_progress = progress
            updated_completed = completed
        else:
            updated_progress = current_progress
            updated_completed = was_completed

        # --- REWARD & BADGE LOGIC ---
        badges_awarded = []
        reward_given = False
        rating_update = None
        if completed and not was_completed:
            # Fetch xp_reward and points_reward from chapters table
            db_cursor.execute("SELECT xp_reward, points_reward FROM chapters WHERE id = %s", (chapter_id,))
            rewards = db_cursor.fetchone()
            if rewards:
                xp_reward, points_reward = rewards
                xp_reward = int(xp_reward or 0)
                points_reward = int(points_reward or 0)
                # Update user_stats with the new totals and derived rating
                db_cursor.execute(
                    "SELECT xp, points, rating FROM user_stats WHERE user_id = %s",
                    (session['user_id'],),
                )
                stats = db_cursor.fetchone()
                current_xp = int(stats[0]) if stats and stats[0] is not None else 0
                current_points = int(stats[1]) if stats and stats[1] is not None else 0
                current_rating = int(stats[2]) if stats and len(stats) > 2 and stats[2] is not None else DEFAULT_RATING

                new_xp_total = current_xp + xp_reward
                new_points_total = current_points + points_reward
                completed_chapters = get_completed_chapter_count(db_cursor, session['user_id'])
                new_rating = calculate_rating(new_xp_total, new_points_total, completed_chapters)

                if stats:
                    db_cursor.execute(
                        "UPDATE user_stats SET xp = %s, points = %s, rating = %s WHERE user_id = %s",
                        (new_xp_total, new_points_total, new_rating, session['user_id'])
                    )
                else:
                    db_cursor.execute(
                        "INSERT INTO user_stats (user_id, xp, points, rating) VALUES (%s, %s, %s, %s)",
                        (session['user_id'], new_xp_total, new_points_total, new_rating)
                    )
                db_connection.commit()
                reward_given = True
                rating_update = {
                    'previous_rating': current_rating,
                    'new_rating': new_rating,
                    'delta': new_rating - current_rating
                }

            # --- BADGE AWARDING LOGIC ---
            try:
                # Check for "First Steps" badge - award when user completes their first chapter
                db_cursor.execute("SELECT COUNT(*) FROM user_badges WHERE user_id = %s", (session['user_id'],))
                badge_count_row = db_cursor.fetchone()
                current_badge_count = badge_count_row[0] if badge_count_row else 0
                print(f"Badge check - User {session['user_id']} has {current_badge_count} badges")

                if current_badge_count == 0:
                    # Award "First Steps" badge
                    db_cursor.execute("SELECT id, name, description, icon FROM badges WHERE LOWER(name) = %s LIMIT 1", ('first steps',))
                    badge_row = db_cursor.fetchone()
                    print(f"Badge query result: {badge_row}")
                    if badge_row:
                        badge_id, badge_name, badge_desc, badge_icon = badge_row
                        # Insert badge award (ignore if already exists)
                        db_cursor.execute(
                            "INSERT IGNORE INTO user_badges (user_id, badge_id) VALUES (%s, %s)",
                            (session['user_id'], badge_id)
                        )
                        print(f"Insert rowcount: {db_cursor.rowcount}")
                        if db_cursor.rowcount > 0:
                            db_connection.commit()
                            badges_awarded.append({
                                'id': badge_id,
                                'name': badge_name,
                                'description': badge_desc,
                                'icon': badge_icon
                            })
                            print(f"✅ Badge awarded: {badge_name} to user {session['user_id']}")
            except Exception as badge_error:
                print("Badge award error:", str(badge_error))
                import traceback
                traceback.print_exc()
                try:
                    db_connection.rollback()
                except Exception:
                    pass

        # Emit socket event for real-time badge notification
        if badges_awarded:
            print(f"🎯 Emitting badge_awarded event for {len(badges_awarded)} badges to user {session['user_id']}")
            print(f"Socket mapping: {socket_to_user}")
            try:
                for sid, uid in list(socket_to_user.items()):
                    if uid == session['user_id']:
                        print(f"📡 Emitting to socket {sid}")
                        socketio.emit('badge_awarded', {'badges': badges_awarded}, room=sid)
            except Exception as socket_error:
                print("Socket emit error:", str(socket_error))
                import traceback
                traceback.print_exc()

        return jsonify({
            'success': True,
            'progress': updated_progress,
            'completed': updated_completed,
            'total_pages': total_pages,
            'reward_given': reward_given,
            'badges_awarded': badges_awarded,
            'rating_update': rating_update
        })
    except Exception as e:
        print("Database error:", str(e))
        if 'db_connection' in locals():
            try:
                db_connection.rollback()
            except Exception:
                pass
        return jsonify({'success': False, 'error': str(e)})
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

# ============== LESSON COMMENTS API ROUTES ==============

@app.route('/api/lessons/<int:lesson_content_id>/comments', methods=['GET'])
@login_required
def get_lesson_comments(lesson_content_id):
    """Get all comments for a lesson page with replies and like counts"""
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Get all comments for this lesson page
        db_cursor.execute("""
            SELECT 
                lc.id,
                lc.user_id,
                u.username,
                lc.comment_text,
                lc.created_at,
                lc.updated_at,
                (SELECT COUNT(*) FROM lesson_comment_likes WHERE comment_id = lc.id) AS like_count,
                (SELECT COUNT(*) FROM lesson_comment_likes WHERE comment_id = lc.id AND user_id = %s) AS user_liked,
                (SELECT COUNT(*) FROM lesson_comment_replies WHERE comment_id = lc.id) AS reply_count
            FROM lesson_comments lc
            JOIN users u ON lc.user_id = u.id
            WHERE lc.lesson_content_id = %s
            ORDER BY lc.created_at DESC
        """, (session['user_id'], lesson_content_id))
        
        comments = db_cursor.fetchall()
        
        # Get replies for each comment
        for comment in comments:
            # Convert user_liked to boolean 'liked' for frontend
            comment['liked'] = bool(comment.get('user_liked', 0))
            
            db_cursor.execute("""
                SELECT 
                    lcr.id,
                    lcr.user_id,
                    u.username,
                    lcr.reply_text,
                    lcr.created_at,
                    (SELECT COUNT(*) FROM lesson_reply_likes WHERE reply_id = lcr.id) AS like_count,
                    (SELECT COUNT(*) FROM lesson_reply_likes WHERE reply_id = lcr.id AND user_id = %s) AS user_liked
                FROM lesson_comment_replies lcr
                JOIN users u ON lcr.user_id = u.id
                WHERE lcr.comment_id = %s
                ORDER BY lcr.created_at ASC
            """, (session['user_id'], comment['id']))
            
            replies = db_cursor.fetchall()
            # Convert user_liked to boolean 'liked' for replies too
            for reply in replies:
                reply['liked'] = bool(reply.get('user_liked', 0))
            comment['replies'] = replies
        
        db_cursor.close()
        db_connection.close()
        
        return jsonify({'success': True, 'comments': comments})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/lessons/<int:lesson_content_id>/comments', methods=['POST'])
@login_required
def post_lesson_comment(lesson_content_id):
    """Create a new comment on a lesson page"""
    try:
        data = request.json
        comment_text = data.get('comment_text', '').strip()
        
        if not comment_text:
            return jsonify({'success': False, 'error': 'Comment cannot be empty'}), 400
        
        if len(comment_text) > 2000:
            return jsonify({'success': False, 'error': 'Comment is too long (max 2000 characters)'}), 400
        
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Verify lesson content exists
        db_cursor.execute("SELECT id FROM lesson_content WHERE id = %s", (lesson_content_id,))
        if not db_cursor.fetchone():
            db_cursor.close()
            db_connection.close()
            return jsonify({'success': False, 'error': 'Lesson not found'}), 404
        
        # Create comment
        db_cursor.execute("""
            INSERT INTO lesson_comments (lesson_content_id, user_id, comment_text)
            VALUES (%s, %s, %s)
        """, (lesson_content_id, session['user_id'], comment_text))
        
        comment_id = db_cursor.lastrowid
        db_connection.commit()
        
        # Get the created comment with user info
        db_cursor.execute("""
            SELECT 
                lc.id,
                lc.user_id,
                u.username,
                lc.comment_text,
                lc.created_at,
                0 AS like_count,
                0 AS user_liked,
                0 AS reply_count
            FROM lesson_comments lc
            JOIN users u ON lc.user_id = u.id
            WHERE lc.id = %s
        """, (comment_id,))
        
        comment = db_cursor.fetchone()
        comment['replies'] = []
        
        db_cursor.close()
        db_connection.close()
        
        return jsonify({'success': True, 'comment': comment}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_lesson_comment(comment_id):
    """Delete a comment (only by comment author or admin)"""
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Get comment
        db_cursor.execute("SELECT user_id FROM lesson_comments WHERE id = %s", (comment_id,))
        comment = db_cursor.fetchone()
        
        if not comment:
            db_cursor.close()
            db_connection.close()
            return jsonify({'success': False, 'error': 'Comment not found'}), 404
        
        # Check authorization
        if comment['user_id'] != session['user_id'] and session.get('role') != 'admin':
            db_cursor.close()
            db_connection.close()
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Delete comment (cascades to replies and likes)
        db_cursor.execute("DELETE FROM lesson_comments WHERE id = %s", (comment_id,))
        db_connection.commit()
        
        db_cursor.close()
        db_connection.close()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/comments/<int:comment_id>/replies', methods=['POST'])
@login_required
def post_comment_reply(comment_id):
    """Add a reply to a comment"""
    try:
        data = request.json
        reply_text = data.get('reply_text', '').strip()
        
        if not reply_text:
            return jsonify({'success': False, 'error': 'Reply cannot be empty'}), 400
        
        if len(reply_text) > 1000:
            return jsonify({'success': False, 'error': 'Reply is too long (max 1000 characters)'}), 400
        
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Verify comment exists
        db_cursor.execute("SELECT id FROM lesson_comments WHERE id = %s", (comment_id,))
        if not db_cursor.fetchone():
            db_cursor.close()
            db_connection.close()
            return jsonify({'success': False, 'error': 'Comment not found'}), 404
        
        # Create reply
        db_cursor.execute("""
            INSERT INTO lesson_comment_replies (comment_id, user_id, reply_text)
            VALUES (%s, %s, %s)
        """, (comment_id, session['user_id'], reply_text))
        
        reply_id = db_cursor.lastrowid
        db_connection.commit()
        
        # Get the created reply with user info
        db_cursor.execute("""
            SELECT 
                lcr.id,
                lcr.user_id,
                u.username,
                lcr.reply_text,
                lcr.created_at,
                0 AS like_count,
                0 AS user_liked
            FROM lesson_comment_replies lcr
            JOIN users u ON lcr.user_id = u.id
            WHERE lcr.id = %s
        """, (reply_id,))
        
        reply = db_cursor.fetchone()
        
        db_cursor.close()
        db_connection.close()
        
        return jsonify({'success': True, 'reply': reply}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/replies/<int:reply_id>', methods=['DELETE'])
@login_required
def delete_comment_reply(reply_id):
    """Delete a reply (only by reply author or admin)"""
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Get reply
        db_cursor.execute("SELECT user_id FROM lesson_comment_replies WHERE id = %s", (reply_id,))
        reply = db_cursor.fetchone()
        
        if not reply:
            db_cursor.close()
            db_connection.close()
            return jsonify({'success': False, 'error': 'Reply not found'}), 404
        
        # Check authorization
        if reply['user_id'] != session['user_id'] and session.get('role') != 'admin':
            db_cursor.close()
            db_connection.close()
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Delete reply (cascades to likes)
        db_cursor.execute("DELETE FROM lesson_comment_replies WHERE id = %s", (reply_id,))
        db_connection.commit()
        
        db_cursor.close()
        db_connection.close()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/comments/<int:comment_id>/like', methods=['POST'])
@login_required
def like_comment(comment_id):
    """Like/unlike a comment"""
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Verify comment exists
        db_cursor.execute("SELECT id FROM lesson_comments WHERE id = %s", (comment_id,))
        if not db_cursor.fetchone():
            db_cursor.close()
            db_connection.close()
            return jsonify({'success': False, 'error': 'Comment not found'}), 404
        
        # Check if user already liked this comment
        db_cursor.execute("""
            SELECT id FROM lesson_comment_likes 
            WHERE comment_id = %s AND user_id = %s
        """, (comment_id, session['user_id']))
        
        existing_like = db_cursor.fetchone()
        
        if existing_like:
            # Unlike
            db_cursor.execute("""
                DELETE FROM lesson_comment_likes 
                WHERE comment_id = %s AND user_id = %s
            """, (comment_id, session['user_id']))
            liked = False
        else:
            # Like
            db_cursor.execute("""
                INSERT INTO lesson_comment_likes (comment_id, user_id)
                VALUES (%s, %s)
            """, (comment_id, session['user_id']))
            liked = True
        
        db_connection.commit()
        
        # Get updated like count
        db_cursor.execute("""
            SELECT COUNT(*) as like_count FROM lesson_comment_likes 
            WHERE comment_id = %s
        """, (comment_id,))
        
        result = db_cursor.fetchone()
        like_count = result['like_count'] if result else 0
        
        db_cursor.close()
        db_connection.close()
        
        return jsonify({'success': True, 'liked': liked, 'like_count': like_count}), 200
    except Exception as e:
        print(f"[ERROR] like_comment failed: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db_connection' in locals():
            try:
                db_connection.rollback()
                db_connection.close()
            except Exception:
                pass
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/replies/<int:reply_id>/like', methods=['POST'])
@login_required
def like_reply(reply_id):
    """Like/unlike a reply"""
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Verify reply exists
        db_cursor.execute("SELECT id FROM lesson_comment_replies WHERE id = %s", (reply_id,))
        if not db_cursor.fetchone():
            db_cursor.close()
            db_connection.close()
            return jsonify({'success': False, 'error': 'Reply not found'}), 404
        
        # Check if user already liked this reply
        db_cursor.execute("""
            SELECT id FROM lesson_reply_likes 
            WHERE reply_id = %s AND user_id = %s
        """, (reply_id, session['user_id']))
        
        existing_like = db_cursor.fetchone()
        
        if existing_like:
            # Unlike
            db_cursor.execute("""
                DELETE FROM lesson_reply_likes 
                WHERE reply_id = %s AND user_id = %s
            """, (reply_id, session['user_id']))
            liked = False
        else:
            # Like
            db_cursor.execute("""
                INSERT INTO lesson_reply_likes (reply_id, user_id)
                VALUES (%s, %s)
            """, (reply_id, session['user_id']))
            liked = True
        
        db_connection.commit()
        
        # Get updated like count
        db_cursor.execute("""
            SELECT COUNT(*) as like_count FROM lesson_reply_likes 
            WHERE reply_id = %s
        """, (reply_id,))
        
        result = db_cursor.fetchone()
        like_count = result['like_count'] if result else 0
        
        db_cursor.close()
        db_connection.close()
        
        return jsonify({'success': True, 'liked': liked, 'like_count': like_count}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============== END LESSON COMMENTS API ROUTES ==============

# Update the startChapter function in chapter_list.html
@app.route('/user/classic/<level>/<int:chapter_id>/start')
@login_required
def start_chapter(level, chapter_id):
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor()
        # Insert user_progress if not exists
        upsert_query = """
        INSERT INTO user_progress (user_id, chapter_id, progress, completed)
        VALUES (%s, %s, 0, 0)
        ON DUPLICATE KEY UPDATE progress = progress
        """
        db_cursor.execute(upsert_query, (session['user_id'], chapter_id))
        db_connection.commit()
    except Exception as e:
        print("Database error (start_chapter):", str(e))
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()
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
@login_required
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    return render_template('admin/dashboard.html')

@app.route('/admin/users')
@login_required
def admin_users():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Fetch all users with their basic info and stats
        db_cursor.execute("""
            SELECT 
                u.id, 
                u.username, 
                u.email, 
                u.created_at,
                u.role,
                u.avatar_path,
                COALESCE(us.xp, 0) as xp,
                COALESCE(us.level, 1) as level,
                COALESCE(us.points, 0) as points,
                COALESCE(us.rating, 1200) as rating,
                COALESCE(l.total_score, 0) as leaderboard_score
            FROM users u
            LEFT JOIN user_stats us ON u.id = us.user_id
            LEFT JOIN leaderboards l ON u.id = l.user_id
            ORDER BY u.created_at DESC
        """)
        users = db_cursor.fetchall()
        
        # Determine active/inactive status based on recent activity
        for user in users:
            db_cursor.execute("""
                SELECT MAX(last_visited) as last_active
                FROM lesson_page_analytics
                WHERE user_id = %s
            """, (user['id'],))
            activity = db_cursor.fetchone()
            
            if activity and activity['last_active']:
                last_active = activity['last_active']
                if last_active.tzinfo is not None:
                    last_active = last_active.replace(tzinfo=None)
                days_inactive = (datetime.utcnow() - last_active).days
                user['status'] = 'Active' if days_inactive < 7 else 'Inactive'
                user['last_active'] = last_active
            else:
                user['status'] = 'Inactive'
                user['last_active'] = None
        
        return render_template('admin/users.html', users=users)
    except Exception as e:
        print(f"Error in admin_users: {str(e)}")
        return render_template('admin/users.html', users=[])
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/admin/users/<int:user_id>')
@login_required
def admin_user_details(user_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Fetch user info
        db_cursor.execute("""
            SELECT id, username, email, avatar_path, google_id, created_at, role
            FROM users WHERE id = %s
        """, (user_id,))
        user = db_cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Fetch user badges
        db_cursor.execute('''
            SELECT b.id, b.name, b.description, b.icon, ub.earned_at
            FROM user_badges ub
            JOIN badges b ON ub.badge_id = b.id
            WHERE ub.user_id = %s
            ORDER BY ub.earned_at DESC
        ''', (user_id,))
        badges = db_cursor.fetchall()
        
        # Learning progress metrics
        db_cursor.execute("SELECT COUNT(*) AS total FROM chapters")
        total_chapters = int((db_cursor.fetchone() or {}).get('total') or 0)
        
        db_cursor.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END), 0) AS completed,
                COALESCE(SUM(CASE WHEN completed = 0 AND progress > 0 THEN 1 ELSE 0 END), 0) AS in_progress,
                COALESCE(SUM(progress), 0) AS total_progress
            FROM user_progress
            WHERE user_id = %s
        """, (user_id,))
        progress_row = db_cursor.fetchone() or {}
        
        completed_chapters = int(progress_row.get('completed') or 0)
        in_progress_chapters = int(progress_row.get('in_progress') or 0)
        progress_sum = float(progress_row.get('total_progress') or 0.0)
        overall_percent = min(progress_sum / total_chapters, 100.0) if total_chapters else 0.0
        
        # Engagement metrics
        db_cursor.execute("""
            SELECT
                COALESCE(SUM(time_spent), 0) AS total_time,
                COALESCE(COUNT(DISTINCT DATE(last_visited)), 0) AS active_days,
                COALESCE(COUNT(DISTINCT chapter_id), 0) AS chapters_visited,
                MAX(last_visited) AS last_visited
            FROM lesson_page_analytics
            WHERE user_id = %s
        """, (user_id,))
        engagement_row = db_cursor.fetchone() or {}
        
        total_time_spent = int(float(engagement_row.get('total_time') or 0))
        active_days = int(engagement_row.get('active_days') or 0)
        chapters_visited = int(engagement_row.get('chapters_visited') or 0)
        last_active_dt = engagement_row.get('last_visited')
        avg_daily_seconds = total_time_spent // active_days if active_days else 0
        
        # Score metrics
        db_cursor.execute("""
            SELECT xp, level, points, rating FROM user_stats WHERE user_id = %s
        """, (user_id,))
        stats_row = db_cursor.fetchone()
        
        xp = int((stats_row.get('xp') or 0) if stats_row else 0)
        level = int((stats_row.get('level') or 1) if stats_row else 1)
        points = int((stats_row.get('points') or 0) if stats_row else 0)
        rating = int((stats_row.get('rating') or 1200) if stats_row else 1200)
        
        # Fetch user rank
        db_cursor.execute('''
            SELECT user_id, total_score FROM leaderboards ORDER BY total_score DESC
        ''')
        leaderboard = db_cursor.fetchall()
        user_rank = None
        for idx, entry in enumerate(leaderboard, 1):
            if entry['user_id'] == user_id:
                user_rank = idx
                break
        
        print(f"DEBUG: User {user_id} rank: {user_rank}")
        print(f"DEBUG: User rank type: {type(user_rank)}")
        
        # Format data for response
        response_data = {
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'avatar_path': user['avatar_path'],
                'created_at': user['created_at'].strftime('%b %d, %Y') if user['created_at'] else '',
                'role': user['role']
            },
            'badges': [{
                'name': b['name'],
                'description': b['description'],
                'icon': b['icon'],
                'earned_at': b['earned_at'].strftime('%b %d, %Y') if b['earned_at'] else ''
            } for b in badges],
            'progress': {
                'completed_chapters': completed_chapters,
                'in_progress_chapters': in_progress_chapters,
                'total_chapters': total_chapters,
                'overall_percent': round(overall_percent, 1),
                'bar_width': max(0, min(int(round(overall_percent)), 100))
            },
            'engagement': {
                'total_time_label': _format_duration_short(total_time_spent),
                'active_days': active_days,
                'avg_daily_label': _format_duration_short(avg_daily_seconds),
                'chapters_visited': chapters_visited,
                'last_active_label': last_active_dt.strftime('%b %d, %Y %I:%M %p') if last_active_dt else 'Never',
                'last_active_relative': _format_relative_time(last_active_dt) if last_active_dt else 'Never'
            },
            'scores': {
                'xp': xp,
                'level': level,
                'points': points,
                'rating': rating,
                'rank': user_rank or 'Unranked'
            }
        }
        
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in admin_user_details: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/admin/levels')
@login_required
def admin_levels():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Fetch all levels with their chapter counts
        query = """
            SELECT l.*, COUNT(c.id) as chapter_count 
            FROM levels l 
            LEFT JOIN chapters c ON l.id = c.level_id 
            GROUP BY l.id
        """
        db_cursor.execute(query)
        levels = db_cursor.fetchall()
        
        return render_template('admin/levels.html', levels=levels)
    except Exception as e:
        print("Database error:", str(e))
        return render_template('admin/levels.html', levels=[])
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/admin/levels/add', methods=['POST'])
@login_required
def add_level():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        title = request.form.get('title')
        description = request.form.get('description')
        image_url = None
        # Handle image upload
        if 'image_url' in request.files:
            image_file = request.files['image_url']
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                # Save to static/images
                image_path = os.path.join('static', 'images', filename)
                image_file.save(image_path)
                image_url = f'/static/images/{filename}'
        
        if not title or not description:
            return jsonify({'success': False, 'message': 'Title and description are required'})
        
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor()
        
        query = "INSERT INTO levels (title, description, image_url) VALUES (%s, %s, %s)"
        db_cursor.execute(query, (title, description, image_url))
        db_connection.commit()
        
        return jsonify({'success': True, 'message': 'Level added successfully'})
    except Exception as e:
        print("Database error:", str(e))
        if 'db_connection' in locals():
            db_connection.rollback()
        return jsonify({'success': False, 'message': 'Failed to add level'})
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/admin/levels/<int:level_id>/edit')
@login_required
def get_level_for_edit(level_id):
    print(f"=== BACKEND: get_level_for_edit called with level_id={level_id} ===")
    print(f"Session data: user_id={session.get('user_id')}, role={session.get('role')}")
    
    if session.get('role') != 'admin':
        print("❌ Unauthorized access attempt")
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        print("📊 Connecting to database...")
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        query = "SELECT id, title, description, image_url FROM levels WHERE id = %s"
        print(f"🔍 Executing query: {query} with level_id={level_id}")
        db_cursor.execute(query, (level_id,))
        level = db_cursor.fetchone()
        
        print(f"📋 Query result: {level}")
        
        if level:
            print(f"✅ Returning level data: {level}")
            return jsonify(level)
        else:
            print("❌ Level not found in database")
            return jsonify({'success': False, 'message': 'Level not found'}), 404
    except Exception as e:
        print(f"💥 Database error in get_level_for_edit: {str(e)}")
        print(f"💥 Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Failed to fetch level'}), 500
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()
        print("=== BACKEND: get_level_for_edit completed ===")

@app.route('/admin/levels/<int:level_id>', methods=['PUT'])
@login_required
def update_level(level_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        title = request.form.get('title')
        description = request.form.get('description')
        
        if not title or not description:
            return jsonify({'success': False, 'message': 'Title and description are required'})
        
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Get current level data
        db_cursor.execute("SELECT image_url FROM levels WHERE id = %s", (level_id,))
        current_level = db_cursor.fetchone()
        
        if not current_level:
            return jsonify({'success': False, 'message': 'Level not found'}), 404
        
        image_url = current_level['image_url']
        
        # Handle image upload (if new image provided)
        if 'image_url' in request.files:
            image_file = request.files['image_url']
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                # Save to static/images
                image_path = os.path.join('static', 'images', filename)
                image_file.save(image_path)
                image_url = f'/static/images/{filename}'
        
        # Update level
        query = "UPDATE levels SET title = %s, description = %s, image_url = %s WHERE id = %s"
        db_cursor.execute(query, (title, description, image_url, level_id))
        db_connection.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Level updated successfully',
            'level': {
                'id': level_id,
                'title': title,
                'description': description,
                'image_url': image_url
            }
        })
    except Exception as e:
        print("Database error:", str(e))
        if 'db_connection' in locals():
            db_connection.rollback()
        return jsonify({'success': False, 'message': 'Failed to update level'}), 500
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/admin/levels/<int:level_id>', methods=['DELETE'])
@login_required
def delete_level(level_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor()
        
        # Delete the level (chapters will be automatically deleted due to CASCADE)
        query = "DELETE FROM levels WHERE id = %s"
        db_cursor.execute(query, (level_id,))
        db_connection.commit()
        
        return jsonify({'success': True, 'message': 'Level deleted successfully'})
    except Exception as e:
        print("Database error:", str(e))
        if 'db_connection' in locals():
            db_connection.rollback()
        return jsonify({'success': False, 'message': 'Failed to delete level'})
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/admin/chapters/<int:level_id>')
@login_required
def get_chapters(level_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        query = "SELECT * FROM chapters WHERE level_id = %s ORDER BY order_num"
        db_cursor.execute(query, (level_id,))
        chapters = db_cursor.fetchall()
        
        return jsonify(chapters)
    except Exception as e:
        print("Database error:", str(e))
        return jsonify([])
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/admin/chapters/add', methods=['POST'])
@login_required
def add_chapter():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        level_id = request.form.get('level_id')
        name = request.form.get('name')
        title = request.form.get('title')
        description = request.form.get('description')
        xp_reward = request.form.get('xp_reward')
        points_reward = request.form.get('points_reward')
        order_num = request.form.get('order_num')
        
        if not all([level_id, name, title, description, xp_reward, points_reward, order_num]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor()
        
        query = """
            INSERT INTO chapters (level_id, name, title, description, xp_reward, points_reward, order_num)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        db_cursor.execute(query, (level_id, name, title, description, xp_reward, points_reward, order_num))
        db_connection.commit()
        
        return jsonify({'success': True, 'message': 'Chapter added successfully'})
    except Exception as e:
        print("Database error:", str(e))
        if 'db_connection' in locals():
            db_connection.rollback()
        return jsonify({'success': False, 'message': 'Failed to add chapter'})
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/admin/chapters/<int:chapter_id>', methods=['DELETE'])
@login_required
def delete_chapter(chapter_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor()
        
        query = "DELETE FROM chapters WHERE id = %s"
        db_cursor.execute(query, (chapter_id,))
        db_connection.commit()
        
        return jsonify({'success': True, 'message': 'Chapter deleted successfully'})
    except Exception as e:
        print("Database error:", str(e))
        if 'db_connection' in locals():
            db_connection.rollback()
        return jsonify({'success': False, 'message': 'Failed to delete chapter'})
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/admin/chapters/<int:chapter_id>/edit')
@login_required
def get_chapter_for_edit(chapter_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        query = "SELECT * FROM chapters WHERE id = %s"
        db_cursor.execute(query, (chapter_id,))
        chapter = db_cursor.fetchone()
        
        if not chapter:
            return jsonify({'success': False, 'message': 'Chapter not found'}), 404
        
        return jsonify(chapter)
    except Exception as e:
        print("Database error:", str(e))
        return jsonify({'success': False, 'message': 'Failed to fetch chapter details'}), 500
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/admin/chapters/<int:chapter_id>', methods=['PUT'])
@login_required
def update_chapter(chapter_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        name = request.form.get('name')
        title = request.form.get('title')
        description = request.form.get('description')
        xp_reward = request.form.get('xp_reward')
        points_reward = request.form.get('points_reward')
        order_num = request.form.get('order_num')
        
        if not all([name, title, description, xp_reward, points_reward, order_num]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor()
        
        query = """
            UPDATE chapters 
            SET name = %s, title = %s, description = %s, 
                xp_reward = %s, points_reward = %s, order_num = %s
            WHERE id = %s
        """
        db_cursor.execute(query, (name, title, description, xp_reward, points_reward, order_num, chapter_id))
        db_connection.commit()
        
        return jsonify({'success': True, 'message': 'Chapter updated successfully'})
    except Exception as e:
        print("Database error:", str(e))
        if 'db_connection' in locals():
            db_connection.rollback()
        return jsonify({'success': False, 'message': 'Failed to update chapter'})
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/admin/rankings')
@login_required
def admin_rankings():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    return render_template('admin/rankings.html')

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
    code_queue[:] = [(sid, uid, rating) for sid, uid, rating in code_queue if sid != request.sid]
    quiz_queue[:] = [(sid, uid, rating) for sid, uid, rating in quiz_queue if sid != request.sid]
    # Handle disconnection from active matches
    for match_id, info in list(active_matches.items()):
        players = info.get('players', [])
        if request.sid in players:
            players = [p for p in players if p != request.sid]
            remaining_user = players[0] if players else None
            if not players:
                _finalize_match(match_id)
            else:
                info['players'] = players
                emit('opponent_disconnected', room=match_id)
                winner_id = socket_to_user.get(remaining_user) if remaining_user else None
                winner_name = get_username_by_user_id(winner_id) if winner_id else 'Draw'
                emit('match_end', {'winner': winner_name}, room=match_id)
                _finalize_match(match_id)

def get_username_by_user_id(user_id):
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        query = "SELECT username, avatar_path FROM users WHERE id = %s"
        db_cursor.execute(query, (user_id,))
        result = db_cursor.fetchone()
        return result if result else {'username': f'Player{user_id}', 'avatar_path': None}
    except Exception as e:
        print("Database error:", str(e))
        return {'username': f'Player{user_id}', 'avatar_path': None}
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
    user_rating = get_user_rating(user_id)
    
    if mode == 'code':
        code_queue[:] = [(sid, uid, rating) for sid, uid, rating in code_queue if sid != socket_id]
        opponent = _pop_best_match(code_queue, user_rating)
        if opponent:
            opponent_socket, opponent_user_id, opponent_rating = opponent
            room = f'match_{socket_id}_{opponent_socket}'
            active_matches[room] = { 'players': [socket_id, opponent_socket], 'mode': 'code' }

            join_room(room, socket_id)
            join_room(room, opponent_socket)

            opponent_username = get_username_by_user_id(opponent_user_id)
            current_username = get_username_by_user_id(user_id)

            emit('match_found', {
                'opponent': {
                    'name': opponent_username,
                    'rating': opponent_rating
                }
            }, room=socket_id)

            emit('match_found', {
                'opponent': {
                    'name': current_username,
                    'rating': user_rating
                }
            }, room=opponent_socket)
        else:
            code_queue.append((socket_id, user_id, user_rating))
            emit('queue_status', {'status': 'waiting', 'rating': user_rating})
    
    elif mode == 'quiz':
        quiz_queue[:] = [(sid, uid, rating) for sid, uid, rating in quiz_queue if sid != socket_id]
        opponent = _pop_best_match(quiz_queue, user_rating)
        if opponent:
            opponent_socket, opponent_user_id, opponent_rating = opponent
            room = f'match_{socket_id}_{opponent_socket}'
            active_matches[room] = { 'players': [socket_id, opponent_socket], 'mode': 'quiz' }

            join_room(room, socket_id)
            join_room(room, opponent_socket)

            opponent_user = get_username_by_user_id(opponent_user_id)
            current_user = get_username_by_user_id(user_id)

            emit('match_found', {
                'opponent': {
                    'name': opponent_user.get('username', 'Opponent'),
                    'rating': opponent_rating,
                    'avatar': opponent_user.get('avatar_path')
                },
                'you': {
                    'name': current_user.get('username', 'You'),
                    'avatar': current_user.get('avatar_path')
                }
            }, room=socket_id)

            emit('match_found', {
                'opponent': {
                    'name': current_user.get('username', 'Opponent'),
                    'rating': user_rating,
                    'avatar': current_user.get('avatar_path')
                },
                'you': {
                    'name': opponent_user.get('username', 'You'),
                    'avatar': opponent_user.get('avatar_path')
                }
            }, room=opponent_socket)
        else:
            quiz_queue.append((socket_id, user_id, user_rating))
            emit('queue_status', {'status': 'waiting', 'rating': user_rating})

@socketio.on('cancel_queue')
def handle_cancel_queue():
    socket_id = request.sid
    # Remove from queues if present
    code_queue[:] = [(sid, uid, rating) for sid, uid, rating in code_queue if sid != socket_id]
    quiz_queue[:] = [(sid, uid, rating) for sid, uid, rating in quiz_queue if sid != socket_id]
    emit('queue_cancelled')

@socketio.on('start_match')
def handle_start_match():
    socket_id = request.sid
    for match_id, info in active_matches.items():
        players = info.get('players', [])
        mode = info.get('mode', 'code')
        if socket_id not in players:
            continue

        if mode == 'code':
            if match_id in code_matches:
                break
            db_challenges = load_all_code_challenges()
            challenge = random.choice(db_challenges) if db_challenges else DEFAULT_CODE_CHALLENGE
            code_matches[match_id] = {
                "challenge": challenge,
                "start_time": time.time(),
                "submissions": {},
                "winner": None
            }
            emit('code_challenge_start', {
                "challenge": {
                    "title": challenge["title"],
                    "description": challenge.get("description", ""),
                    "starter_code": challenge.get("starter_code", ""),
                    "function_name": challenge.get("function_name", ""),
                    "time_limit": challenge.get("time_limit", 300),
                    "language": challenge.get("language", "javascript")
                }
            }, room=match_id)

            break

        elif mode == 'quiz':
            if match_id in quiz_matches:
                break
            questions = load_all_quiz_questions()
            if not questions:
                questions = [DEFAULT_QUIZ_QUESTION] * 5
            # Select 5 random questions for the match
            selected_questions = random.sample(questions, min(5, len(questions)))
            if len(selected_questions) < 5:
                # Pad with more questions if needed
                while len(selected_questions) < 5:
                    selected_questions.append(random.choice(questions) if questions else DEFAULT_QUIZ_QUESTION)
            
            quiz_matches[match_id] = {
                'questions': selected_questions,
                'current_question_index': 0,
                'start_time': time.time(),
                'question_start_time': time.time(),
                'answers': {},
                'answer_times': {},
                'scores': {p: 0 for p in players},
                'total_questions': 5
            }
            
            # Send the first question
            first_question = selected_questions[0]
            emit('quiz_question_start', {
                'question': {
                    'id': first_question.get('id', 0),
                    'question': first_question['question'],
                    'choices': first_question['choices'],
                    'time_limit': first_question.get('time_limit', 20),
                    'explanation': first_question.get('explanation')
                },
                'question_number': 1,
                'total_questions': 5
            }, room=match_id)
            break

@socketio.on('submit_code')
def handle_submit_code(data):
    socket_id = request.sid
    code = data.get('code')
    for match_id, info in active_matches.items():
        players = info.get('players', [])
        if socket_id in players and match_id in code_matches:
            match = code_matches[match_id]
            challenge = match["challenge"]
            # Run code against test cases (JavaScript only)
            results, passed = run_js_code_against_tests(code, challenge)
            match["submissions"][socket_id] = {
                "code": code,
                "results": results,
                "passed": passed,
                "timestamp": time.time()
            }
            # Check for winner
            if passed and not match["winner"]:
                match["winner"] = socket_id
                emit('code_challenge_result', {
                    "results": results,
                    "winner": True
                }, room=socket_id)
                # Notify opponent
                for p in players:
                    if p != socket_id:
                        emit('code_challenge_result', {
                            "results": results,
                            "winner": False
                        }, room=p)
                winner_id = socket_to_user.get(socket_id)
                winner_name = get_username_by_user_id(winner_id) if winner_id else 'Unknown'
                summary = {
                    'overview': f"{winner_name} solved '{challenge['title']}' first.",
                    'details': challenge.get('description', '')
                }
                emit('match_end', {
                    "winner": winner_name,
                    "mode": "code",
                    "summary": summary
                }, room=match_id)
                _finalize_match(match_id)
            else:
                emit('code_challenge_result', {
                    "results": results,
                    "winner": False
                }, room=socket_id)
            break


@socketio.on('submit_quiz_answer')
def handle_submit_quiz_answer(data):
    socket_id = request.sid
    answer_index = int(data.get('answer_index', -1))
    # find match
    for match_id, info in active_matches.items():
        players = info.get('players', [])
        if socket_id in players and match_id in quiz_matches:
            qm = quiz_matches[match_id]
            current_idx = qm['current_question_index']
            question = qm['questions'][current_idx]
            question_start_time = qm.get('question_start_time', time.time())
            
            # Record answer
            qm['answers'][socket_id] = answer_index
            answer_time = time.time()
            qm['answer_times'][socket_id] = answer_time
            
            # Notify opponent that this player has answered
            opponent = [p for p in players if p != socket_id][0]
            emit('player_status', {
                'player': 'opponent',
                'status': 'answered'
            }, room=opponent)
            
            # Wait for both players to answer
            if len(qm['answers']) >= 2:
                correct_index = question.get('correct_index')
                time_limit = question.get('time_limit', 20)
                
                # Calculate scores with speed multiplier
                for p in players:
                    if qm['answers'].get(p) == correct_index:
                        # Calculate time taken (in seconds)
                        time_taken = qm['answer_times'][p] - question_start_time
                        
                        # Speed multiplier system:
                        # 0-5 seconds: 2.0x multiplier (300 points)
                        # 5-10 seconds: 1.5x multiplier (225 points)
                        # 10-15 seconds: 1.25x multiplier (187.5 points)
                        # 15-20 seconds: 1.0x multiplier (150 points)
                        base_points = 150
                        if time_taken <= 5:
                            multiplier = 2.0
                        elif time_taken <= 10:
                            multiplier = 1.5
                        elif time_taken <= 15:
                            multiplier = 1.25
                        else:
                            multiplier = 1.0
                        
                        points_earned = int(base_points * multiplier)
                        qm['scores'][p] += points_earned
                        
                        # Store the points earned for this round
                        if 'round_points' not in qm:
                            qm['round_points'] = {}
                        qm['round_points'][p] = {
                            'points': points_earned,
                            'multiplier': multiplier,
                            'time_taken': time_taken
                        }
                
                # Determine round winner (who answered correctly first)
                round_winner = None
                correct_entries = [
                    (p, qm['answer_times'].get(p, float('inf')))
                    for p in players
                    if qm['answers'].get(p) == correct_index
                ]
                if correct_entries:
                    round_winner = min(correct_entries, key=lambda item: item[1])[0]
                
                correct_choice = None
                if isinstance(question.get('choices'), list) and 0 <= correct_index < len(question['choices']):
                    correct_choice = question['choices'][correct_index]
                
                # Emit results to both players
                for p in players:
                    opponent = [player for player in players if player != p][0]
                    player_round_data = qm.get('round_points', {}).get(p, {'points': 0, 'multiplier': 0, 'time_taken': 0})
                    
                    emit('quiz_result', {
                        'your_answer': qm['answers'].get(p),
                        'opponent_answer': qm['answers'].get(opponent),
                        'correct_index': correct_index,
                        'correct_choice': correct_choice,
                        'explanation': question.get('explanation'),
                        'round_winner': (p == round_winner),
                        'your_score': qm['scores'][p],
                        'opponent_score': qm['scores'][opponent],
                        'opponent_correct': (qm['answers'].get(opponent) == correct_index),
                        'points_earned': player_round_data['points'],
                        'multiplier': player_round_data['multiplier'],
                        'time_taken': round(player_round_data['time_taken'], 2)
                    }, room=p)
                
                # Move to next question or end match
                qm['current_question_index'] += 1
                qm['answers'] = {}
                qm['answer_times'] = {}
                qm['round_points'] = {}
                
                if qm['current_question_index'] < qm['total_questions']:
                    # Send next question after a delay
                    def send_next_question():
                        if match_id in quiz_matches:
                            next_idx = quiz_matches[match_id]['current_question_index']
                            next_question = quiz_matches[match_id]['questions'][next_idx]
                            quiz_matches[match_id]['question_start_time'] = time.time()
                            emit('quiz_question_start', {
                                'question': {
                                    'id': next_question.get('id', 0),
                                    'question': next_question['question'],
                                    'choices': next_question['choices'],
                                    'time_limit': next_question.get('time_limit', 20),
                                    'explanation': next_question.get('explanation')
                                },
                                'question_number': next_idx + 1,
                                'total_questions': qm['total_questions']
                            }, room=match_id)
                    
                    socketio.sleep(3)  # 3 second delay before next question
                    send_next_question()
                else:
                    # Match ended - determine final winner
                    scores_list = [(p, qm['scores'][p]) for p in players]
                    scores_list.sort(key=lambda x: x[1], reverse=True)
                    
                    if scores_list[0][1] > scores_list[1][1]:
                        winner_socket = scores_list[0][0]
                        winner_id = socket_to_user.get(winner_socket)
                        winner_user = get_username_by_user_id(winner_id) if winner_id else None
                        winner_name = winner_user.get('username', 'Unknown') if winner_user else 'Unknown'
                    else:
                        winner_name = 'Draw'
                    
                    summary = {
                        'overview': f"Final Score: {scores_list[0][1]} - {scores_list[1][1]}",
                        'details': f"{winner_name} wins!" if winner_name != 'Draw' else "It's a tie!"
                    }
                    
                    emit('match_end', {
                        'winner': winner_name,
                        'mode': 'quiz',
                        'summary': summary,
                        'final_scores': {p: qm['scores'][p] for p in players}
                    }, room=match_id)
                    
                    _finalize_match(match_id)
            break

@socketio.on('surrender')
def handle_surrender(data):
    """Handle player surrendering/leaving the battle"""
    user_id = session.get('user_id')
    if not user_id:
        return
    
    sid = request.sid
    
    # Find the match this player is in
    match_id = None
    for room_id, info in active_matches.items():
        if sid in info.get('players', []):
            match_id = room_id
            break
    
    if match_id:
        # Get match data
        match_info = active_matches.get(match_id, {})
        mode = match_info.get('mode', 'quiz')
        qm = quiz_matches.get(match_id) if mode == 'quiz' else None
        cm = code_matches.get(match_id) if mode == 'code' else None
        match_data = qm or cm
        
        if match_info and 'players' in match_info:
            players = match_info['players']
            opponent = [p for p in players if p != sid]
            
            if opponent:
                opponent_sid = opponent[0]
                opponent_id = socket_to_user.get(opponent_sid)
                opponent_user = get_username_by_user_id(opponent_id) if opponent_id else None
                opponent_name = opponent_user.get('username', 'Opponent') if opponent_user else 'Opponent'
                
                # Notify opponent that player has left
                emit('player_status', {
                    'player': 'opponent',
                    'status': 'left'
                }, room=opponent_sid)
                
                # Notify opponent that they won
                emit('match_end', {
                    'winner': opponent_name,
                    'mode': mode,
                    'summary': {
                        'overview': 'Opponent surrendered',
                        'details': f'{opponent_name} wins by forfeit!'
                    },
                    'surrendered': True
                }, room=match_id)
        
        # Clean up match
        _finalize_match(match_id)
    
    # Also remove from queues if they're waiting
    code_queue[:] = [(s, u, r) for s, u, r in code_queue if s != sid]
    quiz_queue[:] = [(s, u, r) for s, u, r in quiz_queue if s != sid]

def run_js_code_against_tests(code, challenge):
    results = []
    passed_all = True
    for case in challenge["test_cases"]:
        try:
            # Prepare JS code to run
            args = ', '.join(repr(arg) for arg in case['input'])
            test_code = (
                code +
                f"\nconsole.log({challenge['function_name']}({args}));"
            )
            proc = subprocess.run(
                ["node", "-e", test_code],
                capture_output=True, text=True, timeout=2
            )
            output = proc.stdout.strip()
            expected = str(case["output"])
            passed = (output == expected)
            results.append({"input": case["input"], "expected": expected, "output": output, "passed": passed})
            if not passed:
                passed_all = False
        except Exception as e:
            results.append({"input": case["input"], "expected": str(case["output"]), "output": str(e), "passed": False})
            passed_all = False
    return results, passed_all

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

        # Ensure fast lookups for chapters by level and order
        try:
            db_cursor.execute("CREATE INDEX idx_chapters_level_order ON chapters(level_id, order_num)")
            db_connection.commit()
        except Exception:
            pass
        
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

        # Improve lesson_content page retrieval performance
        try:
            db_cursor.execute("CREATE INDEX idx_lesson_content_chapter_page ON lesson_content(chapter_id, page_num)")
            db_connection.commit()
        except Exception:
            pass

        # Add page_type to lesson_content table if it doesn't exist
        try:
            db_cursor.execute("ALTER TABLE lesson_content ADD COLUMN page_type ENUM('text_image', 'text_code', 'quiz', 'playground') DEFAULT 'text_image'")
            db_connection.commit()
        except Exception as e:
            print("Page type column might already exist:", str(e))
            # Try to modify the existing ENUM if it exists but has wrong values
            try:
                db_cursor.execute("ALTER TABLE lesson_content MODIFY COLUMN page_type ENUM('text_image', 'text_code', 'quiz', 'playground') DEFAULT 'text_image'")
                db_connection.commit()
                print("Updated page_type ENUM values")
            except Exception as e2:
                print("Could not update page_type ENUM:", str(e2))

        # Create lesson_choices table for multiple choice questions
        create_lesson_choices_table = """
        CREATE TABLE IF NOT EXISTS lesson_choices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lesson_content_id INT NOT NULL,
            choice_text TEXT NOT NULL,
            is_correct BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (lesson_content_id) REFERENCES lesson_content(id) ON DELETE CASCADE
        )
        """
        db_cursor.execute(create_lesson_choices_table)
        db_connection.commit()

        try:
            db_cursor.execute("CREATE INDEX idx_lesson_choices_content ON lesson_choices(lesson_content_id)")
            db_connection.commit()
        except Exception:
            pass

        # Create PvP-specific tables for configurable challenges
        try:
            db_cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pvp_code_challenges (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    function_name VARCHAR(255),
                    starter_code TEXT,
                    language VARCHAR(50) DEFAULT 'javascript',
                    time_limit INT DEFAULT 300,
                    test_cases JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            db_connection.commit()
        except Exception:
            pass

        try:
            db_cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pvp_quiz_questions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question TEXT NOT NULL,
                    choices JSON NOT NULL,
                    correct_index INT NOT NULL,
                    time_limit INT DEFAULT 45,
                    explanation TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            db_connection.commit()
        except Exception:
            pass
        
    except Exception as e:
        print("Error initializing tables:", str(e))
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

# --- Startup diagnostics for DB config (safe: no secrets) ---
def _log_db_startup_info():
    try:
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "3306")
        ssl_ca = os.getenv("DB_SSL_CA")
        ssl_disabled_env = os.getenv("DB_SSL_DISABLED", "0").strip()
        print(f"DB startup config → host={db_host}, port={db_port}, ssl_ca_set={'yes' if ssl_ca else 'no'}, ssl_disabled={ssl_disabled_env}")
        # Try a quick connection ping
        try:
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute("SELECT 1")
                cur.fetchone()
                print("DB connectivity check: OK")
            finally:
                try:
                    cur.close()
                except Exception:
                    pass
                conn.close()
        except Exception as e:
            print(f"DB connectivity check failed: {e}")
    except Exception as e:
        print(f"DB startup info error: {e}")


# --- PvP challenge helpers ---
def load_all_code_challenges():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM pvp_code_challenges ORDER BY id DESC")
        rows = cur.fetchall() or []
        challenges = []
        for r in rows:
            try:
                test_cases = json.loads(r.get('test_cases') or '[]')
            except Exception:
                test_cases = []
            challenges.append({
                'id': r['id'],
                'title': r['title'],
                'description': r['description'],
                'function_name': r['function_name'],
                'starter_code': r['starter_code'],
                'language': r['language'] or 'javascript',
                'time_limit': r.get('time_limit') or 300,
                'test_cases': test_cases,
            })
        return challenges
    except Exception as e:
        print('load_all_code_challenges error:', str(e))
        return []
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def load_all_quiz_questions():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM pvp_quiz_questions ORDER BY difficulty, id DESC")
        rows = cur.fetchall() or []
        questions = []
        for r in rows:
            try:
                choices = json.loads(r.get('choices') or '[]')
            except Exception:
                choices = []
            questions.append({
                'id': r['id'],
                'question': r['question'],
                'difficulty': r.get('difficulty', 'normal'),
                'choices': choices,
                'correct_index': int(r['correct_index']),
                'time_limit': int(r.get('time_limit') or 45),
                'explanation': r.get('explanation')
            })
        return questions
    except Exception as e:
        print('load_all_quiz_questions error:', str(e))
        return []
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass
            pass


# Admin pages for PvP management
@app.route('/admin/pvp')
@login_required
def admin_pvp():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    quiz_questions = load_all_quiz_questions()
    return render_template('admin/pvp.html', quiz_questions=quiz_questions)


@app.route('/admin/pvp/code/add', methods=['POST'])
@login_required
def admin_add_code_challenge():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    function_name = request.form.get('function_name', '').strip()
    starter_code = request.form.get('starter_code', '').strip()
    language = request.form.get('language') or 'javascript'
    time_limit = int(request.form.get('time_limit') or 300)
    
    if not title or not function_name:
        return jsonify({'success': False, 'message': 'Title and function name are required'}), 400
    
    # Build test cases from form inputs
    test_cases = []
    i = 0
    while f'test_input_{i}' in request.form and f'test_output_{i}' in request.form:
        test_input = request.form.get(f'test_input_{i}', '').strip()
        test_output = request.form.get(f'test_output_{i}', '').strip()
        
        if test_input and test_output:
            # Parse input as comma-separated values for function arguments
            try:
                # Split and parse input values
                input_parts = [part.strip() for part in test_input.split(',')]
                parsed_input = []
                for part in input_parts:
                    try:
                        # Try to parse as number first
                        if '.' in part:
                            parsed_input.append(float(part))
                        else:
                            parsed_input.append(int(part))
                    except ValueError:
                        # If not a number, treat as string (remove quotes if present)
                        if part.startswith('"') and part.endswith('"'):
                            parsed_input.append(part[1:-1])
                        elif part.startswith("'") and part.endswith("'"):
                            parsed_input.append(part[1:-1])
                        else:
                            parsed_input.append(part)
                
                test_cases.append({
                    "input": parsed_input,
                    "output": test_output
                })
            except Exception:
                # If parsing fails, use raw values
                test_cases.append({
                    "input": [test_input],
                    "output": test_output
                })
        i += 1
    
    if not test_cases:
        return jsonify({'success': False, 'message': 'At least one test case is required'}), 400
    
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO pvp_code_challenges (title, description, function_name, starter_code, language, time_limit, test_cases) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (title, description, function_name, starter_code, language, time_limit, json.dumps(test_cases))
        )
        conn.commit()
        return redirect(url_for('admin_pvp'))
    except Exception as e:
        print('admin_add_code_challenge error:', str(e))
        return jsonify({'success': False, 'message': 'DB error'}), 500
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@app.route('/admin/pvp/quiz/add', methods=['POST'])
@login_required
def admin_add_quiz_question():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    question = request.form.get('question', '').strip()
    difficulty = request.form.get('difficulty', 'normal').strip()
    correct_choice_index = int(request.form.get('correct_choice') or 0)
    time_limit = int(request.form.get('time_limit') or 45)
    explanation = request.form.get('explanation', '').strip()
    
    if not question:
        return jsonify({'success': False, 'message': 'Question text is required'}), 400
    
    # Validate difficulty
    if difficulty not in ['easy', 'normal', 'intermediate', 'hard']:
        difficulty = 'normal'
    
    # Build choices from form inputs
    choices = []
    i = 0
    while f'choice_{i}' in request.form:
        choice_text = request.form.get(f'choice_{i}', '').strip()
        if choice_text:
            choices.append(choice_text)
        i += 1
    
    if len(choices) < 2:
        return jsonify({'success': False, 'message': 'At least 2 choices are required'}), 400
    
    if correct_choice_index >= len(choices):
        return jsonify({'success': False, 'message': 'Invalid correct choice index'}), 400
    
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO pvp_quiz_questions (question, difficulty, choices, correct_index, time_limit, explanation) VALUES (%s,%s,%s,%s,%s,%s)",
            (question, difficulty, json.dumps(choices), correct_choice_index, time_limit, explanation)
        )
        conn.commit()
        return redirect(url_for('admin_pvp'))
    except Exception as e:
        print('admin_add_quiz_question error:', str(e))
        return jsonify({'success': False, 'message': 'DB error'}), 500
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@app.route('/admin/pvp/quiz/<int:question_id>', methods=['PUT'])
@login_required
def admin_update_quiz_question(question_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        difficulty = data.get('difficulty', 'normal').strip()
        time_limit = int(data.get('time_limit', 45))
        choices = data.get('choices', [])
        correct_index = int(data.get('correct_index', 0))
        explanation = data.get('explanation', '').strip()
        
        if not question:
            return jsonify({'success': False, 'error': 'Question text is required'}), 400
        
        # Validate difficulty
        if difficulty not in ['easy', 'normal', 'intermediate', 'hard']:
            difficulty = 'normal'
        
        if len(choices) < 2:
            return jsonify({'success': False, 'error': 'At least 2 choices are required'}), 400
        
        if correct_index >= len(choices):
            return jsonify({'success': False, 'error': 'Invalid correct choice index'}), 400
        
        conn = None
        cur = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE pvp_quiz_questions SET question=%s, difficulty=%s, choices=%s, correct_index=%s, time_limit=%s, explanation=%s WHERE id=%s",
                (question, difficulty, json.dumps(choices), correct_index, time_limit, explanation, question_id)
            )
            conn.commit()
            return jsonify({'success': True, 'message': 'Question updated successfully'})
        except Exception as e:
            print('admin_update_quiz_question error:', str(e))
            return jsonify({'success': False, 'error': 'Database error'}), 500
        finally:
            try:
                if cur:
                    cur.close()
            except Exception:
                pass
            try:
                if conn:
                    conn.close()
            except Exception:
                pass
    except Exception as e:
        print('admin_update_quiz_question error:', str(e))
        return jsonify({'success': False, 'error': 'Invalid request'}), 400

# Call this when the app starts
_log_db_startup_info()
init_chapters_table()
init_google_auth_columns()
recalculate_all_user_ratings()

@app.route('/api/analyze-code', methods=['POST'])
def analyze_code():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        code = data.get('message')
        print("Sending code to Gemini API:", code)  # Debug log

        # Gemini API endpoint and model (per official docs)
        api_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return jsonify({'error': 'Gemini API key not set'}), 500

        # Prompt Gemini to analyze code for errors
        prompt = f"Analyze the following code for potential errors and provide suggestions or corrections. Double check before saying NO ISSUES FOUND IN THE CODE, even missing/wrong semicolons, parenthesis, etc. \n\nCode:\n{code}"
        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }
        print("[Gemini DEBUG] Prompt sent to Gemini:", prompt)
        print("[Gemini DEBUG] Payload sent to Gemini:", payload)

        response = requests.post(
            api_url,
            headers={
                'Content-Type': 'application/json',
                'X-goog-api-key': api_key
            },
            json=payload,
            timeout=30
        )

        print("Gemini API Response Status:", response.status_code)  # Debug log
        print("Gemini API Response:", response.text)  # Debug log

        if response.status_code != 200:
            return jsonify({
                'error': f'Gemini API returned status {response.status_code}',
                'details': response.text
            }), 500

        try:
            response_data = response.json()
            # Extract the text response from Gemini
            gemini_text = response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            return jsonify({'result': gemini_text, 'raw': response_data})
        except Exception as e:
            print("Gemini JSON parsing error:", str(e))
            return jsonify({
                'error': 'Invalid JSON response from Gemini API',
                'details': response.text
            }), 500

    except requests.exceptions.RequestException as e:
        print("Request error:", str(e))
        return jsonify({
            'error': 'Failed to connect to Gemini API',
            'details': str(e)
        }), 500
    except Exception as e:
        print("Unexpected error:", str(e))
        return jsonify({
            'error': 'An unexpected error occurred',
            'details': str(e)
        }), 500
        
@app.route("/proxy/4o")
def proxy_4o():
    try:
        message = request.args.get("message")
        if not message:
            return jsonify({"error": "No message provided"}), 400

        # Decode base64 message
        try:
            # Add padding if needed
            padding = 4 - (len(message) % 4)
            if padding != 4:
                message += '=' * padding
                
            decoded_message = base64.b64decode(message).decode('utf-8')
        except Exception as e:
            return jsonify({"error": f"Invalid base64 encoding: {str(e)}"}), 400

        # Make request to the API
        response = requests.get(
            f"https://jonell01-ccprojectsapihshs.hf.space/api/chaitext?ask={quote(decoded_message)}"
        )
        
        if response.status_code != 200:
            return jsonify({"error": f"API error: {response.text}"}), response.status_code

        return jsonify({"answer": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/lesson-content/<int:chapter_id>')
@login_required
def get_lesson_content(chapter_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get lesson content for the chapter, ordered by page number
        cursor.execute("""
            SELECT * FROM lesson_content 
            WHERE chapter_id = %s 
            ORDER BY page_num
        """, (chapter_id,))
        
        pages = cursor.fetchall()
        return jsonify(pages)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/lesson-content/<int:page_id>/edit')
@login_required
def get_lesson_content_for_edit(page_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Get lesson content details
        cursor.execute("""
            SELECT * FROM lesson_content 
            WHERE id = %s
        """, (page_id,))
        page = cursor.fetchone()
        if not page:
            return jsonify({"success": False, "message": "Page not found"}), 404
        # If quiz, get choices
        if page.get('page_type') == 'quiz':
            cursor.execute("SELECT id, choice_text, is_correct FROM lesson_choices WHERE lesson_content_id = %s", (page_id,))
            page['choices'] = cursor.fetchall()
        return jsonify(page)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/lesson-content/add', methods=['POST'])
@login_required
def add_lesson_content():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get form data
        chapter_id = request.form.get('chapter_id')
        title = request.form.get('title', '')  # Make title optional
        content = request.form.get('content')
        code_example = request.form.get('code_example')
        next_button_text = request.form.get('next_button_text', 'Next')
        page_type = request.form.get('page_type', 'text_image')  # Default to text_image
        correct_message = request.form.get('correct_message', '')
        incorrect_message = request.form.get('incorrect_message', '')
        notes = request.form.get('notes', '')
        
        if not content:  # Only content is required
            return jsonify({"success": False, "message": "Content is required"}), 400
        
        # Handle image upload
        image_url = None
        if page_type == 'text_image' and 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to filename to make it unique
                filename = f"{int(time.time())}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                image_url = f"/{file_path}"  # Store relative path
        
        # Get the next page number for this chapter
        cursor.execute("""
            SELECT COALESCE(MAX(page_num), 0) + 1 
            FROM lesson_content 
            WHERE chapter_id = %s
        """, (chapter_id,))
        page_num = cursor.fetchone()[0]
        
        # Insert new lesson content
        cursor.execute("""
            INSERT INTO lesson_content 
            (chapter_id, page_num, title, content, code_example, image_url, next_button_text, page_type, correct_message, incorrect_message, notes) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            chapter_id,
            page_num,
            title,
            content,
            code_example,
            image_url,
            next_button_text,
            page_type,
            correct_message,
            incorrect_message,
            notes,
        ))
        lesson_content_id = cursor.lastrowid

        # If quiz, insert choices
        if page_type == 'quiz':
            # Find all choice_text_X fields
            choices = []
            for key in request.form:
                if key.startswith('choice_text_'):
                    idx = key.split('_')[-1]
                    text = request.form.get(key)
                    choices.append((idx, text))
            # Find which is correct
            correct_idx = request.form.get('correct_choice')
            for idx, text in choices:
                is_correct = (str(idx) == str(correct_idx))
                cursor.execute("""
                    INSERT INTO lesson_choices (lesson_content_id, choice_text, is_correct)
                    VALUES (%s, %s, %s)
                """, (lesson_content_id, text, is_correct))

        conn.commit()
        # Create table for pvp code challenges
        db_cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pvp_code_challenges (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                function_name VARCHAR(255),
                starter_code TEXT,
                language VARCHAR(50) DEFAULT 'javascript',
                time_limit INT DEFAULT 300,
                test_cases JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        # Create table for pvp quiz questions
        db_cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pvp_quiz_questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question TEXT NOT NULL,
                choices JSON NOT NULL,
                correct_index INT NOT NULL,
                time_limit INT DEFAULT 45,
                explanation TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        conn.commit()
        return jsonify({"success": True, "message": "Lesson page added successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/lesson-content/<int:page_id>', methods=['PUT'])
@login_required
def update_lesson_content(page_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get form data
        title = request.form.get('title', '')  # Make title optional
        content = request.form.get('content')
        code_example = request.form.get('code_example')
        next_button_text = request.form.get('next_button_text', 'Next')
        new_page_num = int(request.form.get('page_num', 1))
        page_type = request.form.get('page_type', 'text_image')  # Default to text_image
        correct_message = request.form.get('correct_message', '')
        incorrect_message = request.form.get('incorrect_message', '')
        notes = request.form.get('notes', '')
        if not content:  # Only content is required
            return jsonify({"success": False, "message": "Content is required"}), 400

        # Get current page info
        cursor.execute("""
            SELECT chapter_id, page_num, image_url 
            FROM lesson_content 
            WHERE id = %s
        """, (page_id,))
        current_page = cursor.fetchone()
        if not current_page:
            return jsonify({"success": False, "message": "Page not found"}), 404
        chapter_id, old_page_num, current_image_url = current_page

        # Handle image upload
        image_url = current_image_url  # Keep current image by default
        if page_type == 'text_image' and 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename and allowed_file(file.filename):
                # Delete old image if exists
                if current_image_url:
                    old_file_path = os.path.join('static', current_image_url.lstrip('/'))
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                
                # Save new image
                filename = secure_filename(file.filename)
                filename = f"{int(time.time())}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                image_url = f"/{file_path}"  # Store relative path

        # If page number is changing, we need to reorder
        if new_page_num != old_page_num:
            # Get total pages in chapter
            cursor.execute("""
                SELECT COUNT(*) 
                FROM lesson_content 
                WHERE chapter_id = %s
            """, (chapter_id,))
            total_pages = cursor.fetchone()[0]
            # Validate new page number
            if new_page_num < 1 or new_page_num > total_pages:
                return jsonify({"success": False, "message": "Invalid page number"}), 400
            try:
                # First, update the current page to a temporary number to avoid conflicts
                cursor.execute("""
                    UPDATE lesson_content 
                    SET page_num = 0 
                    WHERE id = %s
                """, (page_id,))
                # If moving to a lower number (e.g., page 4 to page 2)
                if new_page_num < old_page_num:
                    cursor.execute("""
                        UPDATE lesson_content 
                        SET page_num = page_num + 1 
                        WHERE chapter_id = %s 
                        AND page_num >= %s 
                        AND page_num < %s
                    """, (chapter_id, new_page_num, old_page_num))
                # If moving to a higher number (e.g., page 2 to page 4)
                else:
                    cursor.execute("""
                        UPDATE lesson_content 
                        SET page_num = page_num - 1 
                        WHERE chapter_id = %s 
                        AND page_num > %s 
                        AND page_num <= %s
                    """, (chapter_id, old_page_num, new_page_num))
                # Finally, update the current page with its new number
                cursor.execute("""
                    UPDATE lesson_content 
                    SET title = %s, content = %s, code_example = %s, 
                        image_url = %s, next_button_text = %s, page_num = %s, page_type = %s, correct_message = %s, incorrect_message = %s, notes = %s
                    WHERE id = %s
                """, (
                    title,
                    content,
                    code_example,
                    image_url,
                    next_button_text,
                    new_page_num,
                    page_type,
                    correct_message,
                    incorrect_message,
                    notes,
                    page_id,
                ))
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
        else:
            # Just update the content without reordering
            cursor.execute("""
                UPDATE lesson_content 
                SET title = %s, content = %s, code_example = %s, 
                    image_url = %s, next_button_text = %s, page_type = %s, correct_message = %s, incorrect_message = %s, notes = %s
                WHERE id = %s
            """, (
                title,
                content,
                code_example,
                image_url,
                next_button_text,
                page_type,
                correct_message,
                incorrect_message,
                notes,
                page_id,
            ))
            conn.commit()

        # If quiz, update choices
        if page_type == 'quiz':
            # Delete old choices
            cursor.execute("DELETE FROM lesson_choices WHERE lesson_content_id = %s", (page_id,))
            # Add new choices
            choices = []
            for key in request.form:
                if key.startswith('choice_text_'):
                    idx = key.split('_')[-1]
                    text = request.form.get(key)
                    choices.append((idx, text))
            correct_idx = request.form.get('correct_choice')
            for idx, text in choices:
                is_correct = (str(idx) == str(correct_idx))
                cursor.execute("""
                    INSERT INTO lesson_choices (lesson_content_id, choice_text, is_correct)
                    VALUES (%s, %s, %s)
                """, (page_id, text, is_correct))
            conn.commit()
        return jsonify({"success": True, "message": "Lesson page updated successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/lesson-content/<int:page_id>', methods=['DELETE'])
@login_required
def delete_lesson_content(page_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get the chapter_id before deleting
        cursor.execute("SELECT chapter_id FROM lesson_content WHERE id = %s", (page_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"success": False, "message": "Page not found"}), 404
        chapter_id = result[0]
        # Delete the page
        cursor.execute("DELETE FROM lesson_content WHERE id = %s", (page_id,))
        # Reorder remaining pages (split into two statements)
        cursor.execute("SET @row_number = 0;")
        cursor.execute("""
            UPDATE lesson_content 
            SET page_num = (@row_number:=@row_number + 1) 
            WHERE chapter_id = %s 
            ORDER BY page_num;
        """, (chapter_id,))
        # Recalculate progress for all users who have started this chapter
        cursor.execute("""
            UPDATE user_progress up
            JOIN (
                SELECT user_id, chapter_id, progress
                FROM user_progress
                WHERE chapter_id = %s
            ) current_progress ON up.user_id = current_progress.user_id AND up.chapter_id = current_progress.chapter_id
            SET up.progress = (current_progress.progress * (SELECT COUNT(*) FROM lesson_content WHERE chapter_id = %s)) / 
                            (SELECT COUNT(*) FROM lesson_content WHERE chapter_id = %s AND page_num <= 
                                (SELECT FLOOR(current_progress.progress * (SELECT COUNT(*) FROM lesson_content WHERE chapter_id = %s) / 100))
                            )
            WHERE up.chapter_id = %s
        """, (chapter_id, chapter_id, chapter_id, chapter_id, chapter_id))
        conn.commit()
        return jsonify({"success": True, "message": "Lesson page deleted successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/user/classic/<level>/<int:chapter_id>/ajax')
@login_required
def user_lesson_content_ajax(level, chapter_id):
    level = unquote(level)
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)

        requested_page = request.args.get('page', type=int) or 1
        if requested_page < 1:
            requested_page = 1

        # Retrieve total page count once (leverages new index on chapter_id/page_num)
        db_cursor.execute("SELECT COUNT(*) AS total FROM lesson_content WHERE chapter_id = %s", (chapter_id,))
        total_row = db_cursor.fetchone() or {}
        total_pages = total_row.get('total', 0)

        if total_pages == 0:
            return jsonify({'error': 'No lesson pages found', 'is_congrats': False}), 404

        # When requested page exceeds available pages, return completion summary
        if requested_page > total_pages:
            db_cursor.execute("SELECT xp_reward, points_reward, title FROM chapters WHERE id = %s", (chapter_id,))
            chapter = db_cursor.fetchone() or {}
            xp = chapter.get('xp_reward', 0)
            points = chapter.get('points_reward', 0)
            chapter_title = chapter.get('title', '')
            html = render_template_string('''
<div class="congrats-summary text-center">
  <dotlottie-player src="https://lottie.host/1aaf6a28-e236-4b85-80a9-36d4f5fdcc54/YzZgsLVQjc.lottie" background="transparent" speed="1" style="width: 200px; height: 200px; margin: 0 auto; scale: 1.5;" autoplay></dotlottie-player>
  <h2 class="congrats-title" style="color: #ff69b4; font-family: 'Luckiest Guy', cursive; font-size: 3.5rem; text-shadow: 3px 3px 0px #7e31ef;">Congratulations!</h2>
  <p class="congrats-subtitle" style="font-size: 1.5rem; color: #fff; margin-top: 10px;">You've completed <b>{{ chapter_title }}</b>!</p>
  <div class="rewards d-flex justify-content-center gap-4 my-4">
    <span style="font-size: 1.8rem; color: gold; background: rgba(0,0,0,0.2); padding: 10px 20px; border-radius: 10px;"><i class="fas fa-star"></i> <b>{{ xp }}</b> XP</span>
    <span style="font-size: 1.8rem; color: #ff69b4; background: rgba(0,0,0,0.2); padding: 10px 20px; border-radius: 10px;"><i class="fas fa-trophy"></i> <b>{{ points }}</b> Points</span>
  </div>
  <div class="cta mt-4">
    <button class="btn btn-lg end-btn" style="font-size: 1.5rem; padding: 12px 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);" onclick="window.location.href='/user/classic/{{ level }}'">Back to Chapters</button>
  </div>
</div>
''', xp=xp, points=points, chapter_title=chapter_title, level=level)
            return jsonify({
                'html': html,
                'next_button_text': None,
                'is_quiz_page': False,
                'is_congrats': True
            })

        # Fetch the requested page only
        db_cursor.execute(
            """
            SELECT id, page_num, title, content, code_example, image_url, next_button_text,
                   page_type, correct_message, incorrect_message, notes
            FROM lesson_content
            WHERE chapter_id = %s AND page_num = %s
            LIMIT 1
            """,
            (chapter_id, requested_page),
        )
        page = db_cursor.fetchone()

        if not page:
            return jsonify({'error': 'Lesson page not found', 'is_congrats': False}), 404

        if page.get('next_button_text') is None:
            page['next_button_text'] = 'Next'
        if page.get('code_example') is None:
            page['code_example'] = ''
        if page.get('notes') is None:
            page['notes'] = ''
        if page.get('incorrect_message') is None:
            page['incorrect_message'] = ''

        page['content'] = render_inline_code_spans(page.get('content', '') or '')
        page['notes'] = render_inline_code_spans(page.get('notes', '') or '')

        if page.get('page_type') == 'quiz':
            db_cursor.execute(
                "SELECT id, choice_text, is_correct FROM lesson_choices WHERE lesson_content_id = %s ORDER BY id",
                (page['id'],),
            )
            page['choices'] = db_cursor.fetchall()
        else:
            page['choices'] = []

        page_meta = {
            'page_id': page['id'],
            'page_num': page['page_num'],
            'title': page.get('title') or '',
            'page_type': page.get('page_type'),
        }
        plain_text = strip_html_to_text(page.get('content', ''))
        if plain_text:
            page_meta['plain_text'] = plain_text

        quiz_meta = None
        if page_meta['page_type'] == 'quiz':
            choices = page.get('choices') or []
            correct_choice = next((choice for choice in choices if choice.get('is_correct')), None)
            quiz_meta = {
                'page_id': page['id'],
                'page_num': page['page_num'],
                'question': plain_text or page_meta['title'] or f"Question {page['page_num']}",
                'correct_choice': correct_choice.get('choice_text') if correct_choice else '',
                'correct_message': page.get('correct_message') or '',
                'incorrect_message': page.get('incorrect_message') or '',
            }
            page_meta['quiz'] = quiz_meta
        else:
            title_lower = (page_meta['title'] or '').lower()
            if page_meta['page_type'] in ('text_image', 'text_code') and 'takeaway' in title_lower:
                page_meta['takeaway'] = {
                    'title': page_meta['title'] or f"Page {page['page_num']}",
                    'summary': plain_text,
                    'notes': strip_html_to_text(page.get('notes', '')) if page.get('notes') else ''
                }

        html = render_template_string('''
<div id="lesson-page-meta" data-lesson-content-id="{{ page.id }}" hidden></div>
{% if page.page_type == 'text_image' %}
  {% if page.image_url %}
  <img src="{{ page.image_url }}" alt="{{ page.title }}" style="width: auto; height: 200px; text-align: center; display: block; margin: 0 auto 20px auto;" />
  {% endif %}
  <div>{{ page.content|safe }}</div>
{% elif page.page_type == 'text_code' %}
  <div>{{ page.content|safe }}</div>
  {% if page.code_example %}
  <pre><code class="language-html">{{ page.code_example|e }}</code></pre>
  {% endif %}
{% elif page.page_type == 'quiz' %}
  <div>{{ page.content|safe }}</div>
  <form id="quiz-form">
        <input type="hidden" id="correct-message" value="{{ page.correct_message|default('', true)|e }}" />
        <input type="hidden" id="incorrect-message" value="{{ page.incorrect_message|default('', true)|e }}" />
    {% if page.choices %}
      {% for choice in page.choices %}
        <div class="form-check">
          <input class="form-check-input" type="radio" name="quiz_choice" id="choice{{ loop.index }}" value="{{ choice.id }}" data-is-correct="{{ choice.is_correct|int }}">
          <label class="form-check-label" for="choice{{ loop.index }}">
            {{ choice.choice_text }}
          </label>
        </div>
      {% endfor %}
    {% else %}
      <p><em>No choices available.</em></p>
    {% endif %}
  </form>
{% elif page.page_type == 'playground' %}
  <div>{{ page.content|safe }}</div>
  <div id="playground-fullscreen-wrapper" class="playground-fullscreen-wrapper">
    <div id="playground-editor-outer" class="playground-outer position-relative">
      <div class="playground-toolbar">
        <span class="playground-title"><i class="fas fa-code"></i> Code Playground</span>
        <div class="playground-actions">
          <select id="playground-language" class="playground-lang-select" onchange="changePlaygroundMode(this.value)">
            <option value="htmlmixed">HTML/CSS/JS</option>
            <option value="xml">XML</option>
            <option value="javascript">JavaScript</option>
            <option value="css">CSS</option>
          </select>
          <button class="btn btn-success playground-run-btn" onclick="runPlaygroundCode()">
            <i class="fas fa-play"></i> Run
          </button>
        </div>
      </div>
      <div id="playground-editor-container">
                <textarea id="playground-editor">{{ page.code_example|default('', true) }}</textarea>
      </div>
      <button id="playground-fullscreen-btn" class="playground-fullscreen-btn" title="Fullscreen" type="button">
        <i class="fas fa-expand"></i>
      </button>
    </div>
    <div id="playground-output" class="playground-output" style="display: none; height: 100vh;">
      <div class="playground-output-header" style="display:none;">Output</div>
      <div id="playground-output-content"><span class="playground-output-placeholder">No output yet</span></div>
    </div>
  </div>
  <style>
    .playground-fullscreen-wrapper.fullscreen .playground-outer {
      flex: 1 1 0;
      min-width: 0;
      border-right: 2px solid #2d145c;
      background: #19182c;
      display: flex;
      flex-direction: column;
      height: 100% !important;
      max-height: 100% !important;
    }
    .playground-fullscreen-wrapper.fullscreen #playground-editor-container,
    .playground-fullscreen-wrapper.fullscreen .CodeMirror {
      flex: 1 1 0;
      height: 100% !important;
      min-height: 0 !important;
      max-height: 100% !important;
    }
    .playground-fullscreen-wrapper.fullscreen .playground-toolbar {
      border-radius: 0;
    }
    .playground-fullscreen-wrapper.fullscreen .playground-output {
      display: flex !important;
      flex-direction: column;
      flex: 1 1 0;
      min-width: 0;
      height: 100% !important;
      max-height: 100% !important;
      margin: 0 !important;
      border-radius: 0 !important;
      box-shadow: none !important;
      font-size: 1.1rem;
      overflow: auto;
      border-left: 2px solid #2d145c;
      background: #23223a;
    }
    .playground-fullscreen-wrapper.fullscreen .playground-output-header {
      display: block !important;
    }
    .playground-fullscreen-wrapper.fullscreen #playground-output-content {
      flex: 1 1 0;
      height: 100%;
      overflow: auto;
      display: flex;
      flex-direction: column;
    }
    @media (max-width: 900px) {
      .playground-fullscreen-wrapper.fullscreen {
        flex-direction: column;
      }
      .playground-fullscreen-wrapper.fullscreen .playground-outer,
      .playground-fullscreen-wrapper.fullscreen .playground-output {
        height: 50% !important;
        max-height: 50% !important;
      }
      .playground-fullscreen-wrapper.fullscreen .playground-outer {
        border-right: none;
        border-bottom: 2px solid #2d145c;
      }
      .playground-fullscreen-wrapper.fullscreen .playground-output {
        border-left: none;
        border-top: 2px solid #2d145c;
      }
    }
  </style>
  <script>
    function runPlaygroundCode() {
      var code = window.codeMirrorInstance ? window.codeMirrorInstance.getValue() : document.getElementById('playground-editor').value;
      var output = document.getElementById('playground-output');
      var outputContent = document.getElementById('playground-output-content');
      // Show loader
      output.style.display = '';
      outputContent.innerHTML = '<div class="playground-loader" style="display: flex; align-items: center; justify-content: center; height: 60px;"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
      setTimeout(function() {
        try {
          outputContent.innerHTML = '';
          var iframe = document.createElement('iframe');
          iframe.style.width = '100%';
          iframe.style.height = '100%';
          iframe.style.background = '#fff';
          if (document.querySelector('.playground-fullscreen-wrapper.fullscreen')) {
            iframe.style.height = '100%';
          }
          outputContent.appendChild(iframe);
        } catch (e) {
          outputContent.textContent = 'Error running code: ' + e;
        }
      }, 700); // Simulate processing delay
    }
    function setupPlaygroundFullscreen() {
      var wrapper = document.getElementById('playground-fullscreen-wrapper');
      var outer = document.getElementById('playground-editor-outer');
      var output = document.getElementById('playground-output');
      var btn = document.getElementById('playground-fullscreen-btn');
      var outputHeader = output.querySelector('.playground-output-header');
      var outputContent = document.getElementById('playground-output-content');
      if (!wrapper || !btn) return;
      btn.onclick = function() {
        var isFullscreen = wrapper.classList.toggle('fullscreen');
        if (isFullscreen) {
          btn.innerHTML = '<i class="fas fa-compress"></i>';
          output.style.display = 'flex';
          wrapper.style.position = 'absolute';
          wrapper.style.top = '0';
          wrapper.style.left = '0';
          wrapper.style.width = '100%';
          wrapper.style.height = '100%';
          if (outputHeader) outputHeader.style.display = 'block';
          if (outputContent && !outputContent.innerHTML.trim()) {
            outputContent.innerHTML = '<span class="playground-output-placeholder">No output yet</span>';
          }
          // Resize CodeMirror
          if (window.codeMirrorInstance) {
            setTimeout(function() { window.codeMirrorInstance.refresh(); }, 200);
          }
        } else {
          btn.innerHTML = '<i class="fas fa-expand"></i>';
          output.style.display = 'none';
          wrapper.style.position = '';
          wrapper.style.top = '';
          wrapper.style.left = '';
          wrapper.style.width = '';
          wrapper.style.height = '';
          if (outputHeader) outputHeader.style.display = 'none';
          if (outputContent) outputContent.innerHTML = '<span class="playground-output-placeholder">No output yet</span>';
          // Resize CodeMirror
          if (window.codeMirrorInstance) {
            setTimeout(function() { window.codeMirrorInstance.refresh(); }, 200);
          }
        }
      };
      // On initial fullscreen, show placeholder if no output
      if (wrapper.classList.contains('fullscreen') && outputContent && !outputContent.innerHTML.trim()) {
        outputContent.innerHTML = '<span class="playground-output-placeholder">No output yet</span>';
      }
    }
    document.addEventListener('DOMContentLoaded', setupPlaygroundFullscreen);
  </script>
{% else %}
  <div>{{ page.content|safe }}</div>
{% endif %}
<script>if(window.Prism){Prism.highlightAll();}</script>
''', page=page)
        is_quiz_page = page.get('page_type') == 'quiz'
        return jsonify({
            'html': html,
            'next_button_text': page.get('next_button_text', 'Next'),
            'is_quiz_page': is_quiz_page,
            'is_congrats': False,
            'quiz_meta': quiz_meta,
            'page_meta': page_meta
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/proxy/gpt4o')
def proxy_gpt4o():
    ask = request.args.get('ask')
    uid = request.args.get('uid')
    roleplay = request.args.get('roleplay')
    if not ask:
        return jsonify({'error': 'Missing ask parameter'}), 400
    try:
        api_url = 'https://www.haji-mix-api.gleeze.com/api/gpt4o'
        params = {'ask': ask}
        if uid:
            params['uid'] = uid
        if roleplay:
            params['roleplay'] = roleplay
        resp = requests.get(api_url, params=params, timeout=30)
        return (resp.text, resp.status_code, {'Content-Type': resp.headers.get('Content-Type', 'application/json')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/account')
@login_required
def account():
    user_id = session['user_id']
    performance = {
        'progress': {
            'overall_percent': 0.0,
            'overall_percent_label': '0',
            'overall_percent_display': 0,
            'bar_width': 0,
            'completed_chapters': 0,
            'in_progress_chapters': 0,
            'total_chapters': 0,
        },
        'engagement': {
            'total_time_seconds': 0,
            'total_time_label': '0m',
            'active_days': 0,
            'avg_daily_label': '0m',
            'chapters_visited': 0,
            'last_active_label': None,
            'last_active_relative': '',
        },
        'scores': {
            'xp': 0,
            'points': 0,
            'rating': DEFAULT_RATING,
            'level': 1,
        },
    }
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)

        # Fetch user info
        db_cursor.execute("SELECT id, username, email, avatar_path, google_id FROM users WHERE id = %s", (user_id,))
        user = db_cursor.fetchone()

        # Fetch user badges (join to get badge name and icon)
        db_cursor.execute('''
            SELECT b.id, b.name, b.description, b.icon
            FROM user_badges ub
            JOIN badges b ON ub.badge_id = b.id
            WHERE ub.user_id = %s
            ORDER BY ub.earned_at ASC
        ''', (user_id,))
        badges = db_cursor.fetchall()

        # Learning progress metrics
        total_chapters = 0
        try:
            db_cursor.execute("SELECT COUNT(*) AS total FROM chapters")
            total_row = db_cursor.fetchone() or {}
            total_chapters = int(total_row.get('total') or 0)
        except mysql_errors.ProgrammingError:
            total_chapters = 0

        try:
            db_cursor.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END), 0) AS completed,
                    COALESCE(SUM(CASE WHEN completed = 0 AND progress > 0 THEN 1 ELSE 0 END), 0) AS in_progress,
                    COALESCE(SUM(progress), 0) AS total_progress
                FROM user_progress
                WHERE user_id = %s
                """,
                (user_id,),
            )
            progress_row = db_cursor.fetchone() or {}
        except mysql_errors.ProgrammingError:
            progress_row = {}

        completed_chapters = int(progress_row.get('completed') or 0)
        in_progress_chapters = int(progress_row.get('in_progress') or 0)
        progress_sum = float(progress_row.get('total_progress') or 0.0)
        overall_percent = 0.0
        if total_chapters:
            overall_percent = min(progress_sum / total_chapters, 100.0)
        overall_percent_label = f"{overall_percent:.1f}"
        if overall_percent_label.endswith('.0'):
            overall_percent_label = overall_percent_label[:-2]
        if not overall_percent_label:
            overall_percent_label = '0'
        bar_width = max(0, min(int(round(overall_percent)), 100))
        performance['progress'].update({
            'total_chapters': total_chapters,
            'completed_chapters': completed_chapters,
            'in_progress_chapters': in_progress_chapters,
            'overall_percent': overall_percent,
            'overall_percent_label': overall_percent_label,
            'overall_percent_display': int(round(overall_percent)),
            'bar_width': bar_width,
        })

        # Engagement metrics
        try:
            db_cursor.execute(
                """
                SELECT
                    COALESCE(SUM(time_spent), 0) AS total_time,
                    COALESCE(COUNT(DISTINCT DATE(last_visited)), 0) AS active_days,
                    COALESCE(COUNT(DISTINCT chapter_id), 0) AS chapters_visited,
                    MAX(last_visited) AS last_visited
                FROM lesson_page_analytics
                WHERE user_id = %s
                """,
                (user_id,),
            )
            engagement_row = db_cursor.fetchone() or {}
        except mysql_errors.ProgrammingError:
            engagement_row = {}

        total_time_spent = int(float(engagement_row.get('total_time') or 0))
        active_days = int(engagement_row.get('active_days') or 0)
        chapters_visited = int(engagement_row.get('chapters_visited') or 0)
        last_active_dt = engagement_row.get('last_visited')
        try:
            last_active_label = last_active_dt.strftime("%b %d, %Y %I:%M %p") if last_active_dt else None
        except Exception:
            last_active_label = None
        avg_daily_seconds = total_time_spent // active_days if active_days else 0
        performance['engagement'].update({
            'total_time_seconds': total_time_spent,
            'total_time_label': _format_duration_short(total_time_spent),
            'active_days': active_days,
            'avg_daily_label': _format_duration_short(avg_daily_seconds),
            'chapters_visited': chapters_visited,
            'last_active_label': last_active_label,
            'last_active_relative': _format_relative_time(last_active_dt),
        })

        # Score metrics
        try:
            db_cursor.execute(
                "SELECT xp, level, points, rating FROM user_stats WHERE user_id = %s",
                (user_id,),
            )
            stats_row = db_cursor.fetchone()
        except mysql_errors.ProgrammingError:
            stats_row = None
        if stats_row:
            rating_value = int(stats_row.get('rating') or DEFAULT_RATING)
            performance['scores'].update({
                'xp': int(stats_row.get('xp') or 0),
                'level': int(stats_row.get('level') or 1),
                'points': int(stats_row.get('points') or 0),
                'rating': rating_value if rating_value > 0 else DEFAULT_RATING,
            })

        # Fetch user rank (by points, from leaderboards)
        db_cursor.execute('''
            SELECT user_id, total_score FROM leaderboards ORDER BY total_score DESC
        ''')
        leaderboard = db_cursor.fetchall()
        user_rank = None
        user_points = 0
        for idx, entry in enumerate(leaderboard, 1):
            if entry['user_id'] == user_id:
                user_rank = idx
                user_points = entry['total_score']
                break

        if user_points:
            try:
                performance['scores']['points'] = max(performance['scores']['points'], int(user_points))
            except Exception:
                pass

        return render_template('account.html', user=user, badges=badges, user_rank=user_rank, user_points=user_points, performance=performance)
    except Exception as e:
        print("Account page error:", str(e))
        return render_template('account.html', user=None, badges=[], user_rank=None, user_points=0, performance=performance)
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user_id = session['user_id']
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor()
        # Delete user (CASCADE will remove related user_badges, progress, etc.)
        db_cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db_connection.commit()
        session.clear()
        return jsonify({'success': True, 'redirect': url_for('home')})
    except Exception as e:
        print("Delete account error:", str(e))
        if 'db_connection' in locals():
            db_connection.rollback()
        return jsonify({'success': False, 'message': 'Failed to delete account'})
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/account/update', methods=['POST'])
@login_required
def update_account():
    try:
        user_id = session['user_id']
        username = request.form.get('username', '').strip()
        use_google_avatar = request.form.get('use_google_avatar') == '1'
        avatar_file = request.files.get('avatar')

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # Fetch current user and google_id
        cur.execute("SELECT id, username, google_id, avatar_path FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Validate unique username if changed
        if username and username != user['username']:
            if len(username) < 3:
                return jsonify({'success': False, 'message': 'Username must be at least 3 characters'})
            cur.execute("SELECT id FROM users WHERE username = %s AND id <> %s", (username, user_id))
            if cur.fetchone():
                return jsonify({'success': False, 'message': 'Username already taken'})

        new_avatar_path = user['avatar_path']
        if use_google_avatar and user.get('google_id'):
            # Keep avatar_path as is (already set at login) or clear to let frontend display Google image URL
            # We'll retain avatar_path if already stored from Google profile
            pass
        else:
            # Handle avatar upload if provided
            if avatar_file and avatar_file.filename and allowed_file(avatar_file.filename):
                filename = secure_filename(avatar_file.filename)
                filename = f"{int(time.time())}_{filename}"
                file_path = os.path.join('static', 'uploads', 'lesson_images', filename)
                try:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                except Exception:
                    pass
                avatar_file.save(file_path)
                new_avatar_path = f"/{file_path}"

        # Apply updates
        update_fields = []
        params = []
        if username and username != user['username']:
            update_fields.append("username = %s")
            params.append(username)
        if new_avatar_path != user['avatar_path']:
            update_fields.append("avatar_path = %s")
            params.append(new_avatar_path)

        if update_fields:
            params.append(user_id)
            cur2 = conn.cursor()
            cur2.execute(f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s", tuple(params))
            conn.commit()
            cur2.close()
            # Keep session username in sync if it changed
            if username and username != user['username']:
                session['username'] = username

        return jsonify({'success': True, 'message': 'Account updated successfully', 'updated_username': username if username else user['username']})
    except Exception as e:
        if 'conn' in locals():
            try:
                conn.rollback()
            except Exception:
                pass
        print('update_account error:', str(e))
        return jsonify({'success': False, 'message': 'Failed to update account'}), 500
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

@app.route('/account/check-username')
@login_required
def check_username():
    try:
        desired = (request.args.get('username') or '').strip()
        if not desired:
            return jsonify({'available': False, 'reason': 'empty'})
        if len(desired) < 3:
            return jsonify({'available': False, 'reason': 'short'})
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE username = %s AND id <> %s", (desired, session['user_id']))
        count = cur.fetchone()[0]
        cur.close(); conn.close()
        return jsonify({'available': count == 0})
    except Exception as e:
        return jsonify({'available': False, 'error': str(e)}), 500

@app.route('/user/classic/<level>/<int:chapter_id>/<int:page_num>/analytics', methods=['POST'])
@login_required
def log_page_analytics(level, chapter_id, page_num):
    try:
        data = request.get_json()
        time_spent = int(data.get('time_spent', 0))
        incorrect_attempts = int(data.get('incorrect_attempts', 0))
        is_new_visit = data.get('is_new_visit', False)  # New parameter to indicate if this is a new visit
        session_key = data.get('session_key', None)  # Unique session key to prevent duplicates
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor()

        # Check if this user has already visited this page
        check_query = """
        SELECT id, visit_count FROM lesson_page_analytics 
        WHERE user_id = %s AND chapter_id = %s AND page_num = %s
        """
        db_cursor.execute(check_query, (session['user_id'], chapter_id, page_num))
        existing_record = db_cursor.fetchone()

        if existing_record:
            # Update existing record - only increment visit_count if it's a new visit
            # Cap visit_count at 1 to satisfy DB constraint (0 or 1 only)
            visit_increment = 1 if is_new_visit else 0
            update_query = """
            UPDATE lesson_page_analytics 
            SET visit_count = LEAST(1, visit_count + %s),
                last_visited = NOW()
            WHERE user_id = %s AND chapter_id = %s AND page_num = %s
            """
            db_cursor.execute(update_query, (
                visit_increment, session['user_id'], chapter_id, page_num
            ))
        else:
            # Insert new record - only for first visit
            insert_query = """
            INSERT INTO lesson_page_analytics 
            (user_id, chapter_id, page_num, time_spent, visit_count, incorrect_attempts, last_visited)
            VALUES (%s, %s, %s, %s, 1, %s, NOW())
            """
            db_cursor.execute(insert_query, (
                session['user_id'], chapter_id, page_num, time_spent, incorrect_attempts
            ))
        
        db_connection.commit()
        return jsonify({'success': True})
    except Exception as e:
        print("Analytics logging error:", str(e))
        if 'db_connection' in locals():
            db_connection.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

@app.route('/admin/levels/<int:level_id>/analytics')
@login_required
def admin_level_analytics(level_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        
        # Query to get analytics data properly aggregated
        query = '''
            SELECT 
                c.id AS chapter_id,
                c.title AS chapter_title,
                lc.page_num,
                lc.title AS page_title,
                lpa.user_id,
                AVG(lpa.time_spent) AS avg_time_spent,
                SUM(lpa.visit_count) AS total_visits,
                SUM(lpa.incorrect_attempts) AS total_incorrect
            FROM chapters c
            JOIN lesson_content lc ON lc.chapter_id = c.id
            LEFT JOIN lesson_page_analytics lpa ON lpa.chapter_id = c.id AND lpa.page_num = lc.page_num
            WHERE c.level_id = %s
            GROUP BY c.id, c.title, lc.page_num, lc.title, lpa.user_id
            ORDER BY c.id, lc.page_num, lpa.user_id
        '''
        db_cursor.execute(query, (level_id,))
        analytics = db_cursor.fetchall()
        
        # Process the data to get proper chapter-level unique user counts
        chapter_data = {}
        page_data = {}
        
        for row in analytics:
            chapter_id = row['chapter_id']
            page_num = row['page_num']
            user_id = row['user_id']
            
            # Initialize chapter data if not exists
            if chapter_id not in chapter_data:
                chapter_data[chapter_id] = {
                    'chapter_title': row['chapter_title'],
                    'unique_users': set(),
                    'total_page_visits': 0,
                    'total_incorrect': 0
                }
            
            # Initialize page data if not exists
            page_key = f"{chapter_id}_{page_num}"
            if page_key not in page_data:
                page_data[page_key] = {
                    'chapter_id': chapter_id,
                    'chapter_title': row['chapter_title'],
                    'page_num': page_num,
                    'page_title': row['page_title'],
                    'total_visits': 0,
                    'total_incorrect': 0
                }
            
            # Add data if user_id exists (not null)
            if user_id:
                chapter_data[chapter_id]['unique_users'].add(user_id)
                chapter_data[chapter_id]['total_page_visits'] += row['total_visits'] or 0
                chapter_data[chapter_id]['total_incorrect'] += row['total_incorrect'] or 0
                
                page_data[page_key]['total_visits'] += row['total_visits'] or 0
                page_data[page_key]['total_incorrect'] += row['total_incorrect'] or 0
        
        # Convert sets to counts and format the response
        processed_analytics = []
        for page_key, page_info in page_data.items():
            processed_analytics.append({
                'chapter_id': page_info['chapter_id'],
                'chapter_title': page_info['chapter_title'],
                'page_num': page_info['page_num'],
                'page_title': page_info['page_title'],
                'total_visits': page_info['total_visits'],
                'total_incorrect': page_info['total_incorrect']
            })
        
        # Add chapter-level data for unique user counts
        chapter_summary = {}
        for chapter_id, chapter_info in chapter_data.items():
            chapter_summary[chapter_id] = {
                'unique_users': len(chapter_info['unique_users']),
                'total_page_visits': chapter_info['total_page_visits'],
                'total_incorrect': chapter_info['total_incorrect']
            }
        
        return jsonify({
            'success': True, 
            'analytics': processed_analytics,
            'chapter_summary': chapter_summary
        })
    except Exception as e:
        print("Analytics fetch error:", str(e))
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if 'db_cursor' in locals():
            db_cursor.close()
        if 'db_connection' in locals():
            db_connection.close()

# === GOOGLE ANALYTICS DATA API ENDPOINT FOR ADMIN DASHBOARD ===
@app.route('/admin/analytics-data')
@login_required
def admin_analytics_data():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        GA_PROPERTY_ID = '493879650'
        CREDENTIALS_FILE = os.path.join(os.getcwd(), 'ga-credentials.json')
        client = BetaAnalyticsDataClient.from_service_account_file(CREDENTIALS_FILE)
        from datetime import datetime
        import calendar

        now = datetime.now()
        year = now.year
        current_month = now.month
        months = [calendar.month_abbr[m] for m in range(1, current_month+1)]
        month_keys = [f"{m:02d}" for m in range(1, current_month+1)]
        start_date = f"{year}-01-01"
        end_date = now.strftime('%Y-%m-%d')
        request = RunReportRequest(
            property=f"properties/{GA_PROPERTY_ID}",
            dimensions=[Dimension(name="month")],
            metrics=[Metric(name="activeUsers")],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)]
        )
        response = client.run_report(request)
        print("GA API rows:", [(row.dimension_values[0].value, row.metric_values[0].value) for row in response.rows])
        data_map = {row.dimension_values[0].value: int(row.metric_values[0].value) for row in response.rows}
        print("Data map:", data_map)
        data = [data_map.get(key, 0) for key in month_keys]
        print("Labels:", months)
        print("Data:", data)
        return jsonify({"success": True, "labels": months, "data": data})
    except Exception as e:
        print("Google Analytics API error:", str(e))
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/admin/total-users')
@login_required
def admin_total_users():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor()
        db_cursor.execute("SELECT COUNT(*) FROM users")
        total = db_cursor.fetchone()[0]
        db_cursor.close()
        db_connection.close()
        return jsonify({'success': True, 'total_users': total})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/active-users')
@login_required
def admin_active_users():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        GA_PROPERTY_ID = '493879650'
        CREDENTIALS_FILE = os.path.join(os.getcwd(), 'ga-credentials.json')
        client = BetaAnalyticsDataClient.from_service_account_file(CREDENTIALS_FILE)
        request = RunReportRequest(
            property=f"properties/{GA_PROPERTY_ID}",
            metrics=[Metric(name="activeUsers")],
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")]
        )
        response = client.run_report(request)
        active_users = int(response.rows[0].metric_values[0].value) if response.rows else 0
        return jsonify({'success': True, 'active_users': active_users})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/levels-completed')
@login_required
def admin_levels_completed():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor()
        # Count all completed chapters (levels) by all users
        db_cursor.execute("SELECT COUNT(*) FROM user_progress WHERE completed = TRUE")
        total = db_cursor.fetchone()[0]
        db_cursor.close()
        db_connection.close()
        return jsonify({'success': True, 'levels_completed': total})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/recent-signups')
@login_required
def admin_recent_signups():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        db_cursor.execute("SELECT id, username, email, created_at FROM users ORDER BY created_at DESC LIMIT 5")
        users = db_cursor.fetchall()
        db_cursor.close()
        db_connection.close()
        # Format registration date for display
        for user in users:
            if user.get('created_at'):
                user['registered_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M')
            else:
                user['registered_at'] = ''
            user.pop('created_at', None)
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/top-users')
@login_required
def admin_top_users():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    try:
        db_connection = get_db_connection()
        db_cursor = db_connection.cursor(dictionary=True)
        db_cursor.execute("""
            SELECT u.username,
                   us.points,
                   us.xp,
                   COALESCE(us.rating, %s) AS rating
            FROM user_stats us
            JOIN users u ON us.user_id = u.id
            ORDER BY rating DESC, us.points DESC, us.xp DESC
            LIMIT 5
        """, (DEFAULT_RATING,))
        users = db_cursor.fetchall()
        db_cursor.close()
        db_connection.close()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
