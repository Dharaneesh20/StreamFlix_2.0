/**
 * StreamFlix Main JavaScript
 * Handles home page functionality including movie loading and search
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('StreamFlix main.js loaded');
    
    // Get token if user is logged in
    const token = localStorage.getItem('token');
    
    // Update navigation based on authentication status
    updateNavigation(!!token);
    
    // Load popular movies for the homepage
    loadMovies();
    
    // Set up search functionality
    setupSearch();
});

// Update navigation based on authentication status
function updateNavigation(isAuthenticated) {
    const navLinks = document.getElementById('nav-links');
    const userSection = document.getElementById('user-section');
    
    if (isAuthenticated) {
        // User is logged in
        if (navLinks) {
            navLinks.innerHTML = `
                <a href="/index.html">Home</a>
                <a href="/dashboard.html">Dashboard</a>
                <a href="/favorites.html">Favorites</a>
                <a href="/upload.html">Upload</a>
            `;
        }
        
        if (userSection) {
            userSection.style.display = 'flex';
            const userData = JSON.parse(localStorage.getItem('user'));
            if (userData && userData.name) {
                document.getElementById('user-name').textContent = userData.name;
            }
        }
    } else {
        // User is not logged in
        if (navLinks) {
            navLinks.innerHTML = `
                <a href="/login.html">Login</a>
                <a href="/register.html">Register</a>
            `;
        }
        
        if (userSection) {
            userSection.style.display = 'none';
        }
    }
}

// Load popular movies
function loadMovies() {
    console.log('Loading popular movies...');
    const moviesContainer = document.getElementById('movies-container');
    
    if (!moviesContainer) {
        console.error('Movies container not found!');
        return;
    }
    
    // Show loading indicator
    moviesContainer.innerHTML = '<div class="loading">Loading movies...</div>';
    
    // Get auth token if user is logged in
    const token = localStorage.getItem('token');
    const headers = {};
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
        headers['x-access-token'] = token;
    }
    
    // Fetch movies from API
    fetch('/api/movies', { headers })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to fetch movies: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(movies => {
            console.log(`Loaded ${movies.length} movies`);
            
            if (!movies.length) {
                moviesContainer.innerHTML = '<p class="empty-state">No movies available yet.</p>';
                return;
            }
            
            // Clear loading message
            moviesContainer.innerHTML = '';
            
            // Display movies
            movies.forEach(movie => {
                const movieCard = document.createElement('div');
                movieCard.className = 'movie-card';
                movieCard.innerHTML = `
                    <img src="${movie.posterUrl}" alt="${movie.title}" class="movie-poster">
                    <div class="movie-info">
                        <h3 class="movie-title">${movie.title}</h3>
                        <div class="movie-meta">
                            <span>${movie.year}</span>
                            <span>${Math.floor(movie.duration / 60)} min</span>
                        </div>
                    </div>
                `;
                
                // Add click event
                movieCard.addEventListener('click', () => {
                    window.location.href = `/movie.html?id=${movie.id}`;
                });
                
                moviesContainer.appendChild(movieCard);
            });
        })
        .catch(error => {
            console.error('Error loading movies:', error);
            moviesContainer.innerHTML = `
                <p class="error-message">Failed to load movies: ${error.message}</p>
            `;
        });
}

// Set up search functionality
function setupSearch() {
    const searchBtn = document.getElementById('search-btn');
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    
    if (!searchBtn || !searchInput || !searchResults) {
        console.log('Search elements not found');
        return;
    }
    
    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    function performSearch() {
        const query = searchInput.value.trim();
        if (!query) return;
        
        console.log(`Searching for: ${query}`);
        
        // Show loading state
        searchResults.innerHTML = '<div class="loading">Searching...</div>';
        
        // Get auth token if available
        const token = localStorage.getItem('token');
        const headers = {};
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
            headers['x-access-token'] = token;
        }
        
        // Fetch search results
        fetch(`/api/search?q=${encodeURIComponent(query)}`, { headers })
            .then(response => response.json())
            .then(movies => {
                console.log(`Found ${movies.length} results for "${query}"`);
                
                if (movies.length === 0) {
                    searchResults.innerHTML = '<p class="empty-state">No movies found matching your search.</p>';
                    return;
                }
                
                // Clear loading message
                searchResults.innerHTML = '';
                
                // Display results
                movies.forEach(movie => {
                    const movieCard = document.createElement('div');
                    movieCard.className = 'movie-card';
                    movieCard.innerHTML = `
                        <img src="${movie.posterUrl}" alt="${movie.title}" class="movie-poster">
                        <div class="movie-info">
                            <h3 class="movie-title">${movie.title}</h3>
                            <div class="movie-meta">
                                <span>${movie.year}</span>
                                <span>${Math.floor(movie.duration / 60)} min</span>
                            </div>
                        </div>
                    `;
                    
                    // Add click event
                    movieCard.addEventListener('click', () => {
                        window.location.href = `/movie.html?id=${movie.id}`;
                    });
                    
                    searchResults.appendChild(movieCard);
                });
            })
            .catch(error => {
                console.error('Error searching movies:', error);
                searchResults.innerHTML = '<p class="error-message">Search failed. Please try again later.</p>';
            });
    }
}
