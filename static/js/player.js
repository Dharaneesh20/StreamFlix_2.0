/**
 * StreamFlix Player
 * Handles loading and playing video content
 */

document.addEventListener('DOMContentLoaded', () => {
    // Get movie ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    const movieId = urlParams.get('id');
    
    if (!movieId) {
        console.error('No movie ID provided in URL');
        document.getElementById('movie-title').textContent = 'Movie not found';
        return;
    }

    const token = localStorage.getItem('token');
    
    // Load movie details
    fetch(`/api/movies/${movieId}`, {
        headers: {
            'x-access-token': token || ''
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to fetch movie details');
        }
        return response.json();
    })
    .then(movie => {
        console.log('Movie details loaded:', movie);
        
        // Set page title
        document.title = `${movie.title} - StreamFlix`;
        
        // Set movie details
        document.getElementById('movie-title').textContent = movie.title;
        document.getElementById('movie-description').textContent = movie.description;
        document.getElementById('movie-year').textContent = movie.year;
        
        const hours = Math.floor(movie.duration / 3600);
        const minutes = Math.floor((movie.duration % 3600) / 60);
        document.getElementById('movie-duration').textContent = hours > 0 
            ? `${hours}h ${minutes}m` 
            : `${minutes}m`;
            
        document.getElementById('movie-genre').textContent = movie.genre;
        document.getElementById('movie-views').textContent = `${movie.views} views`;
        document.getElementById('movie-uploader').textContent = movie.uploaderId;
        
        const uploadDate = new Date(movie.uploadDate).toLocaleDateString();
        document.getElementById('movie-upload-date').textContent = uploadDate;
        
        // Set video source - IMPORTANT: This is what was missing
        const videoPlayer = document.getElementById('video-player');
        videoPlayer.src = `/api/stream/${movieId}`;
        console.log('Video source set to:', videoPlayer.src);
        
        // Check if movie is in favorites
        checkFavoriteStatus(movieId);
        
        // Load recommended movies
        loadRecommendedMovies(movie.genre);
    })
    .catch(error => {
        console.error('Error loading movie:', error);
        document.getElementById('movie-title').textContent = 'Error loading movie';
    });

    // Favorite button functionality
    function checkFavoriteStatus(movieId) {
        if (!token) return;
        
        fetch('/api/favorites', {
            headers: {
                'x-access-token': token
            }
        })
        .then(response => response.json())
        .then(favorites => {
            const favBtn = document.getElementById('favorite-btn');
            const favorite = favorites.find(fav => fav.movieId === movieId);
            
            if (favorite) {
                favBtn.textContent = 'Remove from Favorites';
                favBtn.dataset.inFavorites = 'true';
                favBtn.dataset.favoriteId = favorite.id;
            } else {
                favBtn.textContent = 'Add to Favorites';
                favBtn.dataset.inFavorites = 'false';
            }
        });
    }

    // Handle favorite button click
    document.getElementById('favorite-btn').addEventListener('click', () => {
        if (!token) {
            window.location.href = '/login.html';
            return;
        }
        
        const favBtn = document.getElementById('favorite-btn');
        
        if (favBtn.dataset.inFavorites === 'true') {
            // Remove from favorites
            fetch(`/api/favorites/${favBtn.dataset.favoriteId}`, {
                method: 'DELETE',
                headers: {
                    'x-access-token': token
                }
            })
            .then(response => {
                if (response.ok) {
                    favBtn.textContent = 'Add to Favorites';
                    favBtn.dataset.inFavorites = 'false';
                    delete favBtn.dataset.favoriteId;
                }
            });
        } else {
            // Add to favorites
            fetch('/api/favorites', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-access-token': token
                },
                body: JSON.stringify({ movieId })
            })
            .then(response => response.json())
            .then(data => {
                favBtn.textContent = 'Remove from Favorites';
                favBtn.dataset.inFavorites = 'true';
                favBtn.dataset.favoriteId = data.id;
            });
        }
    });

    // Load recommended movies
    function loadRecommendedMovies(genre) {
        fetch(`/api/movies`, {
            headers: {
                'x-access-token': token || ''
            }
        })
        .then(response => response.json())
        .then(movies => {
            const container = document.getElementById('recommended-movies');
            const filteredMovies = movies
                .filter(movie => movie.genre === genre && movie.id !== movieId)
                .slice(0, 6);
                
            if (filteredMovies.length === 0) {
                container.innerHTML = '<p class="empty-state">No similar movies found.</p>';
                return;
            }
            
            container.innerHTML = '';  // Clear container
            
            filteredMovies.forEach(movie => {
                container.innerHTML += `
                    <div class="movie-card" onclick="window.location.href='/movie.html?id=${movie.id}'">
                        <img src="${movie.posterUrl}" alt="${movie.title}" class="movie-poster">
                        <div class="movie-info">
                            <h3 class="movie-title">${movie.title}</h3>
                            <div class="movie-meta">
                                <span>${movie.year}</span>
                                <span>${Math.floor(movie.duration / 60)} min</span>
                            </div>
                        </div>
                    </div>
                `;
            });
        })
        .catch(error => {
            console.error('Error loading recommendations:', error);
        });
    }

    // Track watch history
    function trackWatchHistory(movieId) {
        if (!token) return;
        
        const videoPlayer = document.getElementById('video-player');
        let historyId = null;
        let updateInterval = null;
        
        // Create initial history entry when playback starts
        videoPlayer.addEventListener('play', () => {
            if (historyId) return; // Already created
            
            fetch('/api/watch-history', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-access-token': token
                },
                body: JSON.stringify({
                    movieId,
                    progress: 0
                })
            })
            .then(response => response.json())
            .then(data => {
                historyId = data.id;
                
                // Update progress every 10 seconds
                updateInterval = setInterval(() => {
                    if (videoPlayer.duration) {
                        const progress = videoPlayer.currentTime / videoPlayer.duration;
                        
                        fetch(`/api/watch-history/${historyId}`, {
                            method: 'PUT',
                            headers: {
                                'Content-Type': 'application/json',
                                'x-access-token': token
                            },
                            body: JSON.stringify({
                                progress
                            })
                        });
                    }
                }, 10000);
            });
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
            
            if (historyId && videoPlayer.duration) {
                const progress = videoPlayer.currentTime / videoPlayer.duration;
                
                navigator.sendBeacon(
                    `/api/watch-history/${historyId}`,
                    JSON.stringify({
                        progress,
                        token
                    })
                );
            }
        });
    }

    // Start tracking history when movie is loaded
    if (movieId && token) {
        trackWatchHistory(movieId);
    }
});
