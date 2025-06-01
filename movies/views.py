import os
import re
import subprocess
import threading
import json
import time
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.conf import settings
from django.contrib.auth import authenticate
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Movie, WatchHistory, Favorite
from .serializers import (
    UserSerializer, RegisterSerializer, MovieSerializer,
    WatchHistorySerializer, FavoriteSerializer
)

# Quality presets for video transcoding
QUALITY_PRESETS = {
    '2160p': {'resolution': '3840x2160', 'bitrate': '20000k'},
    '1440p': {'resolution': '2560x1440', 'bitrate': '12000k'},
    '1080p': {'resolution': '1920x1080', 'bitrate': '8000k'},
    '720p': {'resolution': '1280x720', 'bitrate': '5000k'},
    '480p': {'resolution': '854x480', 'bitrate': '2500k'}
}

# Template views
def index(request):
    """Render index page"""
    return render(request, 'index.html')

def serve_html(request, path):
    """Serve HTML templates"""
    try:
        return render(request, f"{path}.html")
    except:
        return JsonResponse({'message': 'Page not found'}, status=404)

# Authentication views
class RegisterView(generics.CreateAPIView):
    """Register a new user"""
    serializer_class = RegisterSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'User registered successfully!',
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    """Login a user"""
    def post(self, request):
        data = request.data
        if not data or not data.get('email') or not data.get('password'):
            return Response({'message': 'Missing email or password!'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Use the email to find the user
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            return Response({'message': 'Invalid credentials!'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check password
        if not user.check_password(data['password']):
            return Response({'message': 'Invalid credentials!'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate token with standard claims
        refresh = RefreshToken.for_user(user)
        
        # Add custom claims
        refresh['name'] = f"{user.first_name} {user.last_name}".strip()
        refresh['email'] = user.email  # Add email to payload for compatibility
        
        # Create user data response
        name = refresh['name'] or user.username
            
        user_data = {
            'email': user.email,
            'name': name,
            'createdAt': user.date_joined.isoformat()
        }
        
        return Response({
            'token': str(refresh.access_token),
            'user': user_data
        }, status=status.HTTP_200_OK)

# Movie views
class MovieListView(generics.ListAPIView):
    """List all movies"""
    queryset = Movie.objects.all().order_by('-upload_date')
    serializer_class = MovieSerializer

class MovieDetailView(generics.RetrieveAPIView):
    """Get movie details"""
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment views
        instance.views += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

# Fix upload movie view to handle JWT authentication properly
class UploadMovieView(APIView):
    """Upload a new movie"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        print("Received upload request with headers:", request.headers)
        print("Authentication info:", request.auth)
        
        if 'movie' not in request.FILES or 'poster' not in request.FILES:
            return Response({'message': 'No file part!'}, status=status.HTTP_400_BAD_REQUEST)
        
        movie_file = request.FILES['movie']
        poster_file = request.FILES['poster']
        
        if not movie_file or not poster_file:
            return Response({'message': 'No selected file!'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check file extensions
        movie_ext = os.path.splitext(movie_file.name)[1][1:].lower()
        poster_ext = os.path.splitext(poster_file.name)[1][1:].lower()
        
        if movie_ext not in settings.ALLOWED_EXTENSIONS or poster_ext not in ['png', 'jpg', 'jpeg']:
            return Response({'message': 'File type not allowed!'}, status=status.HTTP_400_BAD_REQUEST)
        
        title = request.POST.get('title')
        description = request.POST.get('description')
        year = request.POST.get('year')
        genre = request.POST.get('genre')
        
        if not all([title, description, year, genre]):
            return Response({'message': 'Missing required fields!'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            year = int(year)
        except ValueError:
            return Response({'message': 'Year must be a number!'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create movie object (without files first)
            movie = Movie(
                title=title,
                description=description,
                year=year,
                genre=genre,
                uploader=request.user
            )
            
            # Save files - this will trigger the upload_to functions
            movie.file_path.save(movie_file.name, movie_file)
            movie.poster_path.save(poster_file.name, poster_file)
            
            # Save the model to database
            movie.save()
            
            # Get duration using FFmpeg
            try:
                result = subprocess.run([
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'json',
                    movie.file_path.path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                
                duration = int(float(json.loads(result.stdout)['format']['duration']))
                movie.duration = duration
                movie.save()
            except Exception as e:
                print(f"Error getting duration: {str(e)}")
            
            # Start transcoding in background
            threading.Thread(
                target=generate_video_qualities,
                args=(movie.file_path.path, os.path.dirname(movie.file_path.path))
            ).start()
            
            return Response({
                'message': 'Movie uploaded successfully!',
                'id': movie.id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Error during upload: {str(e)}")
            return Response({'message': f'Upload failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def generate_video_qualities(original_path, output_dir):
    """Generate different quality versions of the video"""
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

def stream_video(request, pk):
    """Stream video file"""
    try:
        movie = get_object_or_404(Movie, pk=pk)
        
        if not os.path.exists(movie.file_path.path):
            return JsonResponse({'message': 'Video file not found!'}, status=404)
        
        # Get file size
        file_size = os.path.getsize(movie.file_path.path)
        
        # Handle range requests
        range_header = request.META.get('HTTP_RANGE', '').strip()
        
        if range_header:
            range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)
            
            if range_match:
                start_byte = int(range_match.group(1))
                end_byte = int(range_match.group(2)) if range_match.group(2) else file_size - 1
                
                if end_byte >= file_size:
                    end_byte = file_size - 1
                
                length = end_byte - start_byte + 1
                
                resp = HttpResponse(content_type='video/mp4')
                resp['Content-Length'] = str(length)
                resp['Content-Range'] = f'bytes {start_byte}-{end_byte}/{file_size}'
                resp['Accept-Ranges'] = 'bytes'
                resp.status_code = 206
                
                # Open the file and seek to the requested byte range
                with open(movie.file_path.path, 'rb') as file:
                    file.seek(start_byte)
                    resp.write(file.read(length))
                
                return resp
        
        # If no range header or invalid range, return the whole file
        response = FileResponse(open(movie.file_path.path, 'rb'), content_type='video/mp4')
        response['Content-Length'] = file_size
        response['Accept-Ranges'] = 'bytes'
        return response
    
    except Exception as e:
        print(f"Error streaming video: {str(e)}")
        return JsonResponse({'message': f'Error streaming video: {str(e)}'}, status=500)

def get_poster(request, filename):
    """Serve movie poster"""
    try:
        movie = Movie.objects.filter(poster_path__contains=filename).first()
        
        if not movie:
            return JsonResponse({'message': 'Poster not found!'}, status=404)
        
        return FileResponse(open(movie.poster_path.path, 'rb'))
    except Exception as e:
        return JsonResponse({'message': f'Error: {str(e)}'}, status=500)

class MovieSearchView(generics.ListAPIView):
    """Search for movies"""
    serializer_class = MovieSerializer
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if not query:
            return Movie.objects.none()
        
        return Movie.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(genre__icontains=query)
        ).order_by('-upload_date')

# Watch history views
class WatchHistoryListCreateView(generics.ListCreateAPIView):
    """List or create watch history entries"""
    serializer_class = WatchHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WatchHistory.objects.filter(user=self.request.user).order_by('-watch_date')
    
    def create(self, request, *args, **kwargs):
        movie_id = request.data.get('movieId')
        progress = request.data.get('progress', 0)
        
        if not movie_id:
            return Response({'message': 'Missing movie ID!'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            movie = Movie.objects.get(pk=movie_id)
        except Movie.DoesNotExist:
            return Response({'message': 'Movie not found!'}, status=status.HTTP_404_NOT_FOUND)
        
        # Create or update watch history
        watch_history, created = WatchHistory.objects.update_or_create(
            user=request.user,
            movie=movie,
            defaults={'progress': progress}
        )
        
        return Response({
            'message': 'Added to watch history!',
            'id': watch_history.id
        }, status=status.HTTP_201_CREATED)

class WatchHistoryUpdateView(generics.UpdateAPIView):
    """Update watch history progress"""
    serializer_class = WatchHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WatchHistory.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        progress = request.data.get('progress')
        
        if progress is None:
            return Response({'message': 'Missing progress!'}, status=status.HTTP_400_BAD_REQUEST)
        
        instance = self.get_object()
        instance.progress = progress
        instance.save()
        
        return Response({'message': 'Progress updated!'}, status=status.HTTP_200_OK)

# Favorites views
class FavoriteListCreateView(generics.ListCreateAPIView):
    """List or create favorite entries"""
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).order_by('-added_date')
    
    def create(self, request, *args, **kwargs):
        movie_id = request.data.get('movieId')
        
        if not movie_id:
            return Response({'message': 'Missing movie ID!'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            movie = Movie.objects.get(pk=movie_id)
        except Movie.DoesNotExist:
            return Response({'message': 'Movie not found!'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already in favorites
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            movie=movie
        )
        
        if not created:
            return Response({
                'message': 'Movie already in favorites!',
                'id': favorite.id
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'Added to favorites!',
            'id': favorite.id
        }, status=status.HTTP_201_CREATED)

class FavoriteDeleteView(generics.DestroyAPIView):
    """Delete a favorite entry"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'message': 'Removed from favorites!'}, status=status.HTTP_200_OK)

# User views
class UserUploadsView(generics.ListAPIView):
    """List movies uploaded by the current user"""
    serializer_class = MovieSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Movie.objects.filter(uploader=self.request.user).order_by('-upload_date')

class UserUpdateView(APIView):
    """Update user profile"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        name = request.data.get('name')
        
        if not name:
            return Response({'message': 'Name is required!'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Split name into first and last name
        name_parts = name.split(' ', 1)
        request.user.first_name = name_parts[0]
        request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        request.user.save()
        
        return Response({'message': 'Profile updated successfully'}, status=status.HTTP_200_OK)

class ChangePasswordView(APIView):
    """Change user password"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        current_password = request.data.get('currentPassword')
        new_password = request.data.get('newPassword')
        
        if not current_password or not new_password:
            return Response({'message': 'Current and new password are required!'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check current password
        if not request.user.check_password(current_password):
            return Response({'message': 'Current password is incorrect!'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Set new password
        request.user.set_password(new_password)
        request.user.save()
        
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
