"""
Face Plugin SDK integration service.

This module provides integration with the Face Plugin SDK for biometric
face recognition and verification. It handles face capture, encoding,
and matching against stored employee biometric data.
"""

import logging
import numpy as np
from typing import Dict, Optional, Tuple
from django.core.exceptions import ValidationError
from .encryption import get_biometric_encryption

logger = logging.getLogger(__name__)


class BiometricVerificationError(Exception):
    """Raised when biometric verification fails."""
    pass


class FacePluginService:
    """
    Service for integrating with Face Plugin SDK.
    
    This is a mock implementation that simulates Face Plugin SDK behavior.
    In production, this would integrate with the actual Face Plugin SDK library.
    """
    
    # Verification thresholds
    MATCH_THRESHOLD = 0.6  # Similarity threshold for face matching
    MIN_QUALITY_SCORE = 0.7  # Minimum quality score for face capture
    
    def __init__(self):
        """Initialize Face Plugin SDK service."""
        self.encryption = get_biometric_encryption()
        logger.info("Face Plugin SDK service initialized")
    
    def process_face_capture(self, biometric_data: Dict) -> Dict:
        """
        Process captured face data from the Face Plugin SDK.
        
        Args:
            biometric_data: Raw biometric data from Face Plugin SDK
                {
                    "face_image": "base64_encoded_image",
                    "face_encoding": [array of floats],
                    "quality_score": 0.95,
                    "capture_timestamp": "ISO datetime"
                }
        
        Returns:
            Processed and validated biometric data
        
        Raises:
            ValidationError: If biometric data is invalid or quality is too low
        """
        # Validate required fields
        if not biometric_data:
            raise ValidationError("Biometric data is required")
        
        if 'face_encoding' not in biometric_data:
            raise ValidationError("Face encoding is missing")
        
        # Check quality score
        quality_score = biometric_data.get('quality_score', 0)
        if quality_score < self.MIN_QUALITY_SCORE:
            raise ValidationError(
                f"Face capture quality too low: {quality_score}. "
                f"Minimum required: {self.MIN_QUALITY_SCORE}"
            )
        
        # Normalize face encoding
        face_encoding = self._normalize_encoding(biometric_data['face_encoding'])
        
        # Create processed biometric data
        processed_data = {
            'face_encoding': face_encoding,
            'quality_score': quality_score,
            'capture_timestamp': biometric_data.get('capture_timestamp'),
            'face_descriptor': {
                'encoding_version': '1.0',
                'algorithm': 'face_plugin_sdk',
                'dimensions': len(face_encoding)
            }
        }
        
        logger.info(f"Face capture processed with quality score: {quality_score}")
        return processed_data
    
    def verify_face(
        self, 
        captured_biometric: Dict, 
        stored_biometric_encrypted: str
    ) -> Tuple[bool, float]:
        """
        Verify captured face against stored employee biometric data.
        
        Args:
            captured_biometric: Processed biometric data from current capture
            stored_biometric_encrypted: Encrypted stored biometric data
        
        Returns:
            Tuple of (is_match: bool, similarity_score: float)
        
        Raises:
            BiometricVerificationError: If verification process fails
        """
        try:
            # Decrypt stored biometric data
            stored_biometric = self.encryption.decrypt_biometric_data(
                stored_biometric_encrypted
            )
            
            if not stored_biometric:
                raise BiometricVerificationError("No stored biometric data found")
            
            # Extract face encodings
            captured_encoding = captured_biometric.get('face_encoding')
            stored_encoding = stored_biometric.get('face_encoding')
            
            if not captured_encoding or not stored_encoding:
                raise BiometricVerificationError("Face encoding missing")
            
            # Calculate similarity
            similarity = self._calculate_similarity(captured_encoding, stored_encoding)
            
            # Determine if it's a match
            is_match = similarity >= self.MATCH_THRESHOLD
            
            logger.info(
                f"Face verification completed: match={is_match}, "
                f"similarity={similarity:.3f}"
            )
            
            return is_match, similarity
        
        except Exception as e:
            logger.error(f"Face verification failed: {str(e)}")
            raise BiometricVerificationError(f"Verification failed: {str(e)}")
    
    def enroll_face(self, biometric_data: Dict) -> str:
        """
        Enroll a new face for an employee.
        
        Args:
            biometric_data: Processed biometric data to store
        
        Returns:
            Encrypted biometric data string for storage
        """
        # Process the face capture
        processed_data = self.process_face_capture(biometric_data)
        
        # Encrypt for storage
        encrypted_data = self.encryption.encrypt_biometric_data(processed_data)
        
        logger.info("Face enrollment completed successfully")
        return encrypted_data
    
    def _normalize_encoding(self, encoding) -> list:
        """
        Normalize face encoding to standard format.
        
        Args:
            encoding: Face encoding array
        
        Returns:
            Normalized encoding as list
        """
        if isinstance(encoding, np.ndarray):
            encoding = encoding.tolist()
        elif not isinstance(encoding, list):
            encoding = list(encoding)
        
        return encoding
    
    def _calculate_similarity(self, encoding1: list, encoding2: list) -> float:
        """
        Calculate similarity between two face encodings.
        
        Uses cosine similarity for face matching.
        
        Args:
            encoding1: First face encoding
            encoding2: Second face encoding
        
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(encoding1)
            vec2 = np.array(encoding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Normalize to 0-1 range (cosine similarity is -1 to 1)
            similarity = (similarity + 1) / 2
            
            return float(similarity)
        
        except Exception as e:
            logger.error(f"Similarity calculation failed: {str(e)}")
            return 0.0
    
    def validate_biometric_data_structure(self, biometric_data: Dict) -> bool:
        """
        Validate the structure of biometric data.
        
        Args:
            biometric_data: Biometric data to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['face_encoding', 'quality_score']
        
        if not isinstance(biometric_data, dict):
            return False
        
        for field in required_fields:
            if field not in biometric_data:
                return False
        
        # Validate face encoding is a list/array
        if not isinstance(biometric_data['face_encoding'], (list, np.ndarray)):
            return False
        
        # Validate quality score is numeric
        try:
            float(biometric_data['quality_score'])
        except (TypeError, ValueError):
            return False
        
        return True


# Singleton instance
_face_plugin_service = None


def get_face_plugin_service() -> FacePluginService:
    """
    Get singleton instance of FacePluginService.
    
    Returns:
        FacePluginService instance
    """
    global _face_plugin_service
    if _face_plugin_service is None:
        _face_plugin_service = FacePluginService()
    return _face_plugin_service
