from flask import Flask, request, jsonify, send_file, Response, g, render_template
from flask_cors import CORS
import os
import json
import uuid
import shutil
import time
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import subprocess
import threading
import jwt
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId
import re

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['SECRET_KEY'] = 'streamflix_secret_key'

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['streamflix']
users_collection = db['users']
movies_collection = db['movies']
watch_history_collection = db['watch_history']
favorites_collection = db['favorites']

# Use absolute paths for all directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'movies')
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'mkv', 'avi', 'mov', 'wmv'}
app.config['MAX_CONTENT_LENGTH'] = 5000 * 1024 * 1024  # 5GB max upload size

# Create necessary directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Available quality presets
QUALITY_PRESETS = {
    '2160p': {'resolution': '3840x2160', 'bitrate': '20000k'},
    '1440p': {'resolution': '2560x1440', 'bitrate': '12000k'},
    '1080p': {'resolution': '1920x1080', 'bitrate': '8000k'},
    '720p': {'resolution': '1280x720', 'bitrate': '5000k'},
    '480p': {'resolution': '854x480', 'bitrate': '2500k'}
}

# Authentication helper functions
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            user = users_collection.find_one({'email': data['email']})
            
            if not user:
                return jsonify({'message': 'User not found!'}), 401
            
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(user, *args, **kwargs)
    
    return decorated

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Routes
@app.route('/')
def serve_index():
    return render_template('index.html')

@app.route('/<path:path>.html')
def serve_html(path):
    try:
        return render_template(f"{path}.html")
    except:
        return jsonify({'message': 'Page not found'}), 404

