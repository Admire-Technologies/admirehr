"""
API Versioning and Backward Compatibility.
Implements URL path versioning and version-specific serializers.
"""
from rest_framework.versioning import URLPathVersioning
from rest_framework.exceptions import NotAcceptable


class APIVersioning(URLPathVersioning):
    """
    Custom API versioning class that supports URL path versioning.
    Example: /api/v1/employees/, /api/v2/employees/
    """
    default_version = 'v1'
    allowed_versions = ['v1', 'v2']
    version_param = 'version'

    def determine_version(self, request, *args, **kwargs):
        """
        Determine the API version from the URL path.
        Falls back to default version if not specified.
        """
        version = super().determine_version(request, *args, **kwargs)
        
        if version not in self.allowed_versions:
            raise NotAcceptable(
                f'Invalid API version "{version}". '
                f'Supported versions: {", ".join(self.allowed_versions)}'
            )
        
        return version


def get_serializer_class_for_version(base_serializer, version, model_name):
    """
    Get the appropriate serializer class based on API version.
    
    Args:
        base_serializer: The base serializer class
        version: API version string (e.g., 'v1', 'v2')
        model_name: Model name for version-specific serializers
        
    Returns:
        Serializer class for the specified version
    """
    # Try to import version-specific serializer
    try:
        module_path = f'apps.{model_name}.serializers_{version}'
        module = __import__(module_path, fromlist=[f'{model_name.capitalize()}Serializer'])
        return getattr(module, f'{model_name.capitalize()}Serializer')
    except (ImportError, AttributeError):
        # Fall back to base serializer if version-specific one doesn't exist
        return base_serializer


class VersionedSerializerMixin:
    """
    Mixin for views that need version-specific serializers.
    """
    
    def get_serializer_class(self):
        """
        Return the serializer class based on the API version.
        """
        base_serializer = super().get_serializer_class()
        version = self.request.version
        
        if hasattr(self, 'model_name'):
            return get_serializer_class_for_version(
                base_serializer,
                version,
                self.model_name
            )
        
        return base_serializer


class DeprecationWarningMixin:
    """
    Mixin to add deprecation warnings to API responses.
    """
    deprecated_version = None
    sunset_date = None
    replacement_url = None

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Add deprecation headers to the response if the version is deprecated.
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        
        if self.deprecated_version and request.version == self.deprecated_version:
            response['Warning'] = (
                f'299 - "API version {self.deprecated_version} is deprecated'
            )
            
            if self.sunset_date:
                response['Sunset'] = self.sunset_date
                response['Warning'] += f' and will be removed on {self.sunset_date}'
            
            if self.replacement_url:
                response['Link'] = f'<{self.replacement_url}>; rel="successor-version"'
            
            response['Warning'] += '"'
        
        return response


# Version-specific field mappings for backward compatibility
VERSION_FIELD_MAPPINGS = {
    'v1': {
        'employee': {
            # v1 field name: v2 field name
            'emp_id': 'employee_id',
            'dept': 'department',
        },
        'attendance': {
            'checkin': 'check_in',
            'checkout': 'check_out',
        }
    }
}


def transform_data_for_version(data, model_name, from_version, to_version):
    """
    Transform data between API versions using field mappings.
    
    Args:
        data: Dictionary of data to transform
        model_name: Model name (e.g., 'employee', 'attendance')
        from_version: Source API version
        to_version: Target API version
        
    Returns:
        Transformed data dictionary
    """
    if from_version == to_version:
        return data
    
    # Get field mappings for the model
    mappings = VERSION_FIELD_MAPPINGS.get(from_version, {}).get(model_name, {})
    
    if not mappings:
        return data
    
    # Transform field names
    transformed = {}
    for key, value in data.items():
        new_key = mappings.get(key, key)
        transformed[new_key] = value
    
    return transformed
