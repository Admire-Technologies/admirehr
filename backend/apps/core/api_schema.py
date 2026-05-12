"""
API Schema customization for DRF Spectacular.
Provides preprocessing and postprocessing hooks for enhanced API documentation.
"""
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object


def custom_preprocessing_hook(endpoints):
    """
    Preprocessing hook to customize API endpoints before schema generation.
    
    Args:
        endpoints: List of (path, path_regex, method, callback) tuples
        
    Returns:
        Filtered and customized endpoints list
    """
    # Filter out admin endpoints and internal APIs
    filtered = []
    for path, path_regex, method, callback in endpoints:
        # Skip admin URLs
        if path.startswith('/admin/'):
            continue
        # Skip internal WebSocket endpoints
        if 'ws/' in path:
            continue
        filtered.append((path, path_regex, method, callback))
    
    return filtered


def custom_postprocessing_hook(result, generator, request, public):
    """
    Postprocessing hook to enhance the generated OpenAPI schema.
    
    Args:
        result: The generated OpenAPI schema dictionary
        generator: The schema generator instance
        request: The HTTP request object
        public: Boolean indicating if this is a public schema
        
    Returns:
        Enhanced OpenAPI schema dictionary
    """
    # Add custom examples to common response schemas
    if 'components' in result and 'schemas' in result['components']:
        schemas = result['components']['schemas']
        
        # Add example for error responses
        if 'Error' not in schemas:
            schemas['Error'] = {
                'type': 'object',
                'properties': {
                    'error': {
                        'type': 'string',
                        'description': 'Error code or type',
                        'example': 'validation_error'
                    },
                    'message': {
                        'type': 'string',
                        'description': 'Human-readable error message',
                        'example': 'Invalid input data'
                    },
                    'details': {
                        'type': 'object',
                        'description': 'Additional error details',
                        'example': {'field': ['This field is required.']}
                    }
                }
            }
    
    # Add common response examples to paths
    if 'paths' in result:
        for path, methods in result['paths'].items():
            for method, operation in methods.items():
                if method in ['get', 'post', 'put', 'patch', 'delete']:
                    # Add common error responses
                    if 'responses' not in operation:
                        operation['responses'] = {}
                    
                    # Add 401 Unauthorized response
                    if '401' not in operation['responses']:
                        operation['responses']['401'] = {
                            'description': 'Unauthorized - Invalid or missing authentication token',
                            'content': {
                                'application/json': {
                                    'schema': {'$ref': '#/components/schemas/Error'},
                                    'example': {
                                        'error': 'authentication_failed',
                                        'message': 'Authentication credentials were not provided.'
                                    }
                                }
                            }
                        }
                    
                    # Add 403 Forbidden response for protected endpoints
                    if '403' not in operation['responses'] and 'auth' not in path:
                        operation['responses']['403'] = {
                            'description': 'Forbidden - Insufficient permissions',
                            'content': {
                                'application/json': {
                                    'schema': {'$ref': '#/components/schemas/Error'},
                                    'example': {
                                        'error': 'permission_denied',
                                        'message': 'You do not have permission to perform this action.'
                                    }
                                }
                            }
                        }
                    
                    # Add 500 Internal Server Error response
                    if '500' not in operation['responses']:
                        operation['responses']['500'] = {
                            'description': 'Internal Server Error',
                            'content': {
                                'application/json': {
                                    'schema': {'$ref': '#/components/schemas/Error'},
                                    'example': {
                                        'error': 'internal_error',
                                        'message': 'An unexpected error occurred.'
                                    }
                                }
                            }
                        }
    
    return result


class JWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    Custom JWT authentication scheme for API documentation.
    """
    target_class = 'rest_framework_simplejwt.authentication.JWTAuthentication'
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name='Authorization',
            token_prefix='Bearer',
            bearer_format='JWT',
        )
