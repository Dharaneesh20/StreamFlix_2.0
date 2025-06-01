from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # HTML pages
    path('', views.index, name='index'),
    path('<path:path>.html', views.serve_html, name='serve_html'),
    
    # Authentication endpoints
    path('api/register', views.RegisterView.as_view(), name='register'),
    path('api/login', views.LoginView.as_view(), name='login'),
    
    # Movie endpoints
    path('api/movies', views.MovieListView.as_view(), name='movie-list'),
    path('api/movies/<int:pk>', views.MovieDetailView.as_view(), name='movie-detail'),
    path('api/upload', views.UploadMovieView.as_view(), name='upload-movie'),
    path('api/stream/<int:pk>', views.stream_video, name='stream-video'),
    path('api/posters/<str:filename>', views.get_poster, name='get-poster'),
    path('api/search', views.MovieSearchView.as_view(), name='movie-search'),
    
    # Watch history endpoints
    path('api/watch-history', views.WatchHistoryListCreateView.as_view(), name='watch-history-list'),
    path('api/watch-history/<int:pk>', views.WatchHistoryUpdateView.as_view(), name='watch-history-update'),
    
    # Favorites endpoints
    path('api/favorites', views.FavoriteListCreateView.as_view(), name='favorite-list'),
    path('api/favorites/<int:pk>', views.FavoriteDeleteView.as_view(), name='favorite-delete'),
    
    # User endpoints
    path('api/user/uploads', views.UserUploadsView.as_view(), name='user-uploads'),
    path('api/user/update', views.UserUpdateView.as_view(), name='user-update'),
    path('api/user/change-password', views.ChangePasswordView.as_view(), name='change-password'),
]
