"""
General-purpose encryption utilities for sensitive data.

This module provides encryption/decryption for sensitive personal information
to comply with GDPR and data protection standards.
"""

import base64
import json
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings

logger = logging.getLogger(__name__)


class DataEncryption:
    """
    Handles encryption and decryption of sensitive personal data.
    Uses Fernet (symmetric encryption) for secure data storage.
    """
    
    def __init__(self):
        """Initialize encryption with key derived from Django SECRET_KEY."""
        self._cipher = self._get_cipher()
    
    def _get_cipher(self):
        """
        Generate Fernet cipher from Django SECRET_KEY.
        Uses PBKDF2 to derive a proper encryption key.
        """
        # Use Django's SECRET_KEY as the password
        password = settings.SECRET_KEY.encode()
        
        # Use a fixed salt for general data encryption
        salt = b'admire_hrms_data_encryption_v1'
        
        # Derive a key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        return Fernet(key)
    
    def encrypt(self, data):
        """
        Encrypt sensitive data for secure storage.
        
        Args:
            data: String or dictionary to encrypt
        
        Returns:
            Encrypted string (base64 encoded)
        """
        if not data:
            return None
        
        try:
            # Convert to string if needed
            if isinstance(data, dict):
                data_str = json.dumps(data)
            else:
                data_str = str(data)
            
            # Encrypt
            encrypted = self._cipher.encrypt(data_str.encode())
            
            # Return as base64 string for storage
            return base64.b64encode(encrypted).decode('utf-8')
        
        except Exception as e:
            logger.error(f"Failed to encrypt data: {str(e)}")
            raise ValueError("Data encryption failed")
    
    def decrypt(self, encrypted_data):
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted string (base64 encoded)
        
        Returns:
            Decrypted string or dictionary
        """
        if not encrypted_data:
            return None
        
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Decrypt
            decrypted = self._cipher.decrypt(encrypted_bytes)
            decrypted_str = decrypted.decode()
            
            # Try to parse as JSON
            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                return decrypted_str
        
        except Exception as e:
            logger.error(f"Failed to decrypt data: {str(e)}")
            raise ValueError("Data decryption failed")
    
    def encrypt_field(self, value):
        """
        Encrypt a single field value.
        Convenience method for encrypting individual fields.
        
        Args:
            value: Value to encrypt (string, int, etc.)
        
        Returns:
            Encrypted string
        """
        if value is None:
            return None
        return self.encrypt(str(value))
    
    def decrypt_field(self, encrypted_value):
        """
        Decrypt a single field value.
        
        Args:
            encrypted_value: Encrypted string
        
        Returns:
            Decrypted value as string
        """
        if encrypted_value is None:
            return None
        return self.decrypt(encrypted_value)


# Singleton instance
_encryption_instance = None


def get_data_encryption():
    """
    Get singleton instance of DataEncryption.
    
    Returns:
        DataEncryption instance
    """
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = DataEncryption()
    return _encryption_instance


def encrypt_sensitive_data(data):
    """
    Helper function to encrypt sensitive data.
    
    Args:
        data: Data to encrypt
    
    Returns:
        Encrypted string
    """
    return get_data_encryption().encrypt(data)


def decrypt_sensitive_data(encrypted_data):
    """
    Helper function to decrypt sensitive data.
    
    Args:
        encrypted_data: Encrypted string
    
    Returns:
        Decrypted data
    """
    return get_data_encryption().decrypt(encrypted_data)
