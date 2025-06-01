from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.contrib.auth.models import User
import jwt
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Try the standard Authorization header first
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        else:
            # Fall back to the x-access-token header for backward compatibility
            token = request.META.get('HTTP_X_ACCESS_TOKEN')
        
        if not token:
            return None
        
        try:
            # Decode the token
            logger.debug(f"Trying to decode token: {token[:10]}...")
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            logger.debug(f"Token payload: {payload}")
            
            # Check for different payload formats
            if 'email' in payload:
                # Original format with email
                user = User.objects.get(email=payload['email'])
            elif 'user_id' in payload:
                # Standard JWT format with user_id
                user = User.objects.get(id=payload['user_id'])
            elif 'username' in payload:
                # Format with username
                user = User.objects.get(username=payload['username'])
            else:
                # If none of the expected fields are found, try to use 'sub' (subject)
                # which is a standard JWT claim
                if 'sub' in payload:
                    user = User.objects.get(username=payload['sub'])
                else:
                    logger.error(f"No user identifier found in token payload: {payload}")
                    raise exceptions.AuthenticationFailed('Invalid token format')
            
            return (user, token)
        except jwt.ExpiredSignatureError:
            logger.error("Token expired")
            raise exceptions.AuthenticationFailed('Token has expired')
        except (jwt.DecodeError, jwt.InvalidTokenError) as e:
            logger.error(f"Invalid token: {str(e)}")
            raise exceptions.AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            logger.error("User not found")
            raise exceptions.AuthenticationFailed('User not found')
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise exceptions.AuthenticationFailed(f'Authentication error: {str(e)}')
