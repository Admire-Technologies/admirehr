"""
Biometric data encryption and security utilities.

This module provides encryption/decryption for sensitive biometric data
to comply with privacy regulations and data protection standards.
"""

import base64
import json
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings

logger = logging.getLogger(__name__)


class BiometricEncryption:
    """
    Handles encryption and decryption of biometric data.
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
        
        # Use a fixed salt (in production, this should be stored securely)
        salt = b'admire_hrms_biometric_salt_v1'
        
        # Derive a key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        return Fernet(key)
    
    def encrypt_biometric_data(self, biometric_data):
        """
        Encrypt biometric data for secure storage.
        
        Args:
            biometric_data: Dictionary containing biometric information
                {
                    "face_encoding": [...],
                    "face_descriptor": {...},
                    "capture_timestamp": "ISO datetime",
                    "quality_score": 0.95
                }
        
        Returns:
            Encrypted string (base64 encoded)
        """
        if not biometric_data:
            return None
        
        try:
            # Convert to JSON string
            json_data = json.dumps(biometric_data)
            
            # Encrypt
            encrypted = self._cipher.encrypt(json_data.encode())
            
            # Return as base64 string for storage
            return base64.b64encode(encrypted).decode('utf-8')
        
        except Exception as e:
            logger.error(f"Failed to encrypt biometric data: {str(e)}")
            raise ValueError("Biometric data encryption failed")
    
    def decrypt_biometric_data(self, encrypted_data):
        """
        Decrypt biometric data for verification.
        
        Args:
            encrypted_data: Encrypted string (base64 encoded)
        
        Returns:
            Dictionary containing decrypted biometric information
        """
        if not encrypted_data:
            return None
        
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Decrypt
            decrypted = self._cipher.decrypt(encrypted_bytes)
            
            # Parse JSON
            return json.loads(decrypted.decode())
        
        except Exception as e:
            logger.error(f"Failed to decrypt biometric data: {str(e)}")
            raise ValueError("Biometric data decryption failed")
    
    def hash_biometric_template(self, biometric_data):
        """
        Create a one-way hash of biometric template for quick comparison.
        This can be used for indexing without storing raw biometric data.
        
        Args:
            biometric_data: Dictionary containing biometric information
        
        Returns:
            SHA256 hash string
        """
        if not biometric_data:
            return None
        
        try:
            # Convert to stable JSON representation
            json_data = json.dumps(biometric_data, sort_keys=True)
            
            # Create hash
            digest = hashes.Hash(hashes.SHA256())
            digest.update(json_data.encode())
            hash_bytes = digest.finalize()
            
            return base64.b64encode(hash_bytes).decode('utf-8')
        
        except Exception as e:
            logger.error(f"Failed to hash biometric template: {str(e)}")
            raise ValueError("Biometric template hashing failed")


# Singleton instance
_encryption_instance = None


def get_biometric_encryption():
    """
    Get singleton instance of BiometricEncryption.
    
    Returns:
        BiometricEncryption instance
    """
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = BiometricEncryption()
    return _encryption_instance
