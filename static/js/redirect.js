/**
 * StreamFlix redirect and authentication handler
 * Checks authentication status and redirects accordingly
 */

document.addEventListener('DOMContentLoaded', () => {
    // Get current page
    const currentPage = window.location.pathname;
    
    // Check for authentication token
    const token = localStorage.getItem('token');
    const isAuthenticated = !!token;
    
    // Public pages that don't require authentication
    const publicPages = [
        '/index.html',
        '/',
        '/login.html',
        '/register.html'
    ];
    
    // Pages that require authentication
    const protectedPages = [
        '/dashboard.html',
        '/profile.html',
        '/favorites.html',
        '/upload.html',
        '/movie.html'
    ];
    
    // Get user data if available
    const userData = localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : null;
    
    // Check token expiration
    const isTokenExpired = () => {
        if (!token) return true;
        
        try {
            // Token structure is Header.Payload.Signature
            // We extract the payload
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
    
            const { exp } = JSON.parse(jsonPayload);
            
            // Check if the token has expired
            return Date.now() >= exp * 1000;
        } catch (e) {
            console.error('Error parsing token:', e);
            return true;
        }
    };
    
    // Handle navigation based on authentication status
    if (isTokenExpired()) {
        // Clear expired token
        if (token) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            
            // Show alert if trying to access protected page with expired token
            if (protectedPages.some(page => currentPage.includes(page))) {
                alert('Your session has expired. Please log in again.');
                window.location.href = '/login.html';
            }
        }
        
        // Redirect to login if trying to access protected page
        if (protectedPages.some(page => currentPage.includes(page))) {
            window.location.href = '/login.html';
        }
        
        // Update UI for logged out state
        const navLinks = document.getElementById('nav-links');
        const userSection = document.getElementById('user-section');
        
        if (navLinks) {
            navLinks.innerHTML = `
                <a href="/login.html">Login</a>
                <a href="/register.html">Register</a>
            `;
        }
        
        if (userSection) {
            userSection.style.display = 'none';
        }
    } else {
        // User is authenticated
        
        // Redirect to dashboard if trying to access login/register page
        if (['/login.html', '/register.html'].includes(currentPage)) {
            window.location.href = '/dashboard.html';
        }
        
        // Update UI for logged in state
        const navLinks = document.getElementById('nav-links');
        const userSection = document.getElementById('user-section');
        const userName = document.getElementById('user-name');
        
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
        }
        
        if (userName && userData) {
            userName.textContent = userData.name;
        }
        
        // Set up logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                
                window.location.href = '/login.html';
            });
        }
    }
});
