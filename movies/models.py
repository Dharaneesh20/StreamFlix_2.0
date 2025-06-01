import os
import uuid
import time
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

def movie_file_path(instance, filename):
    """Generate file path for new movie file"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    # Use current timestamp instead of instance's upload_date
    timestamp = int(time.time())
    return os.path.join('movies', str(timestamp), filename)

def poster_file_path(instance, filename):
    """Generate file path for new poster file"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    # Use current timestamp instead of instance's upload_date
    timestamp = int(time.time())
    return os.path.join('movies', str(timestamp), filename)

class Movie(models.Model):
    """Movie model"""
    title = models.CharField(max_length=255)
    description = models.TextField()
    year = models.IntegerField()
    genre = models.CharField(max_length=100)
    duration = models.IntegerField(default=0)  # in seconds
    uploader = models.ForeignKey(User, on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    file_path = models.FileField(upload_to=movie_file_path)
    poster_path = models.ImageField(upload_to=poster_file_path)
    views = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title

class WatchHistory(models.Model):
    """Watch history model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    progress = models.FloatField(default=0)  # 0 to 1 (percentage)
    watch_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Watch histories"
        
    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"

class Favorite(models.Model):
    """Favorite model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"
