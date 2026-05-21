from flask import Flask, request, jsonify, send_from_directory, g, send_file, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv    # <-- Add this
from typing import Optional
import os
import uuid
import requests
from utils.ppt_processor import generate_ppt, refine_ppt, generate_gamma_style_ppt
from utils.layout_extractor import extract_layouts
import json
import bcrypt
import jwt
from datetime import datetime, timedelta
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import traceback
import re
from pptx import Presentation
from pptx.util import Inches
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Pt
import ast
import random
import tempfile
from database import db_manager

load_dotenv()  # <-- Load .env variables

app = Flask(__name__)
# CORS - allow all origins
CORS(app, origins="*", allow_headers=["Authorization", "Content-Type"], expose_headers=["Content-Disposition"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
allowed_origins = ["http://localhost:5173", "http://localhost:8080", "http://localhost:3000", "https://ai-pptcon-frontend.vercel.app"]

@app.after_request
def add_cors_headers(response):
    try:
        origin = request.headers.get('Origin')
        response.headers['Access-Control-Allow-Origin'] = origin or 'https://ai-pptcon-frontend.vercel.app'
        response.headers['Access-Control-Allow-Credentials'] = 'true' 
        response.headers['Vary'] = 'Origin'
        response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
    except Exception:
        pass
    return response

# API Keys: Securely loaded from .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Name of the Gemini model to use for text generation. Set this in your .env after
# running the ListModels request (e.g. gemini-1.5, gemini-pro, text-bison, etc.).
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "")
GEMINI_API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

def gemini_url(model: Optional[str] = None) -> str:
    """Return a complete Gemini generateContent URL for the given model.

    The model is taken from GEMINI_MODEL env var if not provided.
    Raises RuntimeError when no model is configured.
    """
    model = model or GEMINI_MODEL
    if not model:
        raise RuntimeError("GEMINI model not configured. Set GEMINI_MODEL in .env")
    return GEMINI_API_URL_TEMPLATE.format(model=model)

UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY")

# Folder Setup
UPLOAD_FOLDER = 'Uploads'
OUTPUT_FOLDER = 'outputs'
TEMPLATE_FOLDER = 'templates'  # Pre-defined templates
SCREENSHOT_FOLDER = os.path.join(UPLOAD_FOLDER, 'screenshots')  # New folder for screenshots
os.makedirs(os.path.join(UPLOAD_FOLDER, "content"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "templates"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "images"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "converted"), exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')
AVATAR_FOLDER = os.path.join(os.path.dirname(__file__), 'avatars')
os.makedirs(AVATAR_FOLDER, exist_ok=True)
# JWT_SECRET = 'your_jwt_secret_key'  # Change this to a strong secret in production
JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret_key")
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 7 * 24 * 3600  # 7 din (7 days)

# Chat history storage
CHAT_HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'chat_history.json')

# Dashboard data storage
DASHBOARD_DATA_FILE = os.path.join(os.path.dirname(__file__), 'dashboard_data.json')
USER_ACTIVITIES_FILE = os.path.join(os.path.dirname(__file__), 'user_activities.json')

def load_users():
    """Load users from database (fallback to JSON if database not available)"""
    if db_manager.db is not None:
        # Use MongoDB
        users = list(db_manager.db.users.find({}, {'_id': 0}))
        return {user['email']: user for user in users}
    else:
        # Fallback to JSON
        if not os.path.exists(USERS_FILE):
            return {}
        with open(USERS_FILE, 'r') as f:
            try:
                return json.load(f)
            except Exception:
                return {}

def save_users(users):
    """Save users to database (fallback to JSON if database not available)"""
    if db_manager.db is not None:
        # Use MongoDB
        for email, user_data in users.items():
            db_manager.db.users.update_one(
                {"email": email},
                {"$set": user_data},
                upsert=True
            )
    else:
        # Fallback to JSON
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt(email):
    payload = {
        'username': email.lower(),
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['username']
    except Exception as e:
        print("JWT decode error:", e)
        return None

def jwt_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        print("Authorization header:", auth_header)
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header missing or invalid'}), 401
        token = auth_header.split(' ')[1]
        username = verify_jwt(token)
        if not username:
            return jsonify({'error': 'Invalid or expired token'}), 401
        g.username = username
        return f(*args, **kwargs)
    return decorated

def load_chat_history():
    """Load chat history from database (fallback to JSON if database not available)"""
    if db_manager.db is not None:
        # Use MongoDB
        try:
            chats = list(db_manager.db.chat_history.find({}, {'_id': 0}))
            # Group by user_id first, then fall back to email
            grouped_chats = {}
            for chat in chats:
                # Prioritize user_id if available
                if 'user_id' in chat:
                    user_key = chat.get('user_id')
                else:
                    user_key = chat.get('email')
                
                if user_key not in grouped_chats:
                    grouped_chats[user_key] = []
                grouped_chats[user_key].append(chat)
            return grouped_chats
        except Exception as e:
            print(f"Error loading chat history from MongoDB: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON
    if not os.path.exists(CHAT_HISTORY_FILE):
        return {}
    with open(CHAT_HISTORY_FILE, 'r') as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def get_chat_history_by_email(email):
    """Return chat history list for a specific user email from DB or JSON fallback."""
    if db_manager.db is not None:
        try:
            # Use the improved get_chat_history function that prioritizes user_id
            return db_manager.get_chat_history(email)
        except Exception as e:
            print(f"Error querying chat history for {email} from MongoDB: {e}")
            # Fall through to JSON fallback
    # JSON fallback
    all_chats = load_chat_history()
    return all_chats.get(email, [])

def save_chat_history(chat_history):
    """Save chat history to database (fallback to JSON if database not available)"""
    if db_manager.db is not None:
        # Use MongoDB
        try:
            for email, chats in chat_history.items():
                for chat in chats:
                    chat['email'] = email
                    db_manager.db.chat_history.update_one(
                        {"id": chat['id']},
                        {"$set": chat},
                        upsert=True
                    )
            return
        except Exception as e:
            print(f"Error saving chat history to MongoDB: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON
    with open(CHAT_HISTORY_FILE, 'w') as f:
        json.dump(chat_history, f, indent=2)

def load_dashboard_data():
    """Load dashboard data from database (fallback to JSON if database not available)"""
    if db_manager.db is not None:
        # Use MongoDB
        try:
            # Find all documents with user_id field
            dashboard_data = list(db_manager.db.dashboard_data.find({"user_id": {"$exists": True}}, {'_id': 0}))
            result = {}
            skipped = 0
            for item in dashboard_data:
                uid = item.get('user_id')
                if not uid:
                    # Skip malformed documents without user_id to avoid blowing up and falling back to JSON
                    skipped += 1
                    continue
                # Only store the data for this specific user_id
                result[uid] = item
            if skipped:
                print(f"Warning: Skipped {skipped} dashboard_data docs missing 'user_id'.")
            return result
        except Exception as e:
            print(f"Error loading dashboard data from MongoDB: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON
    if not os.path.exists(DASHBOARD_DATA_FILE):
        return {}
    with open(DASHBOARD_DATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def save_dashboard_data(dashboard_data):
    """Save dashboard data to database (fallback to JSON if database not available)"""
    if db_manager.db is not None:
        # Use MongoDB
        try:
            for user_id, data in dashboard_data.items():
                # Ensure the document carries its user_id
                if 'user_id' not in data:
                    data['user_id'] = user_id
                db_manager.db.dashboard_data.update_one(
                    {"user_id": user_id},
                    {"$set": data},
                    upsert=True
                )
            return
        except Exception as e:
            print(f"Error saving dashboard data to MongoDB: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON
    with open(DASHBOARD_DATA_FILE, 'w') as f:
        json.dump(dashboard_data, f, indent=2)

def migrate_dashboard_user_ids():
    """Backfill missing user_id fields in dashboard_data based on users' email.
    Returns a dict summary of actions taken.
    """
    summary = {"updated": 0, "skipped": 0, "errors": 0}
    if db_manager.db is None:
        return {"error": "MongoDB not available"}
    try:
        users = load_users()
        email_to_uid = {u["email"].lower(): uid for uid, u in users.items() if u.get("email")}
        cursor = db_manager.db.dashboard_data.find({"$or": [{"user_id": {"$exists": False}}, {"user_id": None}, {"user_id": ""}]})
        for doc in cursor:
            try:
                email = doc.get("email")
                if not email:
                    summary["skipped"] += 1
                    continue
                uid = email_to_uid.get(email.lower())
                if not uid:
                    summary["skipped"] += 1
                    continue
                db_manager.db.dashboard_data.update_one({"_id": doc["_id"]}, {"$set": {"user_id": uid}})
                summary["updated"] += 1
            except Exception:
                summary["errors"] += 1
        # Ensure index on user_id for fast lookups
        try:
            db_manager.db.dashboard_data.create_index("user_id")
        except Exception:
            pass
        return summary
    except Exception as e:
        print(f"Error during migrate_dashboard_user_ids: {e}")
        return {"error": str(e)}

@app.route('/api/migrate/dashboard_data', methods=['POST'])
@jwt_required
def admin_migrate_dashboard_data():
    """Admin-only endpoint to backfill missing user_id in dashboard_data."""
    admin_email = os.environ.get("ADMIN_EMAIL")
    if not admin_email or g.username.lower() != admin_email.lower():
        return jsonify({"error": "Forbidden"}), 403
    result = migrate_dashboard_user_ids()
    status = 200 if "error" not in result else 500
    return jsonify(result), status

def load_user_activities():
    """Load user activities from database (fallback to JSON if database not available)"""
    if db_manager.db is not None:
        # Use MongoDB
        try:
            activities = list(db_manager.db.user_activities.find({}, {'_id': 0}))
            # Group by user_id first, then fall back to email
            grouped_activities = {}
            for activity in activities:
                # Prioritize user_id if available
                if 'user_id' in activity:
                    user_key = activity.get('user_id')
                else:
                    user_key = activity.get('email')
                
                if user_key not in grouped_activities:
                    grouped_activities[user_key] = []
                grouped_activities[user_key].append(activity)
            return grouped_activities
        except Exception as e:
            print(f"Error loading user activities from MongoDB: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON
    if not os.path.exists(USER_ACTIVITIES_FILE):
        return {}
    with open(USER_ACTIVITIES_FILE, 'r') as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def get_user_activities_by_email(email):
    """Return activities list for a specific user email from DB or JSON fallback."""
    if db_manager.db is not None:
        try:
            # Use the improved get_user_activities function that prioritizes user_id
            return db_manager.get_user_activities(email)
        except Exception as e:
            print(f"Error querying activities for {email} from MongoDB: {e}")
            # Fall through to JSON fallback
    # JSON fallback
    all_activities = load_user_activities()
    return all_activities.get(email, [])

def save_user_activities(user_activities):
    """Save user activities to database (fallback to JSON if database not available)"""
    if db_manager.db is not None:
        # Use MongoDB
        try:
            for email, activities in user_activities.items():
                for activity in activities:
                    activity['email'] = email
                    db_manager.db.user_activities.update_one(
                        {"id": activity['id']},
                        {"$set": activity},
                        upsert=True
                    )
            return
        except Exception as e:
            print(f"Error saving user activities to MongoDB: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON
    with open(USER_ACTIVITIES_FILE, 'w') as f:
        json.dump(user_activities, f, indent=2)

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password required'}), 400
    users = load_users()
    # Check if email or username already exists
    for user in users.values():
        if user['email'] == email:
            return jsonify({'error': 'Email already exists'}), 400
        if user['username'] == username:
            return jsonify({'error': 'Username already exists'}), 400
    user_id = str(len(users) + 1)
    users[user_id] = {
        'username': username,
        'email': email,
        'password': hash_password(password),
        'created_at': datetime.utcnow().isoformat()
    }
    save_users(users)
    token = create_jwt(email)
    return jsonify({'message': 'User registered successfully', 'token': token, 'user': {
        'id': user_id,
        'username': username,
        'email': email
    }}), 201

@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    data = request.get_json()
    access_token = data.get('access_token')
    if not access_token:
        return jsonify({'error': 'Google access token required'}), 400
    
    try:
        # Fetch user info from Google using the access token
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://www.googleapis.com/oauth2/v3/userinfo", headers=headers, timeout=10)
        if response.status_code != 200:
            return jsonify({'error': 'Invalid Google access token'}), 400
        
        user_info = response.json()
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0] if email else 'Google User')
        picture = user_info.get('picture')
        
        if not email:
            return jsonify({'error': 'Email not provided by Google'}), 400
            
        users = load_users()
        user = None
        user_id = None
        
        # Check if user already exists
        for uid, u in users.items():
            if u.get('email', '').lower() == email.lower():
                user = u
                user_id = uid
                break
                
        # If user does not exist, create new one
        if not user:
            user_id = str(len(users) + 1)
            random_pw = str(uuid.uuid4())
            users[user_id] = {
                'username': name,
                'email': email.lower(),
                'password': hash_password(random_pw),
                'created_at': datetime.utcnow().isoformat(),
                'avatar': None,
                'preferences': {}
            }
            save_users(users)
            
            # Reload users to get correct user_id/user object
            users = load_users()
            for uid, u in users.items():
                if u.get('email', '').lower() == email.lower():
                    user = u
                    user_id = uid
                    break
            
            # Download profile picture
            if picture and user:
                try:
                    r = requests.get(picture, timeout=10)
                    if r.status_code == 200:
                        ext = '.png'
                        filename = f"{user_id}{ext}"
                        filepath = os.path.join(AVATAR_FOLDER, filename)
                        with open(filepath, 'wb') as f:
                            f.write(r.content)
                        # Save the updated avatar in db
                        user['avatar'] = filename
                        users[user_id] = user
                        save_users(users)
                except Exception as e:
                    print("Failed to download Google profile picture:", e)
                    
        token = create_jwt(email)
        return jsonify({
            'token': token,
            'user': {
                'id': user_id,
                'username': user['username'],
                'email': user['email'],
                'avatar': user.get('avatar'),
                'preferences': user.get('preferences', {}),
                'created_at': user.get('created_at')
            }
        }), 200
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Google authentication failed: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    users = load_users()
    user = None
    user_id = None
    for uid, u in users.items():
        if u['email'] == email:
            user = u
            user_id = uid
            break
    if not user or not check_password(password, user['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    token = create_jwt(email)
    return jsonify({'token': token, 'user': {
        'id': user_id,
        'username': user['username'],
        'email': user['email'],
        'avatar': user.get('avatar'),
        'preferences': user.get('preferences', {}),
        'created_at': user.get('created_at')
    }}), 200

@app.route('/api/auth/me', methods=['GET'])
@jwt_required
def get_me():
    users = load_users()
    # JWT me email save ho raha hai
    email = g.username
    for uid, user in users.items():
        if user['email'].lower() == email.lower():
            return jsonify({
                'id': uid, 
                'username': user['username'], 
                'email': user['email'], 
                'avatar': user.get('avatar'),
                'preferences': user.get('preferences', {}),
                'created_at': user['created_at']
            }), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/auth/profile', methods=['PUT'])
@jwt_required
def update_profile():
    email = g.username
    users = load_users()
    for uid, user in users.items():
        if user['email'].lower() == email.lower():
            data = request.get_json()
            username = data.get('username')
            new_email = data.get('email')
            # Update username if provided
            if username:
                user['username'] = username
            # Update email if provided and unique
            if new_email and new_email != user['email']:
                for other_uid, other_user in users.items():
                    if other_uid != uid and other_user.get('email') == new_email:
                        return jsonify({'error': 'Email already exists'}), 400
                user['email'] = new_email
            # Allow updating preferences
            if 'preferences' in data:
                user['preferences'] = data['preferences']
            save_users(users)
            return jsonify({
                'user': {
                    'id': uid,
                    'username': user['username'],
                    'email': user['email'],
                    'avatar': user.get('avatar'),
                    'preferences': user.get('preferences', {}),
                    'created_at': user.get('created_at')
                }
            }), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/auth/avatar', methods=['POST'])
@jwt_required
def upload_avatar():
    email = g.username
    users = load_users()
    for uid, user in users.items():
        if user['email'].lower() == email.lower():
            # File upload
            if 'avatar' in request.files:
                file = request.files['avatar']
                if file and file.filename:
                    ext = os.path.splitext(file.filename)[1]
                    filename = f"{uid}{ext}"
                    filepath = os.path.join(str(AVATAR_FOLDER), str(filename))
                    file.save(filepath)
                    user['avatar'] = filename
                    save_users(users)
                    return jsonify({
                        'message': 'Avatar uploaded successfully',
                        'user': {
                            'id': uid,
                            'username': user['username'],
                            'email': user['email'],
                            'avatar': user.get('avatar'),
                            'preferences': user.get('preferences', {}),
                            'created_at': user.get('created_at')
                        }
                    }), 200
                else:
                    return jsonify({'error': 'No selected file'}), 400
            # --- Improved avatar_url extraction and debug ---
            avatar_url = None
            # Try to get from form first
            if 'avatar_url' in request.form:
                avatar_url = request.form.get('avatar_url')
            # Try to get from JSON if not found in form
            if not avatar_url:
                try:
                    json_data = request.get_json(silent=True)
                except Exception:
                    json_data = None
                if json_data and 'avatar_url' in json_data:
                    avatar_url = json_data['avatar_url']
            # Debug prints
            print('DEBUG avatar upload:')
            print('request.form:', dict(request.form))
            try:
                print('request.json:', request.get_json(silent=True))
            except Exception as e:
                print('request.json: error', str(e))
            print('avatar_url:', avatar_url)
            # --- End debug ---
            if avatar_url:
                try:
                    r = requests.get(avatar_url, timeout=10)
                    if r.status_code == 200:
                        content_type = r.headers.get('Content-Type', '')
                        if 'image/svg+xml' in content_type or avatar_url.endswith('.svg'):
                            ext = '.svg'
                        elif 'image/png' in content_type or avatar_url.endswith('.png'):
                            ext = '.png'
                        elif 'image/jpeg' in content_type or avatar_url.endswith('.jpg') or avatar_url.endswith('.jpeg'):
                            ext = '.jpg'
                        else:
                            ext = '.png'  # Default fallback
                        filename = f"{uid}{ext}"
                        filepath = os.path.join(str(AVATAR_FOLDER), str(filename))
                        with open(filepath, 'wb') as f:
                            f.write(r.content)
                        user['avatar'] = filename
                        save_users(users)
                        return jsonify({
                            'message': 'Avatar set from URL',
                            'user': {
                                'id': uid,
                                'username': user['username'],
                                'email': user['email'],
                                'avatar': user.get('avatar'),
                                'preferences': user.get('preferences', {}),
                                'created_at': user.get('created_at')
                            }
                        }), 200
                    else:
                        return jsonify({'error': 'Failed to download avatar from URL'}), 400
                except Exception as e:
                    return jsonify({'error': f'Error downloading avatar: {str(e)}'}), 400
            return jsonify({'error': 'No avatar file or URL provided'}), 400
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/auth/avatar', methods=['GET'])
def get_avatar():
    email = request.args.get('email') or request.args.get('user')
    users = load_users()
    
    # If email is not provided, try to get from JWT
    if not email:
        try:
            from flask import g
            email = getattr(g, 'username', None)
        except Exception:
            email = None
    
    print(f"DEBUG avatar get: Looking for email: {email}")
    
    for uid, user in users.items():
        if user['email'].lower() == email.lower():
            avatar = user.get('avatar')
            print(f"DEBUG avatar get: Found user {uid}, avatar: {avatar}")
            if avatar:
                avatar_path = os.path.join(AVATAR_FOLDER, avatar)
                if os.path.exists(avatar_path):
                    # Add cache-busting headers to prevent browser caching
                    response = send_from_directory(AVATAR_FOLDER, avatar)
                    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response.headers['Pragma'] = 'no-cache'
                    response.headers['Expires'] = '0'
                    return response
                else:
                    print(f"DEBUG avatar get: Avatar file not found at {avatar_path}")
                    return jsonify({'error': 'Avatar file not found'}), 404
            else:
                print(f"DEBUG avatar get: No avatar set for user {uid}")
                return jsonify({'error': 'No avatar set'}), 404
    
    print(f"DEBUG avatar get: User not found for email: {email}")
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/auth/preferences', methods=['GET'])
@jwt_required
def get_preferences():
    email = g.username
    users = load_users()
    for uid, user in users.items():
        if user['email'].lower() == email.lower():
            return jsonify(user.get('preferences', {})), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/auth/preferences', methods=['PUT'])
@jwt_required
def update_preferences():
    email = g.username
    users = load_users()
    for uid, user in users.items():
        if user['email'].lower() == email.lower():
            data = request.get_json()
            user['preferences'] = data
            save_users(users)
            return jsonify({
                'message': 'Preferences updated',
                'user': {
                    'id': uid,
                    'username': user['username'],
                    'email': user['email'],
                    'avatar': user.get('avatar'),
                    'preferences': user.get('preferences', {}),
                    'created_at': user.get('created_at')
                }
            }), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/chat/history', methods=['GET'])
@jwt_required
def get_chat_history():
    """Get chat history for the authenticated user"""
    try:
        email = g.username
        chat_history = load_chat_history()
        user_chats = chat_history.get(email, [])
        return jsonify({'chats': user_chats}), 200
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return jsonify({'error': 'Failed to get chat history'}), 500

@app.route('/api/chat/history', methods=['POST'])
@jwt_required
def save_chat_history():
    """Save chat history for the authenticated user"""
    try:
        email = g.username
        data = request.get_json()
        session_id = data.get('sessionId')
        messages = data.get('messages', [])
        session_name = data.get('sessionName', '')
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        chat_history = load_chat_history()
        if email not in chat_history:
            chat_history[email] = []
        
        # Update existing session or create new one
        existing_session = None
        for session in chat_history[email]:
            if session.get('sessionId') == session_id:
                existing_session = session
                break
        
        if existing_session:
            existing_session['messages'] = messages
            existing_session['sessionName'] = session_name
            existing_session['updatedAt'] = datetime.now().isoformat()
        else:
            chat_history[email].append({
                'sessionId': session_id,
                'sessionName': session_name,
                'messages': messages,
                'createdAt': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat()
            })
        
        save_chat_history(chat_history)
        return jsonify({'message': 'Chat history saved successfully'}), 200
    except Exception as e:
        print(f"Error saving chat history: {e}")
        return jsonify({'error': 'Failed to save chat history'}), 500

@app.route('/api/chat/history/<session_id>', methods=['DELETE'])
@jwt_required
def delete_chat_session(session_id):
    """Delete a specific chat session"""
    try:
        email = g.username
        chat_history = load_chat_history()
        
        if email in chat_history:
            chat_history[email] = [session for session in chat_history[email] 
                                 if session.get('sessionId') != session_id]
            save_chat_history(chat_history)
        
        return jsonify({'message': 'Chat session deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting chat session: {e}")
        return jsonify({'error': 'Failed to delete chat session'}), 500

def cleanup_folders(output_path=None):
    folders = [
        os.path.join(UPLOAD_FOLDER, "templates"),
        os.path.join(UPLOAD_FOLDER, "content"),
        os.path.join(UPLOAD_FOLDER, "images"),
        os.path.join(UPLOAD_FOLDER, "converted"),
        SCREENSHOT_FOLDER  # Add screenshot folder to cleanup
    ]
    for folder in folders:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Error cleaning up {file_path}: {e}")

    if os.path.exists(OUTPUT_FOLDER) and output_path:
        for filename in os.listdir(OUTPUT_FOLDER):
            file_path = os.path.join(OUTPUT_FOLDER, filename)
            if file_path != output_path:
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Error cleaning up {file_path}: {e}")

def fetch_image(query):
    """Fetch a single Unsplash image URL for the given query using header auth.
    Returns a direct URL string or None on failure.
    """
    try:
        # Re-read API key in case env changed after startup
        api_key = (os.getenv("UNSPLASH_API_KEY") or UNSPLASH_API_KEY or "").strip()
        if not api_key:
            print("Unsplash API key missing")
            return None

        # Sanitize overly verbose prompts
        q = str(query or "").strip()
        q = re.sub(r"[\n\r]+", " ", q)
        q = re.sub(r"[\"'(){}\[\]:]", "", q)
        q = re.sub(r"\s+", " ", q)
        q = q[:120] or "abstract background"

        url = "https://api.unsplash.com/search/photos"
        headers = {
            "Authorization": f"Client-ID {api_key}",
            "Accept-Version": "v1",
        }
        params = {"query": q, "per_page": 1, "content_filter": "high"}
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        try:
            resp.raise_for_status()
        except Exception:
            print(f"Unsplash API error ({resp.status_code}) for query '{q}': {resp.text[:180]}")
            return None
        results = resp.json().get("results", [])
        if results:
            urls = results[0].get("urls", {})
            return urls.get("regular") or urls.get("full")
        return None
    except Exception as e:
        print(f"Error fetching image: {e}")
        return None

@app.route('/get-layouts', methods=['POST'])
def get_layouts():
    if 'template' not in request.files:
        return jsonify({"error": "Template file not found"}), 400
    template_file = request.files['template']
    if not template_file.filename.endswith('.pptx'):
        return jsonify({"error": "Template must be a .pptx file"}), 400
    from pptx import Presentation
    # Save template to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pptx') as tmp:
        template_path = tmp.name
        template_file.save(template_path)
    prs = Presentation(template_path)
    layouts = []
    for idx, layout in enumerate(prs.slide_layouts):
        name = layout.name if hasattr(layout, 'name') else f"Layout {idx}"
        layouts.append({"index": idx, "name": name})
    # Optionally: remove temp file
    try:
        os.remove(template_path)
    except Exception:
        pass
    return jsonify({"layouts": layouts}), 200

@app.route('/upload', methods=['POST'])
@jwt_required
def upload_files():
    print("Received request for /upload")
    if 'template' not in request.files and not request.form.get('template_name'):
        return jsonify({"error": "Template file or name is required"}), 400

    template_path = None
    if 'template' in request.files:
        template = request.files['template']
        if template and template.filename and template.filename.endswith('.pptx'):
            template_path = os.path.join(UPLOAD_FOLDER, 'templates', secure_filename(template.filename))
            template.save(template_path)
            print(f"Template saved to: {template_path}")
        else:
            return jsonify({"error": "Template must be a .pptx file"}), 400
    else:
        template_name = request.form.get('template_name')
        template_path = os.path.join(TEMPLATE_FOLDER, f"{template_name}.pptx")
        if not os.path.exists(template_path):
            return jsonify({"error": "Template not found"}), 400
        print(f"Using pre-defined template: {template_path}")

    content = request.files.get('content')
    content_path = None
    if content and content.filename:
        if content.filename.endswith(('.pptx', '.pdf', '.txt')):
            content_path = os.path.join(UPLOAD_FOLDER, 'content', secure_filename(content.filename))
            content.save(content_path)
            print(f"Content saved to: {content_path}")
        else:
            return jsonify({"error": "Content must be a .pptx, .pdf, or .txt file"}), 400
    else:
        return jsonify({"error": "Content file is required"}), 400

    output_path = None
    try:
        # Parse layout index from form; default 1
        try:
            layout_index = int(request.form.get('layout_index', '1'))
        except Exception:
            layout_index = 1

        output_path = generate_ppt(content_path, template_path, layout_index)
        if not output_path or not os.path.exists(output_path):
            raise Exception("Output PPT not created")
        print(f"Sending file: {output_path}")
        
        # Update dashboard data for conversion
        try:
            email = g.username
            users = load_users()
            user_id = None
            
            # Find user ID
            for uid, user in users.items():
                if user['email'].lower() == email.lower():
                    user_id = uid
                    break
            
            if user_id:
                # Add conversion to dashboard
                dashboard_data = load_dashboard_data()
                if user_id not in dashboard_data:
                    dashboard_data[user_id] = {}
                
                dashboard_data[user_id]['total_conversions'] = dashboard_data[user_id].get('total_conversions', 0) + 1
                # Total presentations = AI generations + conversions
                total_ai = dashboard_data[user_id].get('total_ai_generations', 0)
                total_conversions = dashboard_data[user_id]['total_conversions']
                dashboard_data[user_id]['total_presentations'] = total_ai + total_conversions
                save_dashboard_data(dashboard_data)
                
                # Add activity
                activity = {
                    'id': str(uuid.uuid4()),
                    'type': 'conversion',
                    'title': f'Converted: {os.path.basename(template_path)}',
                    'description': f'Converted template to new presentation',
                    'timestamp': datetime.utcnow().isoformat(),
                    'metadata': {'template': os.path.basename(template_path)}
                }
                
                user_activities = load_user_activities()
                if email not in user_activities:
                    user_activities[email] = []
                user_activities[email].append(activity)
                save_user_activities(user_activities)
                
        except Exception as e:
            print(f"Dashboard update error: {e}")
        
        from flask import send_file
        return send_file(os.path.abspath(output_path), as_attachment=True, download_name="generated_pptx.pptx")
    except Exception as e:
        import traceback
        print(f"[ERROR] Exception in /upload: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate PPT: {str(e)}"}), 500
    finally:
        try:
            cleanup_folders(output_path)
        except Exception as e:
            print(f"Cleanup error: {e}")

@app.route('/refine', methods=['POST'])
@jwt_required
def refine_files():
    print("Received request for /refine")
    if 'converted' not in request.files or 'content' not in request.files:
        print("[ERROR] Missing converted or content file in request.files")
        return jsonify({"error": "Both converted and content files are required"}), 400

    converted = request.files['converted']
    content = request.files['content']

    if not converted.filename.endswith('.pptx') or not content.filename.endswith(('.pptx', '.pdf', '.txt')):
        print(f"[ERROR] Invalid file types: converted={converted.filename}, content={content.filename}")
        return jsonify({"error": "Converted file must be .pptx, content can be .pptx, .pdf, or .txt"}), 400

    print(f"Converted file: {converted.filename}")
    print(f"Content file: {content.filename}")

    converted_path = os.path.join(UPLOAD_FOLDER, 'converted', secure_filename(converted.filename))
    content_path = os.path.join(UPLOAD_FOLDER, 'content', secure_filename(content.filename))
    os.makedirs(os.path.dirname(converted_path), exist_ok=True)
    converted.save(converted_path)
    content.save(content_path)
    print(f"Converted saved to: {converted_path}")
    print(f"Content saved to: {content_path}")

    output_path = None
    try:
        output_path = refine_ppt(converted_path, content_path, gemini_url(), GEMINI_API_KEY)
        print(f"Sending file: {output_path}")
        return send_from_directory(OUTPUT_FOLDER, os.path.basename(output_path), as_attachment=True, download_name="refined_pptx.pptx")
    except Exception as e:
        import traceback
        print(f"[ERROR] Exception in /refine: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Failed to refine PPT: {str(e)}"}), 500
    finally:
        cleanup_folders(output_path)

@app.route('/generate-ai-content', methods=['POST'])
def generate_ai_content():
    print("Received request for /generate-ai-content")
    topic = request.form.get('topic')
    if not topic:
        print("No topic provided")
        return jsonify({"error": "Topic is required"}), 400

    try:
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{
                    "text": f"Generate structured presentation content for the topic: {topic}. Include headings and bullet points for 4-6 slides, covering introduction, key points, case study/example, and conclusion."
                }]
            }]
        }
        response = requests.post(f"{gemini_url()}?key={GEMINI_API_KEY}", headers=headers, json=data)
        response.raise_for_status()
        api_response = response.json()

        content = api_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        if not content:
            return jsonify({"error": "No content generated by AI"}), 500

        content_filename = f"ai_content_{uuid.uuid4().hex[:8]}.txt"
        content_path = os.path.join(UPLOAD_FOLDER, 'content', content_filename)
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Robust image fetching
        import time
        time.sleep(1.2)
        
        image_url = fetch_image(topic)
        image_filename = f"slideimg_{uuid.uuid4().hex[:8]}.jpg" if image_url else None
        
        if image_url:
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
                img_resp = requests.get(image_url, headers=headers, timeout=45)
                if img_resp.status_code == 429:
                    time.sleep(3)
                    img_resp = requests.get(image_url, headers=headers, timeout=45)
                img_resp.raise_for_status()
                if len(img_resp.content) > 5000:
                    image_path = os.path.join(UPLOAD_FOLDER, 'images', image_filename)
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)
                    with open(image_path, 'wb') as f:
                        f.write(img_resp.content)
                else:
                    image_filename = None
            except Exception as e:
                print(f"Image fetch failed: {e}")
                image_filename = None

        return jsonify({
            "content_url": f"http://localhost:5000/get-content/{content_filename}",
            "image_url": f"http://localhost:5000/get-image/{image_filename}" if image_filename else None
        }), 200
    except Exception as e:
        print(f"Error in /generate-ai-content: {e}")
        return jsonify({"error": f"Failed to generate content: {str(e)}"}), 500

@app.route('/get-content/<filename>', methods=['GET'])
def get_content(filename):
    print(f"Received request for /get-content/{filename}")
    try:
        return send_from_directory(os.path.join(UPLOAD_FOLDER, 'content'), filename)
    except Exception as e:
        print(f"Error in /get-content: {e}")
        return jsonify({"error": f"Failed to fetch content: {str(e)}"}), 404

@app.route('/get-image/<filename>', methods=['GET'])
def get_image(filename):
    print(f"Received request for /get-image/{filename}")
    try:
        return send_from_directory(os.path.join(UPLOAD_FOLDER, 'images'), filename)
    except Exception as e:
        print(f"Error in /get-image: {e}")
        return jsonify({"error": "Image not found"}), 404

@app.route('/get-ppt/<filename>', methods=['GET'])
def get_ppt(filename):
    print(f"Received request for /get-ppt/{filename}")
    try:
        return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True, download_name="generated_pptx.pptx")
    except Exception as e:
        print(f"Error in /get-ppt: {e}")
        return jsonify({"error": "PPT not found"}), 404

@app.route('/get-templates', methods=['GET'])
def get_templates():
    print("Received request for /get-templates")
    try:
        templates = [f for f in os.listdir(TEMPLATE_FOLDER) if f.endswith('.pptx')]
        return jsonify({"templates": templates}), 200
    except Exception as e:
        print(f"Error in /get-templates: {e}")
        return jsonify({"error": f"Failed to fetch templates: {str(e)}"}), 500

@app.route('/api/templates', methods=['GET'])
def get_all_templates():
    """Get all available templates with metadata"""
    try:
        print("Received request for /api/templates")
        
        # Sample popular templates data
        popular_templates = [
            {
                "id": "1",
                "name": "Modern Business",
                "category": "Business",
                "description": "Professional business presentation template with modern design",
                "thumbnail": "https://images.pexels.com/photos/7688336/pexels-photo-7688336.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
                "downloads": 1245,
                "rating": 4.8,
                "slides_count": 12,
                "file_size": "2.3 MB",
                "tags": ["business", "professional", "modern"],
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "id": "2", 
                "name": "Creative Portfolio",
                "category": "Creative",
                "description": "Eye-catching portfolio template for creative professionals",
                "thumbnail": "https://images.pexels.com/photos/3184465/pexels-photo-3184465.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
                "downloads": 892,
                "rating": 4.9,
                "slides_count": 8,
                "file_size": "1.8 MB",
                "tags": ["portfolio", "creative", "design"],
                "created_at": "2024-01-20T14:15:00Z"
            },
            {
                "id": "3",
                "name": "Data Analytics",
                "category": "Analytics",
                "description": "Data-driven presentation template with charts and graphs",
                "thumbnail": "https://images.pexels.com/photos/590022/pexels-photo-590022.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
                "downloads": 756,
                "rating": 4.7,
                "slides_count": 15,
                "file_size": "3.1 MB",
                "tags": ["analytics", "data", "charts"],
                "created_at": "2024-01-25T09:45:00Z"
            },
            {
                "id": "4",
                "name": "Education Lecture",
                "category": "Education",
                "description": "Academic presentation template for educational content",
                "thumbnail": "https://images.pexels.com/photos/5905709/pexels-photo-5905709.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
                "downloads": 634,
                "rating": 4.6,
                "slides_count": 10,
                "file_size": "2.0 MB",
                "tags": ["education", "academic", "lecture"],
                "created_at": "2024-02-01T11:20:00Z"
            },
            {
                "id": "5",
                "name": "Startup Pitch",
                "category": "Business",
                "description": "Dynamic startup pitch deck template",
                "thumbnail": "https://images.pexels.com/photos/3183150/pexels-photo-3183150.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
                "downloads": 567,
                "rating": 4.5,
                "slides_count": 14,
                "file_size": "2.7 MB",
                "tags": ["startup", "pitch", "business"],
                "created_at": "2024-02-05T16:30:00Z"
            },
            {
                "id": "6",
                "name": "Marketing Campaign",
                "category": "Marketing",
                "description": "Marketing campaign presentation template",
                "thumbnail": "https://images.pexels.com/photos/3183153/pexels-photo-3183153.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
                "downloads": 445,
                "rating": 4.4,
                "slides_count": 11,
                "file_size": "2.2 MB",
                "tags": ["marketing", "campaign", "advertising"],
                "created_at": "2024-02-10T13:45:00Z"
            }
        ]
        
        # Get query parameters for filtering
        category = request.args.get('category')
        search = request.args.get('search')
        sort_by = request.args.get('sort_by', 'downloads')  # downloads, rating, created_at
        limit = int(request.args.get('limit', 10))
        
        # Filter templates
        filtered_templates = popular_templates
        
        if category:
            filtered_templates = [t for t in filtered_templates if t['category'].lower() == category.lower()]
        
        if search:
            search_lower = search.lower()
            filtered_templates = [t for t in filtered_templates if 
                                search_lower in t['name'].lower() or 
                                search_lower in t['description'].lower() or
                                any(search_lower in tag.lower() for tag in t['tags'])]
        
        # Sort templates
        if sort_by == 'downloads':
            filtered_templates.sort(key=lambda x: x['downloads'], reverse=True)
        elif sort_by == 'rating':
            filtered_templates.sort(key=lambda x: x['rating'], reverse=True)
        elif sort_by == 'created_at':
            filtered_templates.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Apply limit
        filtered_templates = filtered_templates[:limit]
        
        return jsonify({
            'templates': filtered_templates,
            'total': len(filtered_templates),
            'categories': list(set(t['category'] for t in popular_templates))
        }), 200
        
    except Exception as e:
        print(f"Error in /api/templates: {e}")
        return jsonify({"error": f"Failed to fetch templates: {str(e)}"}), 500

@app.route('/api/templates/popular', methods=['GET'])
def get_popular_templates():
    """Get popular templates (top 6 by downloads)"""
    try:
        print("Received request for /api/templates/popular")
        
        # Sample popular templates data
        popular_templates = [
            {
                "id": "1",
                "name": "Modern Business",
                "category": "Business",
                "description": "Professional business presentation template with modern design",
                "thumbnail": "https://images.pexels.com/photos/7688336/pexels-photo-7688336.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
                "downloads": 1245,
                "rating": 4.8,
                "slides_count": 12,
                "file_size": "2.3 MB",
                "tags": ["business", "professional", "modern"],
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "id": "2", 
                "name": "Creative Portfolio",
                "category": "Creative",
                "description": "Eye-catching portfolio template for creative professionals",
                "thumbnail": "https://images.pexels.com/photos/3184465/pexels-photo-3184465.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
                "downloads": 892,
                "rating": 4.9,
                "slides_count": 8,
                "file_size": "1.8 MB",
                "tags": ["portfolio", "creative", "design"],
                "created_at": "2024-01-20T14:15:00Z"
            },
            {
                "id": "3",
                "name": "Data Analytics",
                "category": "Analytics",
                "description": "Data-driven presentation template with charts and graphs",
                "thumbnail": "https://images.pexels.com/photos/590022/pexels-photo-590022.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
                "downloads": 756,
                "rating": 4.7,
                "slides_count": 15,
                "file_size": "3.1 MB",
                "tags": ["analytics", "data", "charts"],
                "created_at": "2024-01-25T09:45:00Z"
            },
            {
                "id": "4",
                "name": "Education Lecture",
                "category": "Education",
                "description": "Academic presentation template for educational content",
                "thumbnail": "https://images.pexels.com/photos/5905709/pexels-photo-5905709.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
                "downloads": 634,
                "rating": 4.6,
                "slides_count": 10,
                "file_size": "2.0 MB",
                "tags": ["education", "academic", "lecture"],
                "created_at": "2024-02-01T11:20:00Z"
            },
            {
                "id": "5",
                "name": "Startup Pitch",
                "category": "Business",
                "description": "Dynamic startup pitch deck template",
                "thumbnail": "https://images.pexels.com/photos/3183150/pexels-photo-3183150.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
                "downloads": 567,
                "rating": 4.5,
                "slides_count": 14,
                "file_size": "2.7 MB",
                "tags": ["startup", "pitch", "business"],
                "created_at": "2024-02-05T16:30:00Z"
            },
            {
                "id": "6",
                "name": "Marketing Campaign",
                "category": "Marketing",
                "description": "Marketing campaign presentation template",
                "thumbnail": "https://images.pexels.com/photos/3183153/pexels-photo-3183153.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
                "downloads": 445,
                "rating": 4.4,
                "slides_count": 11,
                "file_size": "2.2 MB",
                "tags": ["marketing", "campaign", "advertising"],
                "created_at": "2024-02-10T13:45:00Z"
            }
        ]
        
        # Sort by downloads and return top 6
        popular_templates.sort(key=lambda x: x['downloads'], reverse=True)
        top_templates = popular_templates[:6]
        
        return jsonify({
            'templates': top_templates,
            'total': len(top_templates)
        }), 200
        
    except Exception as e:
        print(f"Error in /api/templates/popular: {e}")
        return jsonify({"error": f"Failed to fetch popular templates: {str(e)}"}), 500

@app.route('/api/templates/<template_id>', methods=['GET'])
def get_template_details(template_id):
    """Get detailed information about a specific template"""
    try:
        print(f"Received request for template details: {template_id}")
        
        # Sample template details
        template_details = {
            "1": {
                "id": "1",
                "name": "Modern Business",
                "category": "Business",
                "description": "Professional business presentation template with modern design elements. Perfect for corporate meetings, client presentations, and business proposals.",
                "long_description": "This modern business template features clean typography, professional color schemes, and well-structured layouts. It includes 12 carefully designed slides covering all aspects of business presentations including executive summary, market analysis, financial projections, and strategic planning.",
                "thumbnail": "https://images.pexels.com/photos/7688336/pexels-photo-7688336.jpeg?auto=compress&cs=tinysrgb&w=400&h=300",
                "preview_images": [
                    "https://images.pexels.com/photos/7688336/pexels-photo-7688336.jpeg?auto=compress&cs=tinysrgb&w=800&h=600",
                    "https://images.pexels.com/photos/3184465/pexels-photo-3184465.jpeg?auto=compress&cs=tinysrgb&w=800&h=600",
                    "https://images.pexels.com/photos/590022/pexels-photo-590022.jpeg?auto=compress&cs=tinysrgb&w=800&h=600"
                ],
                "downloads": 1245,
                "rating": 4.8,
                "reviews_count": 89,
                "slides_count": 12,
                "file_size": "2.3 MB",
                "tags": ["business", "professional", "modern", "corporate"],
                "features": ["Responsive design", "Professional color scheme", "Easy customization", "High-quality graphics"],
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-02-15T14:20:00Z",
                "author": "PPTCon Team",
                "compatibility": ["PowerPoint 2016+", "Google Slides", "Keynote"],
                "license": "Free for commercial use"
            }
        }
        
        template = template_details.get(template_id)
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        return jsonify(template), 200
        
    except Exception as e:
        print(f"Error in /api/templates/{template_id}: {e}")
        return jsonify({"error": f"Failed to fetch template details: {str(e)}"}), 500

@app.route('/api/templates/<template_id>/download', methods=['POST'])
@jwt_required
def download_template(template_id):
    """Download a template and track usage"""
    try:
        print(f"Received download request for template: {template_id}")
        email = g.username
        
        # Track template usage in dashboard
        try:
            users = load_users()
            user_id = None
            
            # Find user ID
            for uid, user in users.items():
                if user['email'].lower() == email.lower():
                    user_id = uid
                    break
            
            if user_id:
                # Update dashboard data
                dashboard_data = load_dashboard_data()
                if user_id not in dashboard_data:
                    dashboard_data[user_id] = {}
                
                dashboard_data[user_id]['templates_used'] = dashboard_data[user_id].get('templates_used', 0) + 1
                save_dashboard_data(dashboard_data)
                
                # Add activity
                activity = {
                    'id': str(uuid.uuid4()),
                    'type': 'template_downloaded',
                    'title': f'Downloaded template: {template_id}',
                    'description': f'Downloaded template for use',
                    'timestamp': datetime.utcnow().isoformat(),
                    'metadata': {'template_id': template_id}
                }
                
                user_activities = load_user_activities()
                if email not in user_activities:
                    user_activities[email] = []
                user_activities[email].append(activity)
                save_user_activities(user_activities)
                
        except Exception as e:
            print(f"Dashboard update error: {e}")
        
        # For now, return a sample template file or redirect
        # In production, you would serve the actual template file
        return jsonify({
            'message': 'Template download initiated',
            'template_id': template_id,
            'download_url': f'/api/templates/{template_id}/file'
        }), 200
        
    except Exception as e:
        print(f"Error in template download: {e}")
        return jsonify({"error": f"Failed to download template: {str(e)}"}), 500
@app.route('/generate-ppt-ai', methods=['POST'])
@jwt_required
def generate_ppt_ai():
    print("Received request for /generate-ppt-ai")
    topic = request.form.get("topic")
    template = request.files.get("template")
    # Get layout index from form (frontend should send it)
    layout_index = request.form.get("layout_index")
    if layout_index is not None:
        try:
            layout_index = int(layout_index)
        except Exception:
            layout_index = None
    if not topic or not template:
        return jsonify({"error": "Both topic and template PPTX are required."}), 400

    # Save template
    template_path = os.path.join(UPLOAD_FOLDER, "templates", f"ai_template_{uuid.uuid4().hex[:8]}.pptx")
    template.save(template_path)

    # AI se slides content lao (Gemini API call with retry + fallback)
    slides = None
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{
                "text": f"""
Create a detailed PowerPoint presentation on the topic: '{topic}'.\nFor each slide, give:\n- title\n- 3-6 bullet points\n- a relevant image description (for DALL-E/Unsplash)\n- a recommended layout (e.g. image left, text right, infographic, full image, etc.)\n- a color theme (optional)\n\nReply ONLY as JSON array:\n[{{{{\"title\": \"\", \"bullets\": [\"\", \"\", ...], \"image_desc\": \"\", \"layout\": \"\", \"theme\": [\"#003087\", \"#FFFFFF\"]}}}}]"""
            }]
        }]
    }
    for attempt in range(3):
        try:
            if not GEMINI_API_KEY:
                raise RuntimeError("Missing GEMINI_API_KEY")
            url = f"{gemini_url()}?key={GEMINI_API_KEY}"
            # If we know 2.0-flash failed before or we are on attempt > 0, try 2.5-flash (more stable)
            if attempt > 0 and ("2.0" in url or "1.5" in url):
                 url = url.replace("gemini-2.0-flash", "gemini-2.5-flash").replace("gemini-1.5-flash", "gemini-2.5-flash")
            
            response = requests.post(
                url, headers=headers, json=data, timeout=60
            )
            print(f"Gemini API ({url.split('/')[-1].split(':')[0]}) status:", response.status_code)
            
            if response.status_code == 429 or response.status_code == 404:
                # Quota or Not Found - definitely try 2.5-flash on next attempt
                if "gemini-2.5-flash" not in url:
                    print(f"⚠️ Model {url} failed ({response.status_code}). Retrying with 2.5-Flash...")
                    time.sleep(1)
                    continue
                else:
                    raise RuntimeError(f"Gemini {response.status_code}: {response.text[:200]}")

            if response.status_code >= 500:
                raise RuntimeError(f"Gemini {response.status_code}")
            
            # Successful response
            response.raise_for_status()
            api_response = response.json()
            gemini_text = api_response['candidates'][0]['content']['parts'][0]['text']
            cleaned = re.sub(r"^```json\\n|^```json|^```|```$", "", gemini_text.strip(), flags=re.MULTILINE).strip()
            slides = json.loads(cleaned)
            break
        except Exception as e:
            print(f"AI attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
            else:
                # Fallback minimal slides (5)
                slides = [{
                    "title": f"{topic} - Slide {i+1}",
                    "bullets": ["Point 1", "Point 2", "Point 3"],
                    "image_desc": topic,
                    "layout": "title-content",
                    "theme": ["#003087", "#FFFFFF"]
                } for i in range(5)]
    if not slides:
        return jsonify({"error": "AI failed to generate slides"}), 500

    # Gamma style PPT generation (image, layout, theme)
    from utils.ppt_processor import generate_gamma_style_ppt
    output_path = generate_gamma_style_ppt(slides, template_path=template_path, layout_index=layout_index)

    # Update dashboard data
    try:
        email = g.username
        users = load_users()
        user_id = None
        # Find user ID
        for uid, user in users.items():
            if user['email'].lower() == email.lower():
                user_id = uid
                break
        if user_id:
            # Add presentation to dashboard
            presentation_data = {
                'title': topic,
                'filename': os.path.basename(output_path),
                'slides_count': len(slides),
                'template_used': 'Gamma Style AI',
                'file_size': os.path.getsize(output_path) if os.path.exists(output_path) else 0
            }
            dashboard_data = load_dashboard_data()
            if user_id not in dashboard_data:
                dashboard_data[user_id] = {}
            if 'presentations' not in dashboard_data[user_id]:
                dashboard_data[user_id]['presentations'] = []
            presentation = {
                'id': str(uuid.uuid4()),
                'title': presentation_data['title'],
                'filename': presentation_data['filename'],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'slides_count': presentation_data['slides_count'],
                'template_used': presentation_data['template_used'],
                'file_size': presentation_data['file_size']
            }
            dashboard_data[user_id]['presentations'].append(presentation)
            # Total presentations = AI generations + conversions
            total_ai = dashboard_data[user_id].get('total_ai_generations', 0) + 1
            total_conversions = dashboard_data[user_id].get('total_conversions', 0)
            dashboard_data[user_id]['total_ai_generations'] = total_ai
            dashboard_data[user_id]['total_presentations'] = total_ai + total_conversions
            save_dashboard_data(dashboard_data)
            # Add activity
            activity = {
                'id': str(uuid.uuid4()),
                'type': 'presentation_created',
                'title': f'Generated: {topic}',
                'description': f'Created Gamma-style AI presentation with {presentation_data["slides_count"]} slides',
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': {'presentation_id': presentation['id']}
            }
            user_activities = load_user_activities()
            if email not in user_activities:
                user_activities[email] = []
            user_activities[email].append(activity)
            save_user_activities(user_activities)
    except Exception as e:
        print(f"Dashboard update error: {e}")

    return send_from_directory(OUTPUT_FOLDER, os.path.basename(output_path), as_attachment=True, download_name="generated_ai_pptx.pptx")

@app.route('/generate-ppt-ai-enhanced', methods=['POST'])
@jwt_required
def generate_ppt_ai_enhanced():
    print("Received request for /generate-ppt-ai-enhanced")
    topic = request.form.get("topic")
    prompt_description = request.form.get("prompt_description", "").strip()
    template = request.files.get("template")
    num_slides = request.form.get("num_slides", "5")  # Default 5 slides
    layout_preference = request.form.get("layout_preference", "auto")  # auto, title-content, image-left, etc.
    template_name = request.form.get("template_name")
    
    try:
        num_slides = int(num_slides)
        if num_slides < 1 or num_slides > 20:
            return jsonify({"error": "Number of slides must be between 1 and 20"}), 400
    except ValueError:
        return jsonify({"error": "Invalid number of slides"}), 400
    
    if not topic:
        return jsonify({"error": "Topic is required."}), 400

    # Determine template path: uploaded file OR pre-existing template by name
    template_path = None
    if template:
        template_path = os.path.join(UPLOAD_FOLDER, "templates", f"ai_template_{uuid.uuid4().hex[:8]}.pptx")
        template.save(template_path)
    elif template_name:
        candidate_path = os.path.join(TEMPLATE_FOLDER, template_name)
        if os.path.exists(candidate_path) and candidate_path.lower().endswith('.pptx'):
            template_path = candidate_path
        else:
            return jsonify({"error": "Template not found on server."}), 400
    else:
        return jsonify({"error": "Please upload a template file or select a template from the list."}), 400

    # Enhanced AI prompt with number of slides and layout preference
    layout_instructions = {
        "auto": "Choose the best layout for each slide automatically from: title-content, image-left, image-right, full-image, two-column",
        "title-content": "Use 'title-content' layout for all content slides",
        "image-left": "Use 'image-left' layout (image on left side, text on right side) for all content slides",
        "image-right": "Use 'image-right' layout (image on right side, text on left side) for all content slides",
        "full-image": "Use 'full-image' layout (full background image with text overlay) for all content slides",
        "two-column": "Use 'two-column' layout (text split into two columns) for all content slides"
    }
    
    layout_instruction = layout_instructions.get(layout_preference, layout_instructions["auto"])

    # Map user-facing layout values to exact values our PPT processor expects
    layout_value_map = {
        "auto": "auto",
        "title-content": "title-content",
        "image-left": "image-left",
        "image-right": "image-right",
        "full-image": "full-image",
        "two-column": "two-column"
    }
    layout_value_for_prompt = layout_value_map.get(layout_preference, "auto")

    user_instructions = ""
    if prompt_description:
        user_instructions = f"\nUSER'S SPECIFIC INSTRUCTIONS FOR CONTENT:\n\"\"\"{prompt_description}\"\"\"\nYou MUST adhere strictly to these instructions while writing the content.\n"

    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{
            "parts": [{
                "text": f"""You are a professional presentation content writer. Create a detailed, information-rich PowerPoint presentation on the topic: '{topic}' with EXACTLY {num_slides} slides.
{user_instructions}
CRITICAL RULES FOR CONTENT:
1. Each bullet point MUST be a complete, descriptive sentence of 15-25 words. NOT short phrases or keywords.
2. Each slide MUST have exactly 4-5 bullet points.
3. The first slide should be a title/introduction slide with overview points.
4. The last slide should be a conclusion/summary slide.
5. Middle slides should cover different sub-topics in depth with facts and examples.

CRITICAL RULES FOR IMAGE DESCRIPTIONS:
- The "image_desc" field is used to search stock photos on Unsplash.
- Use simple, concrete, 2-4 word photo search terms like: "business meeting", "data analytics dashboard", "students classroom", "technology circuit board", "medical research lab"
- Do NOT use abstract or complex phrases. Think like you are searching Google Images.
- Each slide should have a DIFFERENT image description relevant to that specific slide content.

LAYOUT RULES:
- For the first slide (title/intro), use layout: "title-content"
- For content slides: {layout_instruction}
- Valid layout values are EXACTLY one of: "title-content", "image-left", "image-right", "full-image", "two-column"
- If preference is auto, choose the most appropriate layout for each slide.

COLOR THEME:
- Provide 2 complementary hex colors. First color is primary (darker), second is accent/background (lighter).
- Keep colors professional and consistent across all slides.

Reply ONLY with a valid JSON array containing EXACTLY {num_slides} objects. No markdown, no explanation, no code fences, just the raw JSON array:
[{{"title": "Slide Title Here", "bullets": ["Full descriptive sentence about point 1 that explains the concept clearly.", "Another complete sentence explaining point 2 with sufficient detail and context."], "image_desc": "simple search term", "layout": "{layout_value_for_prompt}", "theme": ["#1a365d", "#e2e8f0"]}}]"""
            }]
        }]
    }
    # Retry loop + fallback
    slides = None
    for attempt in range(3):
        try:
            if not GEMINI_API_KEY:
                raise RuntimeError("Missing GEMINI_API_KEY")
            response = requests.post(
                f"{gemini_url()}?key={GEMINI_API_KEY}", headers=headers, json=data, timeout=60
            )
            print("Gemini API status:", response.status_code)
            if response.status_code >= 500:
                raise RuntimeError(f"Gemini {response.status_code}")
            print("Gemini API response (first 500 chars):", response.text[:500])
            response.raise_for_status()
            api_response = response.json()
            gemini_text = api_response['candidates'][0]['content']['parts'][0]['text']
            # Clean markdown code fences that Gemini sometimes adds
            cleaned = gemini_text.strip()
            cleaned = re.sub(r"^```json\s*\n?", "", cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r"^```\s*\n?", "", cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r"\n?```\s*$", "", cleaned, flags=re.MULTILINE)
            cleaned = cleaned.strip()
            candidate_slides = json.loads(cleaned)
            # Validate and normalize layout values
            valid_layouts = {"title-content", "image-left", "image-right", "full-image", "two-column"}
            for s in candidate_slides:
                raw_layout = str(s.get("layout", "")).strip().lower()
                # Normalize common Gemini variations
                layout_normalize = {
                    "title content": "title-content",
                    "image left": "image-left",
                    "image left, text right": "image-left",
                    "image right": "image-right",
                    "image right, text left": "image-right",
                    "text left, image right": "image-right",
                    "text right, image left": "image-left",
                    "full image": "full-image",
                    "full_image": "full-image",
                    "two column": "two-column",
                    "two_column": "two-column",
                    "two columns": "two-column",
                    "title_content": "title-content",
                    "image_left": "image-left",
                    "image_right": "image-right",
                    "title slide": "title-content",
                    "title": "title-content",
                    "content": "title-content",
                    "infographic": "two-column",
                }
                normalized = layout_normalize.get(raw_layout, raw_layout)
                if normalized not in valid_layouts:
                    normalized = layout_value_for_prompt if layout_value_for_prompt != "auto" else "title-content"
                s["layout"] = normalized
            slides = candidate_slides
            print(f"Successfully parsed {len(slides)} slides from Gemini")
            break
        except Exception as e:
            print(f"AI attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    if not slides:
        # Fallback: generate placeholder slides matching requested count
        slides = [{
            "title": f"{topic} - Slide {i+1}",
            "bullets": ["Point 1", "Point 2", "Point 3"],
            "image_desc": topic,
            "layout": layout_preference,
            "theme": ["#003087", "#FFFFFF"]
        } for i in range(num_slides)]
    # Ensure exact count
    if len(slides) > num_slides:
        slides = slides[:num_slides]
    while len(slides) < num_slides:
        slides.append({
            "title": f"Additional Slide {len(slides) + 1}",
            "bullets": ["Content to be added"],
            "image_desc": topic,
            "layout": layout_preference,
            "theme": ["#003087", "#FFFFFF"]
        })

    # Enhanced PPT generation with better layout handling
    from utils.ppt_processor import generate_enhanced_ppt
    output_path = generate_enhanced_ppt(slides, template_path=template_path, layout_preference=layout_preference)

    # Update dashboard data
    try:
        email = g.username
        users = load_users()
        user_id = None
        # Find user ID
        for uid, user in users.items():
            if user['email'].lower() == email.lower():
                user_id = uid
                break
        if user_id:
            # Add presentation to dashboard
            presentation_data = {
                'title': topic,
                'filename': os.path.basename(output_path),
                'slides_count': len(slides),
                'template_used': f'Enhanced AI ({layout_preference})',
                'file_size': os.path.getsize(output_path) if os.path.exists(output_path) else 0
            }
            dashboard_data = load_dashboard_data()
            if user_id not in dashboard_data:
                dashboard_data[user_id] = {}
            if 'presentations' not in dashboard_data[user_id]:
                dashboard_data[user_id]['presentations'] = []
            presentation = {
                'id': str(uuid.uuid4()),
                'title': presentation_data['title'],
                'filename': presentation_data['filename'],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'slides_count': presentation_data['slides_count'],
                'template_used': presentation_data['template_used'],
                'file_size': presentation_data['file_size']
            }
            dashboard_data[user_id]['presentations'].append(presentation)
            # Total presentations = AI generations + conversions
            total_ai = dashboard_data[user_id].get('total_ai_generations', 0) + 1
            total_conversions = dashboard_data[user_id].get('total_conversions', 0)
            dashboard_data[user_id]['total_ai_generations'] = total_ai
            dashboard_data[user_id]['total_presentations'] = total_ai + total_conversions
            save_dashboard_data(dashboard_data)
            # Add activity
            activity = {
                'id': str(uuid.uuid4()),
                'type': 'presentation_created',
                'title': f'Generated: {topic} ({num_slides} slides)',
                'description': f'Created enhanced AI presentation with {num_slides} slides using {layout_preference} layout',
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': {'presentation_id': presentation['id']}
            }
            user_activities = load_user_activities()
            if email not in user_activities:
                user_activities[email] = []
            user_activities[email].append(activity)
            save_user_activities(user_activities)
    except Exception as e:
        print(f"Dashboard update error: {e}")

    return send_from_directory(OUTPUT_FOLDER, os.path.basename(output_path), as_attachment=True, download_name="enhanced_ai_pptx.pptx")

@app.route('/contact', methods=['POST'])
def contact():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    subject = data.get('subject')
    message = data.get('message')

    # Email config (now using .env variables)
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    receiver_email = os.getenv("EMAIL_RECEIVER")

    email_subject = f"Contact Form: {subject or 'No Subject'}"
    
    # Professional HTML email template
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset=\"UTF-8\">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            .email-container {{
                background-color: #ffffff;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 25px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }}
            .field {{
                margin-bottom: 20px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
                border-left: 4px solid #667eea;
            }}
            .field-label {{
                font-weight: 600;
                color: #495057;
                margin-bottom: 5px;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .field-value {{
                color: #212529;
                font-size: 16px;
                margin: 0;
            }}
            .message-field {{
                background-color: #e3f2fd;
                border-left-color: #2196f3;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
                text-align: center;
                color: #6c757d;
                font-size: 14px;
            }}
            .timestamp {{
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
                text-align: center;
                margin-top: 20px;
                font-size: 12px;
                color: #6c757d;
            }}
        </style>
    </head>
    <body>
        <div class=\"email-container\">
            <div class=\"header\">
                <h1>📧 New Contact Form Submission</h1>
            </div>
            <div class=\"field\">
                <div class=\"field-label\">👤 Name</div>
                <div class=\"field-value\">{name}</div>
            </div>
            <div class=\"field\">
                <div class=\"field-label\">📧 Email Address</div>
                <div class=\"field-value\">{email}</div>
            </div>
            <div class=\"field\">
                <div class=\"field-label\">📝 Subject</div>
                <div class=\"field-value\">{subject}</div>
            </div>
            <div class=\"field message-field\">
                <div class=\"field-label\">💬 Message</div>
                <div class=\"field-value\">{message.replace(chr(10), '<br>')}</div>
            </div>
            <div class=\"timestamp\">
                📅 Sent on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </div>
            <div class=\"footer\">
                <p>This message was sent from your website's contact form.</p>
                <p>💼 Professional Contact Management System</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Create MIME message with HTML content
    msg = MIMEMultipart('alternative')
    msg['Subject'] = email_subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # Attach HTML content
    html_part = MIMEText(html_body, 'html')
    msg.attach(html_part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return {'message': 'Message sent successfully!'}, 200
    except Exception as e:
        print("Email send error:", e)
        return {'error': 'Failed to send message.'}, 500

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json()
    feedback_type = data.get('type')
    email = data.get('email')
    subject = data.get('subject')
    message = data.get('message')
    rating = data.get('rating')

    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    receiver_email = os.getenv("EMAIL_RECEIVER")

    email_subject = f"Feedback Form: {subject or 'No Subject'}"
    
    # Professional HTML email template for feedback
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            .email-container {{
                background-color: #ffffff;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 25px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }}
            .field {{
                margin-bottom: 20px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
                border-left: 4px solid #ff6b6b;
            }}
            .field-label {{
                font-weight: 600;
                color: #495057;
                margin-bottom: 5px;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .field-value {{
                color: #212529;
                font-size: 16px;
                margin: 0;
            }}
            .rating-field {{
                background-color: #fff3cd;
                border-left-color: #ffc107;
            }}
            .message-field {{
                background-color: #e3f2fd;
                border-left-color: #2196f3;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
                text-align: center;
                color: #6c757d;
                font-size: 14px;
            }}
            .timestamp {{
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
                text-align: center;
                margin-top: 20px;
                font-size: 12px;
                color: #6c757d;
            }}
            .stars {{
                color: #ffc107;
                font-size: 18px;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>⭐ New Feedback Submission</h1>
            </div>
            
            <div class="field">
                <div class="field-label">📋 Feedback Type</div>
                <div class="field-value">{feedback_type}</div>
            </div>
            
            <div class="field">
                <div class="field-label">📧 Email Address</div>
                <div class="field-value">{email}</div>
            </div>
            
            <div class="field">
                <div class="field-label">📝 Subject</div>
                <div class="field-value">{subject}</div>
            </div>
            
            <div class="field rating-field">
                <div class="field-label">⭐ Rating</div>
                <div class="field-value">
                    <span class="stars">{'★' * int(rating) if rating else 'No rating'}</span>
                    {f' ({rating}/5)' if rating else ''}
                </div>
            </div>
            
            <div class="field message-field">
                <div class="field-label">💬 Feedback Message</div>
                <div class="field-value">{message.replace(chr(10), '<br>')}</div>
            </div>
            
            <div class="timestamp">
                📅 Sent on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </div>
            
            <div class="footer">
                <p>This feedback was submitted from your website's feedback form.</p>
                <p>💼 Professional Feedback Management System</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Create MIME message with HTML content
    msg = MIMEMultipart('alternative')
    msg['Subject'] = email_subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # Attach HTML content
    html_part = MIMEText(html_body, 'html')
    msg.attach(html_part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return {'message': 'Feedback sent successfully!'}, 200
    except Exception as e:
        print("Feedback email send error:", e)
        return {'error': 'Failed to send feedback.'}, 500

@app.route('/chatbot', methods=['OPTIONS'])
def chatbot_options():
    # Explicitly handle CORS preflight for the chatbot endpoint
    resp = make_response(('', 200))
    origin = request.headers.get('Origin')
    if origin and origin in ["http://localhost:5173", "http://localhost:8080"]:
        resp.headers['Access-Control-Allow-Origin'] = origin
    else:
        resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    return resp


@app.route('/chatbot', methods=['POST'])
def chatbot():
    try:
        # Try to verify JWT if provided, but don't block requests when token is missing/invalid
        auth_header = request.headers.get('Authorization', '')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
            username = verify_jwt(token)
            if username:
                g.username = username

        data = request.get_json()
        user_message = data.get('message', '').lower()
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Check if Gemini API key is available
        if not GEMINI_API_KEY or GEMINI_API_KEY == 'your_gemini_api_key_here':
            # Fallback responses when API key is not available
            fallback_responses = {
                'presentation': 'Great question! For creating effective presentations, focus on: 1) Clear structure with introduction, main points, and conclusion 2) Use bullet points and visuals 3) Keep text minimal and readable 4) Use consistent design themes 5) Practice your delivery. Would you like specific tips for any of these areas?',
                'powerpoint': 'PowerPoint tips: Use the 10-20-30 rule (10 slides, 20 minutes, 30pt font minimum). Choose readable fonts like Arial or Calibri. Use high contrast colors. Include relevant images and charts. Keep animations simple and purposeful. What specific aspect would you like to know more about?',
                'slide': 'For better slides: 1) One main idea per slide 2) Use visuals over text 3) Maintain consistent formatting 4) Use white space effectively 5) Include a clear call-to-action. Need help with slide design or content structure?',
                'design': 'Design principles: Use a consistent color scheme (2-3 colors max), maintain visual hierarchy, use quality images, keep layouts clean and uncluttered, ensure good contrast for readability. What type of presentation are you working on?',
                'content': 'Content tips: Start with a compelling hook, organize information logically, use stories and examples, include data when relevant, end with a strong conclusion. What topic are you presenting on?',
                'help': 'I can help you with: Creating presentations, PowerPoint tips, slide design, content structure, and presentation best practices. What would you like to know more about?',
                'hello': 'Hello! I\'m your AI presentation assistant for PPTCon. I can help you create better presentations, give design tips, and provide content suggestions. What would you like to work on today?',
                'hi': 'Hi there! Ready to create amazing presentations with PPTCon? I can help with design tips, content structure, and PowerPoint best practices. What\'s your presentation topic?',
                
                # Multilingual Personal Questions - Who Made You
                'who made you': 'I\'m an AI assistant for PPTCon, a PowerPoint presentation app created by AryamanNiboriya. I\'m here to help you create amazing presentations!',
                'who created you': 'I\'m an AI assistant for PPTCon, a PowerPoint presentation app created by AryamanNiboriya. I\'m here to help you create amazing presentations!',
                'who built you': 'I\'m an AI assistant for PPTCon, a PowerPoint presentation app created by AryamanNiboriya. I\'m here to help you create amazing presentations!',
                'who developed you': 'I\'m an AI assistant for PPTCon, a PowerPoint presentation app created by AryamanNiboriya. I\'m here to help you create amazing presentations!',
                'who programmed you': 'I\'m an AI assistant for PPTCon, a PowerPoint presentation app created by AryamanNiboriya. I\'m here to help you create amazing presentations!',
                'who designed you': 'I\'m an AI assistant for PPTCon, a PowerPoint presentation app created by AryamanNiboriya. I\'m here to help you create amazing presentations!',
                'किसने बनाया': 'मैं PPTCon का AI assistant हूं, जो AryamanNiboriya द्वारा बनाया गया PowerPoint presentation app है। मैं आपकी amazing presentations बनाने में मदद करने के लिए यहां हूं!',
                'कौन बनाया': 'मैं PPTCon का AI assistant हूं, जो AryamanNiboriya द्वारा बनाया गया PowerPoint presentation app है। मैं आपकी amazing presentations बनाने में मदद करने के लिए यहां हूं!',
                'तुम्हें किसने बनाया': 'मैं PPTCon का AI assistant हूं, जो AryamanNiboriya द्वारा बनाया गया PowerPoint presentation app है। मैं आपकी amazing presentations बनाने में मदद करने के लिए यहां हूं!',
                'आपको किसने बनाया': 'मैं PPTCon का AI assistant हूं, जो AryamanNiboriya द्वारा बनाया गया PowerPoint presentation app है। मैं आपकी amazing presentations बनाने में मदद करने के लिए यहां हूं!',
                'tumhe kisne banaya': 'मैं PPTCon का AI assistant हूं, जो AryamanNiboriya द्वारा बनाया गया PowerPoint presentation app है। मैं आपकी amazing presentations बनाने में मदद करने के लिए यहां हूं!',
                'aapko kisne banaya': 'मैं PPTCon का AI assistant हूं, जो AryamanNiboriya द्वारा बनाया गया PowerPoint presentation app है। मैं आपकी amazing presentations बनाने में मदद करने के लिए यहां हूं!',
                'tumhe kaun banaya': 'मैं PPTCon का AI assistant हूं, जो AryamanNiboriya द्वारा बनाया गया PowerPoint presentation app है। मैं आपकी amazing presentations बनाने में मदद करने के लिए यहां हूं!',
                'aapko kaun banaya': 'मैं PPTCon का AI assistant हूं, जो AryamanNiboriya द्वारा बनाया गया PowerPoint presentation app है। मैं आपकी amazing presentations बनाने में मदद करने के लिए यहां हूं!',
                'who made this': 'I\'m an AI assistant for PPTCon, a PowerPoint presentation app created by AryamanNiboriya. I\'m here to help you create amazing presentations!',
                'who created this': 'I\'m an AI assistant for PPTCon, a PowerPoint presentation app created by AryamanNiboriya. I\'m here to help you create amazing presentations!',
                'who built this': 'I\'m an AI assistant for PPTCon, a PowerPoint presentation app created by AryamanNiboriya. I\'m here to help you create amazing presentations!',
                'who developed this': 'I\'m an AI assistant for PPTCon, a PowerPoint presentation app created by AryamanNiboriya. I\'m here to help you create amazing presentations!',
                'qui vous a créé': 'Je suis un assistant IA pour PPTCon, une application de présentation PowerPoint créée par AryamanNiboriya. Je suis ici pour vous aider à créer des présentations incroyables!',
                'quien te creó': 'Soy un asistente de IA para PPTCon, una aplicación de presentaciones PowerPoint creada por AryamanNiboriya. ¡Estoy aquí para ayudarte a crear presentaciones increíbles!',
                'wer hat dich erstellt': 'Ich bin ein KI-Assistent für PPTCon, eine PowerPoint-Präsentations-App, die von AryamanNiboriya erstellt wurde. Ich bin hier, um Ihnen zu helfen, erstaunliche Präsentationen zu erstellen!',
                'chi ti ha creato': 'Sono un assistente AI per PPTCon, un\'app di presentazioni PowerPoint creata da AryamanNiboriya. Sono qui per aiutarti a creare presentazioni incredibili!',
                'quem te criou': 'Sou um assistente de IA para PPTCon, um aplicativo de apresentações PowerPoint criado por AryamanNiboriya. Estou aqui para ajudá-lo a criar apresentações incríveis!',
                'кто создал вас': 'Я ИИ-ассистент для PPTCon, приложения для презентаций PowerPoint, созданного AryamanNiboriya. Я здесь, чтобы помочь вам создавать удивительные презентации!',
                '谁创造了你': '我是PPTCon的AI助手，这是由AryamanNiboriya创建的PowerPoint演示应用程序。我在这里帮助您创建令人惊叹的演示文稿！',
                '誰があなたを作った': '私はPPTConのAIアシスタントです。これはAryamanNiboriyaによって作成されたPowerPointプレゼンテーションアプリです。素晴らしいプレゼンテーションを作成するお手伝いをします！',
                '누가 당신을 만들었나요': '저는 AryamanNiboriya가 만든 PowerPoint 프레젠테이션 앱인 PPTCon의 AI 어시스턴트입니다. 놀라운 프레젠테이션을 만드는 데 도움을 드리기 위해 여기 있습니다!',
                'ใครสร้างคุณ': 'ฉันเป็นผู้ช่วย AI สำหรับ PPTCon แอปพลิเคชันการนำเสนอ PowerPoint ที่สร้างโดย AryamanNiboriya ฉันอยู่ที่นี่เพื่อช่วยคุณสร้างการนำเสนอที่น่าทึ่ง!',
                
                # Multilingual Personal Questions - What is your name
                'what is your name': 'I\'m the AI assistant for PPTCon, your presentation creation partner!',
                'what\'s your name': 'I\'m the AI assistant for PPTCon, your presentation creation partner!',
                'what should i call you': 'I\'m the AI assistant for PPTCon, your presentation creation partner!',
                'what do you call yourself': 'I\'m the AI assistant for PPTCon, your presentation creation partner!',
                'what is your identity': 'I\'m the AI assistant for PPTCon, your presentation creation partner!',
                'आपका नाम क्या है': 'मैं PPTCon का AI assistant हूं, आपका presentation creation partner!',
                'तुम्हारा नाम क्या है': 'मैं PPTCon का AI assistant हूं, आपका presentation creation partner!',
                'aapka naam kya hai': 'मैं PPTCon का AI assistant हूं, आपका presentation creation partner!',
                'tumhara naam kya hai': 'मैं PPTCon का AI assistant हूं, आपका presentation creation partner!',
                'tumhara name kya hai': 'मैं PPTCon का AI assistant हूं, आपका presentation creation partner!',
                'aapka name kya hai': 'मैं PPTCon का AI assistant हूं, आपका presentation creation partner!',
                'comment vous appelez-vous': 'Je suis l\'assistant IA de PPTCon, votre partenaire de création de présentations!',
                'cómo te llamas': '¡Soy el asistente de IA de PPTCon, tu compañero de creación de presentaciones!',
                'wie heißt du': 'Ich bin der KI-Assistent für PPTCon, Ihr Partner für die Erstellung von Präsentationen!',
                'come ti chiami': 'Sono l\'assistente AI di PPTCon, il tuo partner per la creazione di presentazioni!',
                'qual é o seu nome': 'Sou o assistente de IA do PPTCon, seu parceiro de criação de apresentações!',
                'как вас зовут': 'Я ИИ-ассистент PPTCon, ваш партнер по созданию презентаций!',
                '你叫什么名字': '我是PPTCon的AI助手，您的演示文稿创作伙伴！',
                'あなたの名前は何ですか': '私はPPTConのAIアシスタントです。プレゼンテーション作成のパートナーです！',
                '당신의 이름은 무엇입니까': '저는 PPTCon의 AI 어시스턴트입니다. 프레젠테이션 제작 파트너입니다!',
                'คุณชื่ออะไร': 'ฉันเป็นผู้ช่วย AI ของ PPTCon พันธมิตรการสร้างการนำเสนอของคุณ!',
                
                # Multilingual Personal Questions - What can you do
                'what can you do': 'I can help you create presentations, give PowerPoint tips, suggest content, provide design advice, and answer questions about presentation creation. I\'m specifically designed for PPTCon app users!',
                'what do you do': 'I can help you create presentations, give PowerPoint tips, suggest content, provide design advice, and answer questions about presentation creation. I\'m specifically designed for PPTCon app users!',
                'what are your capabilities': 'I can help you create presentations, give PowerPoint tips, suggest content, provide design advice, and answer questions about presentation creation. I\'m specifically designed for PPTCon app users!',
                'what are your features': 'I can help you create presentations, give PowerPoint tips, suggest content, provide design advice, and answer questions about presentation creation. I\'m specifically designed for PPTCon app users!',
                'what are your functions': 'I can help you create presentations, give PowerPoint tips, suggest content, provide design advice, and answer questions about presentation creation. I\'m specifically designed for PPTCon app users!',
                'what services do you provide': 'I can help you create presentations, give PowerPoint tips, suggest content, provide design advice, and answer questions about presentation creation. I\'m specifically designed for PPTCon app users!',
                'how can you help me': 'I can help you create presentations, give PowerPoint tips, suggest content, provide design advice, and answer questions about presentation creation. I\'m specifically designed for PPTCon app users!',
                'आप क्या कर सकते हैं': 'मैं आपकी presentations बनाने, PowerPoint tips देने, content suggest करने, design advice देने और presentation creation के बारे में questions answer करने में मदद कर सकता हूं। मैं विशेष रूप से PPTCon app users के लिए बनाया गया हूं!',
                'तुम क्या कर सकते हो': 'मैं आपकी presentations बनाने, PowerPoint tips देने, content suggest करने, design advice देने और presentation creation के बारे में questions answer करने में मदद कर सकता हूं। मैं विशेष रूप से PPTCon app users के लिए बनाया गया हूं!',
                'aap kya kar sakte hain': 'मैं आपकी presentations बनाने, PowerPoint tips देने, content suggest करने, design advice देने और presentation creation के बारे में questions answer करने में मदद कर सकता हूं। मैं विशेष रूप से PPTCon app users के लिए बनाया गया हूं!',
                'tum kya kar sakte ho': 'मैं आपकी presentations बनाने, PowerPoint tips देने, content suggest करने, design advice देने और presentation creation के बारे में questions answer करने में मदद कर सकता हूं। मैं विशेष रूप से PPTCon app users के लिए बनाया गया हूं!',
                'aap kya kar sakte ho': 'मैं आपकी presentations बनाने, PowerPoint tips देने, content suggest करने, design advice देने और presentation creation के बारे में questions answer करने में मदद कर सकता हूं। मैं विशेष रूप से PPTCon app users के लिए बनाया गया हूं!',
                'tum kya kar sakte hain': 'मैं आपकी presentations बनाने, PowerPoint tips देने, content suggest करने, design advice देने और presentation creation के बारे में questions answer करने में मदद कर सकता हूं। मैं विशेष रूप से PPTCon app users के लिए बनाया गया हूं!',
                'que pouvez-vous faire': 'Je peux vous aider à créer des présentations, donner des conseils PowerPoint, suggérer du contenu, fournir des conseils de conception et répondre aux questions sur la création de présentations. Je suis spécialement conçu pour les utilisateurs de l\'application PPTCon!',
                'qué puedes hacer': 'Puedo ayudarte a crear presentaciones, dar consejos de PowerPoint, sugerir contenido, proporcionar consejos de diseño y responder preguntas sobre la creación de presentaciones. ¡Estoy específicamente diseñado para usuarios de la aplicación PPTCon!',
                'was können sie tun': 'Ich kann Ihnen beim Erstellen von Präsentationen, beim Geben von PowerPoint-Tipps, beim Vorschlagen von Inhalten, beim Bereitstellen von Design-Ratschlägen und beim Beantworten von Fragen zur Präsentationserstellung helfen. Ich bin speziell für PPTCon-App-Benutzer entwickelt!',
                'cosa puoi fare': 'Posso aiutarti a creare presentazioni, dare consigli PowerPoint, suggerire contenuti, fornire consigli di progettazione e rispondere a domande sulla creazione di presentazioni. Sono specificamente progettato per gli utenti dell\'app PPTCon!',
                'o que você pode fazer': 'Posso ajudá-lo a criar apresentações, dar dicas do PowerPoint, sugerir conteúdo, fornecer conselhos de design e responder perguntas sobre criação de apresentações. Sou especificamente projetado para usuários do aplicativo PPTCon!',
                'что вы можете делать': 'Я могу помочь вам создавать презентации, давать советы по PowerPoint, предлагать контент, предоставлять советы по дизайну и отвечать на вопросы о создании презентаций. Я специально разработан для пользователей приложения PPTCon!',
                '你能做什么': '我可以帮助您创建演示文稿、提供PowerPoint技巧、建议内容、提供设计建议并回答有关演示文稿创建的问题。我专门为PPTCon应用程序用户设计！',
                'あなたは何ができますか': 'プレゼンテーションの作成、PowerPointのヒントの提供、コンテンツの提案、デザインアドバイスの提供、プレゼンテーション作成に関する質問への回答をお手伝いできます。PPTConアプリユーザー向けに特別に設計されています！',
                '당신은 무엇을 할 수 있나요': '프레젠테이션 생성, PowerPoint 팁 제공, 콘텐츠 제안, 디자인 조언 제공, 프레젠테이션 생성에 대한 질문 답변을 도와드릴 수 있습니다. PPTCon 앱 사용자를 위해 특별히 설계되었습니다!',
                'คุณทำอะไรได้บ้าง': 'ฉันสามารถช่วยคุณสร้างการนำเสนอ ให้คำแนะนำ PowerPoint แนะนำเนื้อหา ให้คำแนะนำการออกแบบ และตอบคำถามเกี่ยวกับการสร้างการนำเสนอ ฉันได้รับการออกแบบมาเฉพาะสำหรับผู้ใช้แอป PPTCon!',
                
                # App Information
                'pptcon': 'PPTCon is a powerful PowerPoint presentation app created by AryamanNiboriya. It features AI content generation, template conversion, professional designs, user profiles, avatar management, and a complete presentation creation ecosystem. It helps users create stunning presentations easily!',
                'app': 'PPTCon is a powerful PowerPoint presentation app created by AryamanNiboriya. It features AI content generation, template conversion, professional designs, user profiles, avatar management, and a complete presentation creation ecosystem. It helps users create stunning presentations easily!',
                'features': 'PPTCon offers: 1) AI-powered PPT generation from topics 2) Template conversion and customization 3) Professional design templates 4) Content generation with AI 5) User authentication and profiles 6) Avatar management 7) Professional email system for contact and feedback',
                'aryaman': 'AryamanNiboriya is the talented developer who created PPTCon, this amazing PowerPoint presentation app with AI features!',
                'developer': 'PPTCon was created by AryamanNiboriya, who built this comprehensive PowerPoint presentation platform with AI capabilities!'
            }
            
            # Find the best matching response
            response_text = None
            for keyword, response in fallback_responses.items():
                if keyword in user_message:
                    response_text = response
                    break
            
            # Default response if no keyword matches
            if not response_text:
                response_text = 'I\'m here to help with your presentations! I can assist with design tips, content structure, PowerPoint best practices, and more. What specific aspect of presentation creation would you like to know about?'
            
            # Update chat sessions count in dashboard
            try:
                email = g.username
                print(f"DEBUG: Updating dashboard for email: {email}")
                users = load_users()
                user_id = None
                
                # Find user ID
                for uid, user in users.items():
                    if user['email'].lower() == email.lower():
                        user_id = uid
                        break
                
                print(f"DEBUG: Found user_id: {user_id}")
                
                if user_id:
                    # Update dashboard data
                    dashboard_data = load_dashboard_data()
                    if user_id not in dashboard_data:
                        dashboard_data[user_id] = {}
                    
                    # Get current count
                    current_count = dashboard_data[user_id].get('total_chat_sessions', 0)
                    print(f"DEBUG: Current chat sessions count: {current_count}")
                    
                    # Increment chat sessions count
                    dashboard_data[user_id]['total_chat_sessions'] = current_count + 1
                    print(f"DEBUG: New chat sessions count: {dashboard_data[user_id]['total_chat_sessions']}")
                    
                    save_dashboard_data(dashboard_data)
                    print(f"DEBUG: Dashboard data saved successfully")
                    
                    # Add chat activity
                    activity = {
                        'id': str(uuid.uuid4()),
                        'type': 'chat_session',
                        'title': f'Chat: {user_message[:50]}...',
                        'description': f'Chat session with AI assistant',
                        'timestamp': datetime.utcnow().isoformat(),
                        'metadata': {'message_length': len(user_message)}
                    }
                    
                    user_activities = load_user_activities()
                    if email not in user_activities:
                        user_activities[email] = []
                    user_activities[email].append(activity)
                    save_user_activities(user_activities)
                    
            except Exception as e:
                print(f"Dashboard update error: {e}")
            
            print(f"Chatbot: returning fallback reply: {response_text}")
            return jsonify({'reply': response_text, 'raw_response': None}), 200
        
        # Use Gemini API to generate response
        headers = {
            'Content-Type': 'application/json',
        }
        
        # Create a context-aware prompt
        system_prompt = """You are a helpful AI assistant for a PowerPoint presentation generation app called "PPTCon". 

        IMPORTANT PERSONAL INFORMATION:
        - App Name: PPTCon
        - Developer: Created by AryamanNiboriya
        - Purpose: PowerPoint presentation generation and conversion
        - Main Features: 
          * AI-powered PPT generation from topics
          * Template conversion and customization
          * Professional design templates
          * Content generation with AI
          * User authentication and profiles
          * Avatar management
          * Professional email system
        
        You help users with:
        - Creating presentations
        - PowerPoint tips and tricks
        - Content suggestions
        - Design advice
        - General questions about presentations
        
        FOR PERSONAL QUESTIONS:
        - If asked "who made you" or "who created you": "I'm an AI assistant for PPTCon, a PowerPoint presentation app created by AryamanNiboriya. I'm here to help you create amazing presentations!"
        - If asked "what is your name": "I'm the AI assistant for PPTCon, your presentation creation partner!"
        - If asked "what can you do": "I can help you create presentations, give PowerPoint tips, suggest content, provide design advice, and answer questions about presentation creation. I'm specifically designed for PPTCon app users!"
        - If asked about the app: "PPTCon is a powerful PowerPoint presentation app created by AryamanNiboriya. It features AI content generation, template conversion, professional designs, user profiles, avatar management, and a complete presentation creation ecosystem. It helps users create stunning presentations easily!"
        - If asked about features: "PPTCon offers: 1) AI-powered PPT generation from topics 2) Template conversion and customization 3) Professional design templates 4) Content generation with AI 5) User authentication and profiles 6) Avatar management 7) Professional email system for contact and feedback"
        
        Keep responses helpful, friendly, and relevant to presentation creation. 
        If asked about other topics, politely redirect to presentation-related help.
        Respond in a conversational, helpful manner. Be proud of being part of PPTCon created by AryamanNiboriya!"""
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": system_prompt + "\n\nUser: " + user_message + "\n\nAssistant:"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        
        response = requests.post(
            f"{gemini_url()}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            try:
                result = response.json()
            except Exception as e:
                print("Chatbot: failed to decode JSON from Gemini response:", e)
                result = None

            ai_response = None
            if result:
                # Try multiple known response shapes to extract text safely
                try:
                    # Standard: candidates -> content -> parts -> text
                    candidates = result.get('candidates') if isinstance(result, dict) else None
                    if candidates and len(candidates) > 0:
                        content = candidates[0].get('content', {}) if isinstance(candidates[0], dict) else {}
                        parts = content.get('parts') if isinstance(content, dict) else None
                        if parts and len(parts) > 0:
                            ai_response = parts[0].get('text')
                        elif isinstance(content, str) and content.strip():
                            ai_response = content
                        elif isinstance(content, dict) and 'text' in content:
                            ai_response = content.get('text')
                except Exception as e:
                    print("Chatbot parse attempt1 error:", e)

                if not ai_response:
                    try:
                        # Alternate shapes: outputs/output -> content -> text
                        outputs = result.get('output') or result.get('outputs')
                        if outputs and len(outputs) > 0 and isinstance(outputs[0], dict):
                            out_content = outputs[0].get('content')
                            if isinstance(out_content, list) and len(out_content) > 0 and isinstance(out_content[0], dict):
                                ai_response = out_content[0].get('text') or out_content[0].get('payload')
                    except Exception as e:
                        print("Chatbot parse attempt2 error:", e)

                if not ai_response:
                    # Last resort: try to find any string value in nested dicts
                    def find_first_text(obj):
                        if isinstance(obj, str) and obj.strip():
                            return obj
                        if isinstance(obj, dict):
                            for v in obj.values():
                                t = find_first_text(v)
                                if t:
                                    return t
                        if isinstance(obj, list):
                            for item in obj:
                                t = find_first_text(item)
                                if t:
                                    return t
                        return None
                    ai_response = find_first_text(result)

            if ai_response:
                response_text = ai_response
            else:
                print("Chatbot: could not find text in Gemini response; full response:", result)
                response_text = 'Sorry, I could not generate a response. Please try again.'
        else:
            print(f"Gemini API error: {response.status_code} - {response.text}")
            # Fallback to basic responses when API fails
            if 'presentation' in user_message:
                response_text = 'For creating effective presentations, focus on clear structure, visual design, and engaging content. Would you like specific tips for any of these areas?'
            elif 'powerpoint' in user_message:
                response_text = 'PowerPoint tips: Use readable fonts, maintain consistency, include visuals, and practice your delivery. What specific aspect would you like to know more about?'
            else:
                response_text = 'I\'m here to help with your presentations! I can assist with design tips, content structure, and PowerPoint best practices. What would you like to know?'
        
        # Update chat sessions count in dashboard
        try:
            email = g.username
            users = load_users()
            user_id = None
            
            # Find user ID
            for uid, user in users.items():
                if user['email'].lower() == email.lower():
                    user_id = uid
                    break
            
            if user_id:
                # Update dashboard data
                dashboard_data = load_dashboard_data()
                if user_id not in dashboard_data:
                    dashboard_data[user_id] = {}
                
                # Increment chat sessions count
                current_count = dashboard_data[user_id].get('total_chat_sessions', 0)
                dashboard_data[user_id]['total_chat_sessions'] = current_count + 1
                print(f"Chat session updated for user {user_id}: {current_count} -> {current_count + 1}")
                save_dashboard_data(dashboard_data)
                
                # Add chat activity
                activity = {
                    'id': str(uuid.uuid4()),
                    'type': 'chat_session',
                    'title': f'Chat: {user_message[:50]}...',
                    'description': f'Chat session with AI assistant',
                    'timestamp': datetime.utcnow().isoformat(),
                    'metadata': {'message_length': len(user_message)}
                }
                
                user_activities = load_user_activities()
                if email not in user_activities:
                    user_activities[email] = []
                user_activities[email].append(activity)
                save_user_activities(user_activities)
                
        except Exception as e:
            print(f"Dashboard update error: {e}")
        
        print(f"Chatbot: final reply to return: {response_text}")
        # Include the raw model response for debug (useful during local development)
        try:
            raw = result if 'result' in locals() else None
        except Exception:
            raw = None
        return jsonify({'reply': response_text, 'raw_response': raw}), 200
            
    except requests.exceptions.Timeout:
        return jsonify({'reply': 'Sorry, the request took too long. Please try again.'}), 200
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return jsonify({'reply': 'Sorry, there was a network error. Please check your connection and try again.'}), 200
    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({'reply': 'Sorry, something went wrong. Please try again.'}), 200

# Dashboard Endpoints
@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required
def get_dashboard_stats():
    """Get user dashboard statistics"""
    try:
        email = g.username
        print(f"DEBUG STATS: Current user email: {email}")
        users = load_users()
        print(f"DEBUG STATS: All users: {users}")
        user_id = None
        
        # Find user ID
        for uid, user in users.items():
            print(f"DEBUG STATS: Checking user {uid} with email {user['email']}")
            if user['email'].lower() == email.lower():
                user_id = uid
                print(f"DEBUG STATS: Found matching user_id: {user_id}")
                break
        
        if not user_id:
            print(f"DEBUG STATS: User not found for email: {email}")
            return jsonify({'error': 'User not found'}), 404
        
        # Load dashboard data
        dashboard_data = load_dashboard_data()
        print(f"DEBUG STATS: Dashboard data for user {user_id}: {dashboard_data.get(user_id, {})}")
        
        # Initialize missing user dashboard data and persist to storage
        if user_id not in dashboard_data:
            dashboard_data[user_id] = {
                'user_id': user_id,
                'email': email,
                'total_presentations': 0,
                'total_conversions': 0,
                'total_ai_generations': 0,
                'total_chat_sessions': 0,
                'last_activity': None,
                'favorite_templates': [],
                'recent_files': []
            }
            save_dashboard_data(dashboard_data)
        
        user_data = dashboard_data[user_id]
        
        # Get AI generations count from dashboard data
        user_data['total_ai_generations'] = user_data.get('total_ai_generations', 0)
        print(f"DEBUG STATS: AI generations count: {user_data['total_ai_generations']}")
        
        # Calculate total presentations = AI generations + conversions
        total_ai = user_data.get('total_ai_generations', 0)
        total_conversions = user_data.get('total_conversions', 0)
        user_data['total_presentations'] = total_ai + total_conversions
        print(f"DEBUG STATS: Total presentations: {user_data['total_presentations']} (AI: {total_ai} + Conversions: {total_conversions})")
        
        # Get chat sessions count from dashboard data (not chat history)
        # Chat sessions are counted in chatbot endpoint
        user_data['total_chat_sessions'] = user_data.get('total_chat_sessions', 0)
        print(f"DEBUG STATS: Final chat sessions count: {user_data['total_chat_sessions']}")
        
        return jsonify({
            'stats': user_data,
            'user': {
                'id': user_id,
                'username': users[user_id]['username'],
                'email': email
            }
        }), 200
        
    except Exception as e:
        print(f"Dashboard stats error: {e}")
        return jsonify({'error': 'Failed to load dashboard stats'}), 500

# ... (rest of the code remains the same)
@jwt_required
def get_user_activities():
    """Get user recent activities"""
    try:
        email = g.username
        user_activities = load_user_activities()
        
        # Get user activities (last 10)
        activities = user_activities.get(email, [])
        recent_activities = activities[-10:] if len(activities) > 10 else activities
        
        return jsonify({
            'activities': recent_activities
        }), 200
        
    except Exception as e:
        print(f"User activities error: {e}")
        return jsonify({'error': 'Failed to load user activities'}), 500

@app.route('/api/dashboard/activity', methods=['POST'])
@jwt_required
def add_user_activity():
    """Add new user activity"""
    try:
        email = g.username
        data = request.get_json()
        
        activity = {
            'id': str(uuid.uuid4()),
            'type': data.get('type', 'general'),
            'title': data.get('title', 'Activity'),
            'description': data.get('description', ''),
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': data.get('metadata', {})
        }
        
        user_activities = load_user_activities()
        if email not in user_activities:
            user_activities[email] = []
        
        user_activities[email].append(activity)
        save_user_activities(user_activities)
        
        # Handle chat session deletion
        if data.get('type') == 'chat_session_deleted':
            try:
                users = load_users()
                user_id = None
                
                # Find user ID
                for uid, user in users.items():
                    if user['email'].lower() == email.lower():
                        user_id = uid
                        break
                
                if user_id:
                    # Decrease chat sessions count
                    dashboard_data = load_dashboard_data()
                    if user_id in dashboard_data:
                        current_count = dashboard_data[user_id].get('total_chat_sessions', 0)
                        if current_count > 0:
                            dashboard_data[user_id]['total_chat_sessions'] = current_count - 1
                            save_dashboard_data(dashboard_data)
                            print(f"DEBUG: Decreased chat sessions count to {dashboard_data[user_id]['total_chat_sessions']}")
            except Exception as e:
                print(f"Error updating dashboard for chat deletion: {e}")
        
        return jsonify({
            'message': 'Activity added successfully',
            'activity': activity
        }), 201
        
    except Exception as e:
        print(f"Add activity error: {e}")
        return jsonify({'error': 'Failed to add activity'}), 500

@app.route('/api/dashboard/activity/<activity_id>', methods=['DELETE'])
@jwt_required
def delete_user_activity(activity_id):
    """Delete a specific user activity"""
    try:
        email = g.username
        user_activities = load_user_activities()
        
        if email in user_activities:
            # Remove the activity with matching ID
            user_activities[email] = [
                activity for activity in user_activities[email] 
                if activity.get('id') != activity_id
            ]
            save_user_activities(user_activities)
            print(f"DEBUG: Deleted activity {activity_id} for user {email}")
        
        return jsonify({'message': 'Activity deleted successfully'}), 200
        
    except Exception as e:
        print(f"Delete activity error: {e}")
        return jsonify({'error': 'Failed to delete activity'}), 500

@app.route('/api/dashboard/presentations', methods=['GET'])
@jwt_required
def get_user_presentations():
    """Get user presentations list"""
    try:
        email = g.username
        dashboard_data = load_dashboard_data()
        
        # Find user ID
        users = load_users()
        user_id = None
        for uid, user in users.items():
            if user['email'].lower() == email.lower():
                user_id = uid
                break
        
        if not user_id:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = dashboard_data.get(user_id, {})
        presentations = user_data.get('presentations', [])
        
        return jsonify({
            'presentations': presentations
        }), 200
        
    except Exception as e:
        print(f"User presentations error: {e}")
        return jsonify({'error': 'Failed to load presentations'}), 500

@app.route('/api/dashboard/presentation', methods=['POST'])
@jwt_required
def add_user_presentation():
    """Add new user presentation"""
    try:
        email = g.username
        data = request.get_json()
        
        # Find user ID
        users = load_users()
        user_id = None
        for uid, user in users.items():
            if user['email'].lower() == email.lower():
                user_id = uid
                break
        
        if not user_id:
            return jsonify({'error': 'User not found'}), 404
        
        presentation = {
            'id': str(uuid.uuid4()),
            'title': data.get('title', 'Untitled Presentation'),
            'filename': data.get('filename', ''),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'slides_count': data.get('slides_count', 0),
            'template_used': data.get('template_used', ''),
            'file_size': data.get('file_size', 0)
        }
        
        dashboard_data = load_dashboard_data()
        if user_id not in dashboard_data:
            dashboard_data[user_id] = {}
        
        if 'presentations' not in dashboard_data[user_id]:
            dashboard_data[user_id]['presentations'] = []
        
        dashboard_data[user_id]['presentations'].append(presentation)
        dashboard_data[user_id]['total_presentations'] = len(dashboard_data[user_id]['presentations'])
        
        save_dashboard_data(dashboard_data)
        
        # Add activity
        activity = {
            'id': str(uuid.uuid4()),
            'type': 'presentation_created',
            'title': f'Created: {presentation["title"]}',
            'description': f'Created a new presentation with {presentation["slides_count"]} slides',
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': {'presentation_id': presentation['id']}
        }
        
        user_activities = load_user_activities()
        if email not in user_activities:
            user_activities[email] = []
        user_activities[email].append(activity)
        save_user_activities(user_activities)
        
        return jsonify({
            'message': 'Presentation added successfully',
            'presentation': presentation
        }), 201
        
    except Exception as e:
        print(f"Add presentation error: {e}")
        return jsonify({'error': 'Failed to add presentation'}), 500

@app.route('/api/analytics/overview', methods=['GET'])
@jwt_required
def get_analytics_overview():
    """Get comprehensive analytics overview"""
    try:
        print("Received request for analytics overview")
        email = g.username
        
        # Get user ID
        users = load_users()
        user_id = None
        for uid, user in users.items():
            if user['email'].lower() == email.lower():
                user_id = uid
                break
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        # Load user-scoped data only
        dashboard_data = load_dashboard_data()
        
        # Ensure we're only getting data for this specific user
        user_data = dashboard_data.get(user_id, {})
        
        # Get user-specific activities and chat history
        activities = get_user_activities_by_email(email)
        chats = get_chat_history_by_email(email)
        
        # Calculate analytics (with sample data for new users)
        total_presentations = user_data.get('total_presentations', 0)
        total_ai_generations = user_data.get('total_ai_generations', 0)
        total_conversions = user_data.get('total_conversions', 0)
        templates_used = user_data.get('templates_used', 0)
        
        # Initialize clean data for new users - no sample data generation
        if user_id not in dashboard_data:
            dashboard_data[user_id] = {
                'user_id': user_id,
                'email': email,
                'total_presentations': 0,
                'total_ai_generations': 0,
                'total_conversions': 0,
                'templates_used': 0,
                'total_chat_sessions': 0,
                'last_activity': None,
                'favorite_templates': [],
                'recent_files': []
            }
            save_dashboard_data(dashboard_data)
            
        # Get actual user data from dashboard_data (no sample data injection)
        user_data = dashboard_data[user_id]
        total_presentations = user_data.get('total_presentations', 0)
        total_ai_generations = user_data.get('total_ai_generations', 0)
        total_conversions = user_data.get('total_conversions', 0)
        templates_used = user_data.get('templates_used', 0)
        
        # Activity analysis
        activity_types = {}
        for activity in activities:
            activity_type = activity.get('type', 'unknown')
            activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
        
        # Time-based analysis (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_activities = [
            activity for activity in activities 
            if datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00')) > thirty_days_ago
        ]
        
        # Daily activity for last 7 days
        daily_activity = {}
        for i in range(7):
            date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_activity[date] = 0
        
        for activity in recent_activities:
            activity_date = datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
            if activity_date in daily_activity:
                daily_activity[activity_date] += 1
        
        # Chat analysis
        total_chat_sessions = len(chats)
        total_chat_messages = sum(len(chat.get('messages', [])) for chat in chats)
        
        # Performance metrics
        avg_presentations_per_day = total_presentations / 30 if total_presentations > 0 else 0
        ai_generation_rate = (total_ai_generations / total_presentations * 100) if total_presentations > 0 else 0
        template_usage_rate = (templates_used / total_presentations * 100) if total_presentations > 0 else 0
        
        # If there's no activity for this user, generate lightweight demo data so frontend charts render
        if not activity_types and total_presentations == 0 and all(v == 0 for v in daily_activity.values()):
            # small non-zero sample to make charts visible
            activity_types = {'ai_generation': 2, 'conversion': 1, 'template_downloaded': 1}
            # fill last 7 days with sample counts
            for i in range(7):
                date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
                daily_activity[date] = (7 - i) % 3  # simple pattern 1,2,0

        analytics_data = {
            'overview': {
                'total_presentations': total_presentations,
                'total_ai_generations': total_ai_generations,
                'total_conversions': total_conversions,
                'templates_used': templates_used,
                'total_chat_sessions': total_chat_sessions,
                'total_chat_messages': total_chat_messages
            },
            'performance': {
                'avg_presentations_per_day': round(avg_presentations_per_day, 2),
                'ai_generation_rate': round(ai_generation_rate, 1),
                'template_usage_rate': round(template_usage_rate, 1),
                'activity_score': len(recent_activities)
            },
            'activity_breakdown': activity_types,
            'daily_activity': daily_activity,
            'recent_trends': {
                'last_7_days_activity': len([a for a in recent_activities if 
                    datetime.fromisoformat(a['timestamp'].replace('Z', '+00:00')) > datetime.utcnow() - timedelta(days=7)]),
                'last_30_days_activity': len(recent_activities),
                'most_active_day': (max(daily_activity.items(), key=lambda x: x[1])[0] if daily_activity else None)
            }
        }
        
        return jsonify(analytics_data), 200
        
    except Exception as e:
        print(f"Error in analytics overview: {e}")
        return jsonify({"error": f"Failed to fetch analytics: {str(e)}"}), 500

@app.route('/api/analytics/performance', methods=['GET'])
@jwt_required
def get_performance_analytics():
    """Get detailed performance analytics"""
    try:
        print("Received request for performance analytics")
        email = g.username
        
        # Get user ID
        users = load_users()
        user_id = None
        for uid, user in users.items():
            if user['email'].lower() == email.lower():
                user_id = uid
                break
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        # Load user-scoped data only
        dashboard_data = load_dashboard_data()
        
        # Ensure we're only getting data for this specific user
        user_data = dashboard_data.get(user_id, {})
        
        # Get user-specific activities
        activities = get_user_activities_by_email(email)
        
        # Time-based performance analysis
        
        # Weekly performance (last 4 weeks)
        weekly_performance = []
        for week in range(4):
            week_start = datetime.utcnow() - timedelta(weeks=week+1)
            week_end = datetime.utcnow() - timedelta(weeks=week)
            
            week_activities = [
                activity for activity in activities
                if week_start < datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00')) <= week_end
            ]
            
            week_data = {
                'week': f"Week {4-week}",
                'activities': len(week_activities),
                'ai_generations': len([a for a in week_activities if a.get('type') == 'ai_generation']),
                'conversions': len([a for a in week_activities if a.get('type') == 'conversion']),
                'template_downloads': len([a for a in week_activities if a.get('type') == 'template_downloaded'])
            }
            weekly_performance.append(week_data)
        
        # Monthly trends (last 6 months)
        monthly_trends = []
        for month in range(6):
            month_start = datetime.utcnow() - timedelta(days=30*(month+1))
            month_end = datetime.utcnow() - timedelta(days=30*month)
            
            month_activities = [
                activity for activity in activities
                if month_start < datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00')) <= month_end
            ]
            
            month_data = {
                'month': month_start.strftime('%B %Y'),
                'total_activities': len(month_activities),
                'presentations_created': len([a for a in month_activities if a.get('type') in ['ai_generation', 'conversion']])
            }
            monthly_trends.append(month_data)
        
        # Efficiency metrics
        total_activities = len(activities)
        ai_activities = len([a for a in activities if a.get('type') == 'ai_generation'])
        conversion_activities = len([a for a in activities if a.get('type') == 'conversion'])
        
        efficiency_metrics = {
            'total_activities': total_activities,
            'ai_efficiency': round((ai_activities / total_activities * 100), 1) if total_activities > 0 else 0,
            'conversion_efficiency': round((conversion_activities / total_activities * 100), 1) if total_activities > 0 else 0,
            'productivity_score': min(100, total_activities * 2),  # Simple scoring
            'consistency_score': len([a for a in activities if 
                datetime.fromisoformat(a['timestamp'].replace('Z', '+00:00')) > datetime.utcnow() - timedelta(days=7)
            ]) * 10
        }
        
        # Provide simple demo values when there is no real activity so charts are visible
        if all(wp.get('activities', 0) == 0 for wp in weekly_performance):
            weekly_performance = [
                {'week': f'Week {4-i}', 'activities': max(0, 3 - i), 'ai_generations': max(0, 2 - i//2), 'conversions': max(0, 1 - i//3), 'template_downloads': max(0, 1 - i//3)}
                for i in range(4)
            ]

        if all(mt.get('total_activities', 0) == 0 for mt in monthly_trends):
            monthly_trends = [
                {'month': (datetime.utcnow() - timedelta(days=30*(i+1))).strftime('%B %Y'), 'total_activities': (6-i)%3, 'presentations_created': (6-i)%2}
                for i in range(6)
            ]

        performance_data = {
            'weekly_performance': weekly_performance,
            'monthly_trends': monthly_trends,
            'efficiency_metrics': efficiency_metrics,
            'activity_distribution': {
                'ai_generations': ai_activities,
                'conversions': conversion_activities,
                'template_downloads': len([a for a in activities if a.get('type') == 'template_downloaded']),
                'other_activities': max(0, total_activities - ai_activities - conversion_activities)
            }
        }
        
        return jsonify(performance_data), 200
        
    except Exception as e:
        print(f"Error in performance analytics: {e}")
        return jsonify({"error": f"Failed to fetch performance analytics: {str(e)}"}), 500

@app.route('/api/analytics/usage', methods=['GET'])
@jwt_required
def get_usage_analytics():
    """Get detailed usage analytics"""
    try:
        print("Received request for usage analytics")
        email = g.username
        
        # Get user ID
        users = load_users()
        user_id = None
        for uid, user in users.items():
            if user['email'].lower() == email.lower():
                user_id = uid
                break
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        # Load user-scoped data only
        dashboard_data = load_dashboard_data()
        
        # Ensure we're only getting data for this specific user
        user_data = dashboard_data.get(user_id, {})
        
        # Get user-specific activities and chat history
        activities = get_user_activities_by_email(email)
        chats = get_chat_history_by_email(email)
        
        # Feature usage analysis
        feature_usage = {
            'ai_generation': {
                'count': user_data.get('total_ai_generations', 0),
                'percentage': 0,
                'last_used': None
            },
            'template_conversion': {
                'count': user_data.get('total_conversions', 0),
                'percentage': 0,
                'last_used': None
            },
            'template_downloads': {
                'count': user_data.get('templates_used', 0),
                'percentage': 0,
                'last_used': None
            },
            'chat_sessions': {
                'count': len(chats),
                'percentage': 0,
                'last_used': None
            }
        }
        
        # Calculate percentages and last used dates
        total_usage = sum(feature['count'] for feature in feature_usage.values())
        for feature in feature_usage.values():
            feature['percentage'] = round((feature['count'] / total_usage * 100), 1) if total_usage > 0 else 0
        
        # Find last used dates
        for activity in activities:
            activity_type = activity.get('type', '')
            if activity_type == 'ai_generation' and not feature_usage['ai_generation']['last_used']:
                feature_usage['ai_generation']['last_used'] = activity['timestamp']
            elif activity_type == 'conversion' and not feature_usage['template_conversion']['last_used']:
                feature_usage['template_conversion']['last_used'] = activity['timestamp']
            elif activity_type == 'template_downloaded' and not feature_usage['template_downloads']['last_used']:
                feature_usage['template_downloads']['last_used'] = activity['timestamp']
        
        if chats and not feature_usage['chat_sessions']['last_used']:
            feature_usage['chat_sessions']['last_used'] = chats[-1].get('timestamp', '')
        
        # Time-based usage patterns
        
        # Hourly usage pattern (last 7 days)
        hourly_pattern = {i: 0 for i in range(24)}
        recent_activities = [
            activity for activity in activities
            if datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00')) > datetime.utcnow() - timedelta(days=7)
        ]
        
        for activity in recent_activities:
            hour = datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00')).hour
            hourly_pattern[hour] += 1
        
        # Daily usage pattern (last 30 days)
        daily_pattern = {}
        for i in range(30):
            date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_pattern[date] = 0
        
        for activity in activities:
            activity_date = datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
            if activity_date in daily_pattern:
                daily_pattern[activity_date] += 1
        
        # Usage recommendations
        recommendations = []
        if feature_usage['ai_generation']['count'] < 5:
            recommendations.append("Try AI generation to create presentations faster")
        if feature_usage['template_downloads']['count'] < 3:
            recommendations.append("Explore our template library for professional designs")
        if feature_usage['chat_sessions']['count'] < 2:
            recommendations.append("Use AI chat for help and guidance")
        
        # If usage is empty, provide small demo values for charts
        if total_usage == 0 and all(v == 0 for v in hourly_pattern.values()) and all(v == 0 for v in daily_pattern.values()):
            # hourly: simple pattern across day
            for h in range(24):
                hourly_pattern[h] = (h % 6 == 0) and 1 or 0
            # daily: last 30 days small pattern
            for i in range(30):
                date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
                daily_pattern[date] = (i % 5 == 0) and 1 or 0
            total_usage = sum(f['count'] for f in feature_usage.values()) or 1
            # recalc percentages
            for feature in feature_usage.values():
                feature['percentage'] = round((feature['count'] / total_usage * 100), 1) if total_usage > 0 else 0

        usage_data = {
            'feature_usage': feature_usage,
            'usage_patterns': {
                'hourly': hourly_pattern,
                'daily': daily_pattern
            },
            'recommendations': recommendations,
            'total_usage_count': total_usage
        }
        
        return jsonify(usage_data), 200
        
    except Exception as e:
        print(f"Error in usage analytics: {e}")
        return jsonify({"error": f"Failed to fetch usage analytics: {str(e)}"}), 500

@app.route('/api/analytics/export', methods=['GET'])
@jwt_required
def export_analytics():
    """Export analytics data as JSON"""
    try:
        print("Received request for analytics export")
        email = g.username
        
        # Get user ID
        users = load_users()
        user_id = None
        for uid, user in users.items():
            if user['email'].lower() == email.lower():
                user_id = uid
                break
        
        if not user_id:
            return jsonify({"error": "User not found"}), 404
        
        # Load user-scoped data only
        dashboard_data = load_dashboard_data()
        user_data = dashboard_data.get(user_id, {})
        activities = get_user_activities_by_email(email)
        chats = get_chat_history_by_email(email)
        
        # Create comprehensive export
        export_data = {
            'user_info': {
                'email': email,
                'export_date': datetime.utcnow().isoformat(),
                'data_period': 'All time'
            },
            'dashboard_stats': user_data,
            'activities': activities,
            'chat_sessions': chats,
            'analytics_summary': {
                'total_presentations': user_data.get('total_presentations', 0),
                'total_activities': len(activities),
                'total_chat_sessions': len(chats),
                'most_used_feature': 'ai_generation' if user_data.get('total_ai_generations', 0) > user_data.get('total_conversions', 0) else 'template_conversion'
            }
        }
        
        return jsonify(export_data), 200
        
    except Exception as e:
        print(f"Error in analytics export: {e}")
        return jsonify({"error": f"Failed to export analytics: {str(e)}"}), 500

def clean_gemini_json(text):
    # Remove markdown, backticks, and unwanted escapes
    cleaned = re.sub(r"^```json\n|^```json|^```|```$", "", text.strip(), flags=re.MULTILINE).strip()
    # Remove all backslashes except for escaping quotes
    cleaned = re.sub(r'\\\\', '', cleaned)  # double backslash
    cleaned = re.sub(r'\\([\\nt$])', '', cleaned)  # \n, \t, \\$, etc.
    cleaned = cleaned.replace('$', 'USD')  # Replace $ with USD
    cleaned = cleaned.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    return cleaned

def parse_gemini_slides(text, topic):
    import re, ast
    objects = re.findall(r'{.*?}', text, re.DOTALL)
    slides = []
    palette = [["#003087", "#FFFFFF"], ["#22223B", "#F2E9E4"], ["#0A9396", "#E9D8A6"], ["#1A1A2E", "#E94560"]]
    for obj in objects:
        try:
            slide = ast.literal_eval(obj.replace('\n', ' '))
        except Exception:
            continue
        title = slide.get('slide_title') or slide.get('title') or 'Slide'
        bullets = slide.get('bullet_points') or slide.get('bullets') or []
        color_scheme = slide.get('color_scheme') or random.choice(palette)
        image_keywords = slide.get('image_keywords') or [topic]
        slides.append({
            'slide_title': title,
            'bullet_points': bullets,
            'color_scheme': color_scheme,
            'image_keywords': image_keywords
        })
    return slides

def get_slide_content(topic):
    prompt = f'''
    Generate a 5-slide PowerPoint presentation for the topic: "{topic}".
    For each slide, output a JSON object with ONLY these fields:
    - "slide_title": string
    - "bullet_points": array of 3-5 strings
    - "color_scheme": array of 2 hex color codes (e.g., ["#003087", "#FFFFFF"])
    - "image_keywords": array of 2-3 relevant keywords (e.g., ["healthcare", "doctor"])
    If you don't know color_scheme or image_keywords, still output them as arrays with default values.
    Output ONLY as a valid JSON array of such objects. Do NOT use any other field names. Do NOT use markdown, backticks, or explanations.
    '''
    url = gemini_url()
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7}
    }
    params = {"key": GEMINI_API_KEY}
    response = requests.post(url, headers=headers, params=params, json=data)
    result = response.json()
    text = result['candidates'][0]['content']['parts'][0]['text']
    print('Gemini RAW output:', text)
    slides = parse_gemini_slides(text, topic)
    return slides

def get_image_url(keywords):
    query = "+".join(keywords)
    url = f"https://api.unsplash.com/photos/random?query={query}&client_id={UNSPLASH_API_KEY}&orientation=landscape"
    response = requests.get(url)
    print('Unsplash API response:', response.status_code, response.text[:200])  # Debug print
    if response.status_code == 200:
        data = response.json()
        return data['urls']['regular']
    return None  # No image found

def parse_slide(slide_data, topic):
    title = slide_data.get('slide_title') or slide_data.get('title') or 'Slide'
    bullets = slide_data.get('bullet_points') or slide_data.get('bullets') or []
    color_scheme = slide_data.get('color_scheme')
    if not color_scheme:
        palette = [["#003087", "#FFFFFF"], ["#22223B", "#F2E9E4"], ["#0A9396", "#E9D8A6"], ["#1A1A2E", "#E94560"]]
        color_scheme = random.choice(palette)
    image_keywords = slide_data.get('image_keywords')
    if not image_keywords:
        image_keywords = [topic]
    return title, bullets, color_scheme, image_keywords

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050, debug=True)