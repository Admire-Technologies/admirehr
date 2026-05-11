"""
WebSocket authentication middleware for Django Channels.
"""

import logging
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_string):
    """
    Get user from JWT token.
    """
    try:
        # Validate and decode the token
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']
        
        # Get the user from database
        user = User.objects.select_related('company', 'role').get(id=user_id)
        return user
    except (TokenError, InvalidToken, User.DoesNotExist) as e:
        logger.warning(f"Token validation failed: {str(e)}")
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens.
    
    Expects token in query string: ws://host/path/?token=<jwt_token>
    """
    
    async def __call__(self, scope, receive, send):
        # Get token from query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        if token:
            # Authenticate user with token
            scope['user'] = await get_user_from_token(token)
        else:
            # No token provided
            scope['user'] = AnonymousUser()
            logger.warning("WebSocket connection attempt without token")
        
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """
    Convenience function to wrap the inner ASGI application with JWT auth middleware.
    """
    return JWTAuthMiddleware(inner)
