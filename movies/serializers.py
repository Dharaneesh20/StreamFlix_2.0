from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Movie, WatchHistory, Favorite

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    name = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'name', 'password']
    
    def create(self, validated_data):
        name = validated_data.pop('name')
        # Split name into first and last name
        name_parts = name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        email = validated_data.pop('email')
        # Use email as username
        username = email
        
        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        user.set_password(validated_data['password'])
        user.save()
        
        return user

class MovieSerializer(serializers.ModelSerializer):
    """Serializer for the Movie model"""
    uploaderId = serializers.SerializerMethodField()
    uploadDate = serializers.SerializerMethodField()
    posterUrl = serializers.SerializerMethodField()
    videoUrl = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    
    class Meta:
        model = Movie
        fields = ['id', 'title', 'description', 'year', 'genre', 'duration', 
                  'uploaderId', 'uploadDate', 'views', 'posterUrl', 'videoUrl']
    
    def get_id(self, obj):
        return obj.id
    
    def get_uploaderId(self, obj):
        return obj.uploader.email
    
    def get_uploadDate(self, obj):
        return obj.upload_date.isoformat()
    
    def get_posterUrl(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.poster_path.url) if obj.poster_path else None
    
    def get_videoUrl(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(f'/api/stream/{obj.id}') if obj.file_path else None

class WatchHistorySerializer(serializers.ModelSerializer):
    """Serializer for the WatchHistory model"""
    movieId = serializers.SerializerMethodField()
    watchDate = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    genre = serializers.SerializerMethodField()
    posterUrl = serializers.SerializerMethodField()
    
    class Meta:
        model = WatchHistory
        fields = ['id', 'movieId', 'progress', 'watchDate', 'title', 'year', 'duration', 'genre', 'posterUrl']
    
    def get_movieId(self, obj):
        return obj.movie.id
    
    def get_watchDate(self, obj):
        return obj.watch_date.isoformat()
    
    def get_title(self, obj):
        return obj.movie.title
    
    def get_year(self, obj):
        return obj.movie.year
    
    def get_duration(self, obj):
        return obj.movie.duration
    
    def get_genre(self, obj):
        return obj.movie.genre
    
    def get_posterUrl(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.movie.poster_path.url) if obj.movie.poster_path else None

class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for the Favorite model"""
    movieId = serializers.SerializerMethodField()
    addedDate = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    genre = serializers.SerializerMethodField()
    posterUrl = serializers.SerializerMethodField()
    
    class Meta:
        model = Favorite
        fields = ['id', 'movieId', 'addedDate', 'title', 'year', 'duration', 'genre', 'posterUrl']
    
    def get_movieId(self, obj):
        return obj.movie.id
    
    def get_addedDate(self, obj):
        return obj.added_date.isoformat()
    
    def get_title(self, obj):
        return obj.movie.title
    
    def get_year(self, obj):
        return obj.movie.year
    
    def get_duration(self, obj):
        return obj.movie.duration
    
    def get_genre(self, obj):
        return obj.movie.genre
    
    def get_posterUrl(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.movie.poster_path.url) if obj.movie.poster_path else None
