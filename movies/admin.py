from django.contrib import admin
from .models import Movie, WatchHistory, Favorite

class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'genre', 'uploader', 'upload_date', 'views')
    search_fields = ('title', 'description', 'genre')
    list_filter = ('genre', 'year', 'upload_date')
    date_hierarchy = 'upload_date'

class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'progress', 'watch_date')
    search_fields = ('user__username', 'movie__title')
    list_filter = ('watch_date',)

class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'added_date')
    search_fields = ('user__username', 'movie__title')
    list_filter = ('added_date',)

admin.site.register(Movie, MovieAdmin)
admin.site.register(WatchHistory, WatchHistoryAdmin)
admin.site.register(Favorite, FavoriteAdmin)