# This route is for serving static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_file(f"static/{filename}")

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('name') or not data.get('password'):
        return jsonify({'message': 'Missing required fields!'}), 400
    
    user = users_collection.find_one({'email': data['email']})
    
    if user:
        return jsonify({'message': 'User already exists!'}), 409
    
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    created_at = datetime.now().isoformat()
    
    user_id = users_collection.insert_one({
        'email': data['email'], 
        'name': data['name'], 
        'password': hashed_password, 
        'created_at': created_at
    }).inserted_id
    
    return jsonify({'message': 'User registered successfully!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password!'}), 400
    
    user = users_collection.find_one({'email': data['email']})
    
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'message': 'Invalid credentials!'}), 401
    
    token = jwt.encode({
        'email': user['email'],
        'name': user['name'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    user_data = {
        'email': user['email'],
        'name': user['name'],
        'createdAt': user['created_at']
    }
    
    return jsonify({'token': token, 'user': user_data}), 200

@app.route('/api/movies', methods=['GET'])
def get_movies():
    try:
        movies = list(movies_collection.find({}, {'file_path': 0}).sort('upload_date', -1))
        
        result = []
        for movie in movies:
            result.append({
                'id': str(movie['_id']),
                'title': movie['title'],
                'description': movie['description'],
                'year': movie['year'],
                'genre': movie['genre'],
                'duration': movie['duration'],
                'uploaderId': movie['uploader_id'],
                'uploadDate': movie['upload_date'],
                'views': movie['views'],
                'posterUrl': f'/api/posters/{os.path.basename(movie["poster_path"])}'
            })
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Error in get_movies: {str(e)}")
        return jsonify({'message': f'Error fetching movies: {str(e)}'}), 500

@app.route('/api/movies/<movie_id>', methods=['GET'])
def get_movie(movie_id):
    try:
        movie = movies_collection.find_one_and_update(
            {'_id': ObjectId(movie_id)},
            {'$inc': {'views': 1}}
        )
        
        if not movie:
            return jsonify({'message': 'Movie not found!'}), 404
            
        result = {
            'id': str(movie['_id']),
            'title': movie['title'],
            'description': movie['description'],
            'year': movie['year'],
            'genre': movie['genre'],
            'duration': movie['duration'],
            'uploaderId': movie['uploader_id'],
            'uploadDate': movie['upload_date'],
            'views': movie['views'] + 1,
            'posterUrl': f'/api/posters/{os.path.basename(movie["poster_path"])}',
            'videoUrl': f'/api/stream/{movie_id}'
        }
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Error getting movie: {str(e)}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/upload', methods=['POST'])
@token_required
def upload_movie(user):
    try:
        if 'movie' not in request.files or 'poster' not in request.files:
            return jsonify({'message': 'No file part!'}), 400

        movie_file = request.files['movie']
        poster_file = request.files['poster']

        if movie_file.filename == '' or poster_file.filename == '':
            return jsonify({'message': 'No selected file!'}), 400

        if not (allowed_file(movie_file.filename) and poster_file.filename.lower().endswith(('.png', '.jpg', '.jpeg'))):
            return jsonify({'message': 'File type not allowed!'}), 400

        title = request.form.get('title')
        description = request.form.get('description')
        year = request.form.get('year')
        genre = request.form.get('genre')

        if not all([title, description, year, genre]):
            return jsonify({'message': 'Missing required fields!'}), 400

        year = int(year)

        movie_filename = str(uuid.uuid4()) + '.' + movie_file.filename.rsplit('.', 1)[1].lower()
        poster_filename = str(uuid.uuid4()) + '.' + poster_file.filename.rsplit('.', 1)[1].lower()

        movie_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(int(time.time())))
        os.makedirs(movie_dir, exist_ok=True)

        movie_path = os.path.join(movie_dir, movie_filename)
        poster_path = os.path.join(movie_dir, poster_filename)

        movie_file.save(movie_path)
        poster_file.save(poster_path)

        try:
            result = subprocess.run([
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                movie_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

            duration = int(float(json.loads(result.stdout)['format']['duration']))
        except:
            duration = 0

        threading.Thread(target=generate_video_qualities, args=(movie_path, movie_dir)).start()

        upload_date = datetime.now().isoformat()
        
        movie_id = movies_collection.insert_one({
            'title': title,
            'description': description,
            'year': year,
            'genre': genre,
            'duration': duration,
            'uploader_id': user['email'],
            'upload_date': upload_date,
            'file_path': movie_path,
            'poster_path': poster_path,
            'views': 0
        }).inserted_id

        return jsonify({
            'message': 'Movie uploaded successfully!',
            'id': str(movie_id)
        }, 201)

    except Exception as e:
        print("Upload error:", str(e))
        return jsonify({'message': f'Upload failed: {str(e)}'}), 500

def generate_video_qualities(original_path, output_dir):
    filename = os.path.basename(original_path)
    name_without_ext = os.path.splitext(filename)[0]
    
    for quality, settings in QUALITY_PRESETS.items():
        output_file = os.path.join(output_dir, f"{name_without_ext}_{quality}.mp4")
        
        try:
            subprocess.run([
                'ffmpeg',
                '-i', original_path,
                '-vf', f"scale={settings['resolution']}",
                '-b:v', settings['bitrate'],
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-strict', 'experimental',
                output_file
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error generating {quality} version: {e}")

@app.route('/api/stream/<movie_id>')
def stream_video(movie_id):
    try:
        movie = movies_collection.find_one({'_id': ObjectId(movie_id)})
        
        if not movie:
            return jsonify({'message': 'Movie not found!'}), 404
        
        video_path = movie['file_path']
        
        if not os.path.exists(video_path):
            print(f"Error: Video file not found at path: {video_path}")
            return jsonify({'message': 'Video file not found!'}), 404

        # Get file size
        file_size = os.path.getsize(video_path)
        
        # Handle range requests
        range_header = request.headers.get('Range', None)
        
        if range_header:
            byte1, byte2 = 0, None
            match = re.search(r'(\d+)-(\d*)', range_header)
            groups = match.groups()
            
            if groups[0]:
                byte1 = int(groups[0])
            if groups[1]:
                byte2 = int(groups[1])
            
            if byte2 is None:
                byte2 = file_size - 1
            
            length = byte2 - byte1 + 1
            
            resp = Response(
                get_chunk(video_path, byte1, length),
                status=206,
                mimetype='video/mp4',
                content_type='video/mp4',
                direct_passthrough=True
            )
            
            resp.headers.add('Content-Range', f'bytes {byte1}-{byte2}/{file_size}')
            resp.headers.add('Accept-Ranges', 'bytes')
            resp.headers.add('Content-Length', str(length))
            return resp
        
        # Standard response for full file
        return Response(
            get_chunk(video_path, 0, file_size),
            mimetype='video/mp4',
            content_type='video/mp4',
            direct_passthrough=True
        )
    
    except Exception as e:
        print(f"Error streaming video: {str(e)}")
        return jsonify({'message': f'Error streaming video: {str(e)}'}), 500

def get_chunk(filename, start, length):
    with open(filename, 'rb') as f:
        f.seek(start)
        chunk = f.read(length)
    return chunk

@app.route('/api/posters/<path:filename>')
def get_poster(filename):
    movie = movies_collection.find_one({'poster_path': {'$regex': filename}})
    
    if not movie:
        return jsonify({'message': 'Poster not found!'}), 404
    
    return send_file(movie['poster_path'])

@app.route('/api/watch-history', methods=['POST'])
@token_required
def add_to_watch_history(user):
    data = request.get_json()
    
    if not data or not data.get('movieId'):
        return jsonify({'message': 'Missing movie ID!'}), 400
    
    movie_id = data['movieId']
    progress = data.get('progress', 0)
    watch_date = datetime.now().isoformat()
    
    history_id = watch_history_collection.insert_one({
        'user_id': user['email'],
        'movie_id': movie_id,
        'progress': progress,
        'watch_date': watch_date
    }).inserted_id
    
    return jsonify({
        'message': 'Added to watch history!',
        'id': str(history_id)
    }), 201

@app.route('/api/watch-history', methods=['GET'])
@token_required
def get_watch_history(user):
    history_cursor = watch_history_collection.find({'user_id': user['email']}).sort('watch_date', -1)
    
    result = []
    for item in history_cursor:
        movie = movies_collection.find_one({'_id': ObjectId(item['movie_id'])})
        if movie:
            result.append({
                'id': str(item['_id']),
                'movieId': item['movie_id'],
                'progress': item['progress'],
                'watchDate': item['watch_date'],
                'title': movie['title'],
                'year': movie['year'],
                'duration': movie['duration'],
                'genre': movie['genre'],
                'posterUrl': f'/api/posters/{os.path.basename(movie["poster_path"])}'
            })
    
    return jsonify(result), 200

@app.route('/api/watch-history/<history_id>', methods=['PUT'])
@token_required
def update_watch_progress(user, history_id):
    data = request.get_json()
    
    if not data or 'progress' not in data:
        return jsonify({'message': 'Missing progress!'}), 400
    
    progress = data['progress']
    
    watch_history_collection.update_one(
        {'_id': ObjectId(history_id), 'user_id': user['email']},
        {'$set': {'progress': progress, 'watch_date': datetime.now().isoformat()}}
    )
    
    return jsonify({'message': 'Progress updated!'}), 200

@app.route('/api/favorites', methods=['POST'])
@token_required
def add_to_favorites(user):
    data = request.get_json()
    
    if not data or not data.get('movieId'):
        return jsonify({'message': 'Missing movie ID!'}), 400
    
    movie_id = data['movieId']
    
    # Check if already in favorites
    favorite = favorites_collection.find_one({
        'user_id': user['email'],
        'movie_id': movie_id
    })
    
    if favorite:
        return jsonify({'message': 'Movie already in favorites!', 'id': str(favorite['_id'])}), 200
    
    added_date = datetime.now().isoformat()
    
    favorite_id = favorites_collection.insert_one({
        'user_id': user['email'],
        'movie_id': movie_id,
        'added_date': added_date
    }).inserted_id
    
    return jsonify({
        'message': 'Added to favorites!',
        'id': str(favorite_id)
    }), 201

@app.route('/api/favorites/<favorite_id>', methods=['DELETE'])
@token_required
def remove_from_favorites(user, favorite_id):
    favorites_collection.delete_one({
        '_id': ObjectId(favorite_id),
        'user_id': user['email']
    })
    
    return jsonify({'message': 'Removed from favorites!'}), 200

@app.route('/api/favorites', methods=['GET'])
@token_required
def get_favorites(user):
    favorites_cursor = favorites_collection.find({'user_id': user['email']}).sort('added_date', -1)
    
    result = []
    for item in favorites_cursor:
        movie = movies_collection.find_one({'_id': ObjectId(item['movie_id'])})
        if movie:
            result.append({
                'id': str(item['_id']),
                'movieId': item['movie_id'],
                'addedDate': item['added_date'],
                'title': movie['title'],
                'year': movie['year'],
                'duration': movie['duration'],
                'genre': movie['genre'],
                'posterUrl': f'/api/posters/{os.path.basename(movie["poster_path"])}'
            })
    
    return jsonify(result), 200

@app.route('/api/user/uploads', methods=['GET'])
@token_required
def get_user_uploads(user):
    uploads_cursor = movies_collection.find({'uploader_id': user['email']}).sort('upload_date', -1)
    
    result = []
    for movie in uploads_cursor:
        result.append({
            'id': str(movie['_id']),
            'title': movie['title'],
            'description': movie['description'],
            'year': movie['year'],
            'genre': movie['genre'],
            'duration': movie['duration'],
            'uploadDate': movie['upload_date'],
            'views': movie['views'],
            'posterUrl': f'/api/posters/{os.path.basename(movie["poster_path"])}'
        })
    
    return jsonify(result), 200

@app.route('/api/search', methods=['GET'])
def search_movies():
    query = request.args.get('q', '')
    if not query:
        return jsonify([]), 200
    
    search_regex = {'$regex': query, '$options': 'i'}
    movies_cursor = movies_collection.find({
        '$or': [
            {'title': search_regex},
            {'description': search_regex},
            {'genre': search_regex}
        ]
    }).sort('upload_date', -1)
    
    result = []
    for movie in movies_cursor:
        result.append({
            'id': str(movie['_id']),
            'title': movie['title'],
            'description': movie['description'],
            'year': movie['year'],
            'genre': movie['genre'],
            'duration': movie['duration'],
            'uploaderId': movie['uploader_id'],
            'uploadDate': movie['upload_date'],
            'views': movie['views'],
            'posterUrl': f'/api/posters/{os.path.basename(movie["poster_path"])}'
        })
    
    return jsonify(result), 200

@app.route('/api/user/update', methods=['POST'])
@token_required
def update_profile(user):
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'message': 'Name is required!'}), 400
    
    users_collection.update_one(
        {'email': user['email']},
        {'$set': {'name': data['name']}}
    )
    
    return jsonify({'message': 'Profile updated successfully'}), 200

@app.route('/api/user/change-password', methods=['POST'])
@token_required
def change_password(user):
    data = request.get_json()
    
    if not data or not data.get('currentPassword') or not data.get('newPassword'):
        return jsonify({'message': 'Current and new password are required!'}), 400
    
    user_data = users_collection.find_one({'email': user['email']})
    
    if not check_password_hash(user_data['password'], data['currentPassword']):
        return jsonify({'message': 'Current password is incorrect!'}), 401
    
    hashed_password = generate_password_hash(data['newPassword'], method='pbkdf2:sha256')
    users_collection.update_one(
        {'email': user['email']},
        {'$set': {'password': hashed_password}}
    )
    
    return jsonify({'message': 'Password changed successfully'}), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({'message': 'Endpoint not found. Please check the URL.'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'message': 'Internal server error occurred.'}), 500

if __name__ == '__main__':
    print(f"Starting StreamFlix server...")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    app.run(debug=True, host='0.0.0.0', port=5000)
