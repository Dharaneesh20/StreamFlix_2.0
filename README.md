# StreamFlix - Video Streaming Platform


A Netflix-inspired video streaming platform built with Python Flask and vanilla JavaScript.

## ✨ Features

- **🎥 Video Streaming**
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
- Django
- Mongo DB
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
- Mongo Shell
- Mongo Server
- Mongo DB Compass GUI
- Django
- FFmpeg (system-wide access)
- Modern web browser

```bash
# Clone repository
git clone https://github.com/Dharaneesh20/StreamFlix_2.0
cd Stream_Flix

# Install dependencies
pip install -r requirements.txt

# Create Super User
python manage.py createsuperuser

# Initialize database (automatically created on first run)
python manage.py runserver
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
python manage.py runserver

# Access in browser at:
http://localhost:5000
```
### 📜 License
MIT License - See LICENSE for details

## 🙏 Acknowledgments
> ### Django development team

> ### Mongo DB development team

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


