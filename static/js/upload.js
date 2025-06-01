/**
 * StreamFlix Upload Handler
 * Manages movie uploads with progress tracking
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('Upload.js loaded');
    
    // Check if user is authenticated
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }
    
    // Set username in header
    const userData = JSON.parse(localStorage.getItem('user'));
    if (userData) {
        document.getElementById('user-name').textContent = userData.name;
    }
    
    // Handle poster file preview
    const posterInput = document.getElementById('poster');
    const posterPreview = document.getElementById('poster-preview');
    
    if (posterInput) {
        posterInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    posterPreview.innerHTML = `<img src="${e.target.result}" alt="Poster Preview">`;
                }
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Handle form submission
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const title = document.getElementById('title').value;
            const description = document.getElementById('description').value;
            const year = document.getElementById('year').value;
            const genre = document.getElementById('genre').value;
            const movieFile = document.getElementById('movie').files[0];
            const posterFile = document.getElementById('poster').files[0];
            
            if (!title || !description || !year || !genre || !movieFile || !posterFile) {
                alert('Please fill all required fields and select both movie and poster files.');
                return;
            }
            
            // Create FormData
            const formData = new FormData();
            formData.append('title', title);
            formData.append('description', description);
            formData.append('year', year);
            formData.append('genre', genre);
            formData.append('movie', movieFile);
            formData.append('poster', posterFile);
            
            // Show progress UI
            const movieProgress = document.getElementById('movie-progress');
            const progressBar = movieProgress.querySelector('.progress-bar');
            const progressText = movieProgress.querySelector('.progress-text');
            const uploadBtn = document.getElementById('upload-btn');
            
            movieProgress.style.display = 'block';
            uploadBtn.disabled = true;
            uploadBtn.textContent = 'Uploading...';
            
            console.log('Starting upload with token:', token);
            
            // Create AJAX request with progress tracking
            const xhr = new XMLHttpRequest();
            
            xhr.open('POST', '/api/upload', true);
            
            // Send both formats of authorization headers for compatibility
            xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            xhr.setRequestHeader('x-access-token', token);
            
            // Handle CSRF for Django
            const csrfToken = getCookie('csrftoken');
            if (csrfToken) {
                xhr.setRequestHeader('X-CSRFToken', csrfToken);
            }
            
            // Track upload progress
            xhr.upload.onprogress = function(e) {
                if (e.lengthComputable) {
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = percentComplete + '%';
                    progressText.textContent = percentComplete + '%';
                    console.log(`Upload progress: ${percentComplete}%`);
                }
            };
            
            // Handle response
            xhr.onload = function() {
                console.log('Upload response:', xhr.status, xhr.responseText);
                if (xhr.status === 201 || xhr.status === 200) {
                    let response;
                    try {
                        response = JSON.parse(xhr.responseText);
                    } catch (e) {
                        console.error('Error parsing response:', e);
                        response = { message: 'Movie uploaded successfully!' };
                    }
                    alert('Movie uploaded successfully!');
                    window.location.href = '/dashboard.html';
                } else if (xhr.status === 401) {
                    alert('Your session has expired. Please log in again.');
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');
                    window.location.href = '/login.html';
                } else {
                    let errorMessage = 'Upload failed.';
                    try {
                        const response = JSON.parse(xhr.responseText);
                        if (response.message) {
                            errorMessage = response.message;
                        }
                    } catch (e) {
                        console.error('Error parsing response:', e);
                    }
                    alert(errorMessage);
                    
                    // Reset UI
                    movieProgress.style.display = 'none';
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Upload Movie';
                }
            };
            
            // Handle network errors
            xhr.onerror = function() {
                console.error('Network error during upload');
                alert('Network error occurred. Please try again.');
                movieProgress.style.display = 'none';
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Upload Movie';
            };
            
            // Send the form data
            xhr.send(formData);
        });
    }
    
    // Helper function to get CSRF cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
