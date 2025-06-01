# StreamFlix - Video Streaming Platform


A Netflix-inspired video streaming platform built with Python Flask and vanilla JavaScript.

## ✨ Features

- **🎥 Video Streaming**
  - Adaptive bitrate streaming (2160p to 480p)
  - YouTube-style player controls
  - Quality selection during playback
- **🔐 Authentication**
  - JWT-based secure login/register
  - Password hashing
  - Protected routes
- **📊 User Features**
  - Watch history tracking
  - Favorites system
  - User dashboard with stats
  - Movie upload capability
- **🔍 Discovery**
  - Search functionality
  - Recommendations
  - Popular movies section
- **🛠 Admin Features**
  - Movie management
  - User activity monitoring
  - Content analytics

## 🛠 Technologies

**Backend**
- Python Flask
- SQLite Database
- FFmpeg (video processing)
- JWT Authentication
- RESTful API

**Frontend**
- Vanilla JavaScript
- CSS3 (No frameworks)
- HTML5 Video Player
- Responsive Design

## 🚀 Installation

### Prerequisites
- Python 3.8+
- FFmpeg (system-wide access)
- Modern web browser

```bash
# Clone repository
git clone https://github.com/yourusername/streamflix.git
cd streamflix

# Install dependencies
pip install flask flask-cors werkzeug pyjwt cryptography

# Initialize database (automatically created on first run)
python app.py
```

⚙ Configuration
   
Edit app.py: 
```bash
app.config.update({
    'SECRET_KEY': 'your-secret-key-here',
    'UPLOAD_FOLDER': './movies',
    'MAX_CONTENT_LENGTH': 5 * 1024 * 1024 * 1024  # 5GB limit
})
```

📂 Project Structure
```bash
streamflix/
├── static/
│   ├── css/          # Global styles
│   ├── js/           # Auth, player, main scripts
│   └── img/          # Logos & static images
├── templates/        # HTML pages
│   ├── index.html
│   ├── movie.html
│   ├── dashboard.html
│   └── ...other pages
├── movies/           # Uploaded media storage
├── database/         # SQLite database
├── app.py            # Main application
└── schema.sql        # DB schema
```

🌐 API Endpoints
```
Endpoint	Method	Description
/api/register-POST	User registration
/api/login-POST	User authentication
/api/movies-GET	List all movies
/api/movies/{id}-GET	Get movie details
/api/upload	POST-Upload new movie
/api/stream/{id}-GET	Stream video content
/api/favorites-POST	Add/remove favorites
/api/watch-history-POST	Update viewing progress
/api/search	GET-Search movies
```

### 🖥 Usage
#### 1.Registration

>> Visit /register.html to create an account
>> Requires: Name, Email, Password

#### 2.Uploading Content

>> Authenticated users can upload via /upload.html
>> Supported formats: MP4, MKV, AVI (up to 5GB)

#### 3.Watching Movies

>> Browse movies on homepage
>> Select quality (2160p to 480p)
>> Resume playback from watch history

#### 4.Managing Account

>> Update profile information
>> Change password
>> View watch statistics

### 🧪 Testing
```bash
# Run development server
python app.py

# Access in browser at:
http://localhost:5000
```
### 📜 License
MIT License - See LICENSE for details

## 🙏 Acknowledgments
> ### Flask development team

> ### FFmpeg contributors

> ### JWT.io documentation

> ### Netflix UI inspiration

## Note: This is a educational project. Not recommended for production use.


## This README provides:
> - Quick project overview
> - Easy installation guide
> - Clear documentation
> - API reference
> - Usage instructions
> - Project structure visualization
> - License information


