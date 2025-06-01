import logging

logger = logging.getLogger(__name__)

class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log the incoming request
        if request.path.startswith('/api/upload'):
            logger.info(f"REQUEST METHOD: {request.method}")
            logger.info(f"REQUEST PATH: {request.path}")
            logger.info(f"REQUEST HEADERS: {request.headers}")
            
            # Log authentication information
            auth_header = request.headers.get('Authorization', None)
            logger.info(f"AUTH HEADER: {auth_header}")
            
            # Log Django's authentication status
            logger.info(f"USER AUTHENTICATED: {request.user.is_authenticated}")
            logger.info(f"USER: {request.user}")

        # Process the request
        response = self.get_response(request)
        
        # Log the response status
        if request.path.startswith('/api/upload'):
            logger.info(f"RESPONSE STATUS: {response.status_code}")
            
        return response
