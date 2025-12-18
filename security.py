"""
Security Module for Smart Home IoT Simulation
Provides encryption, authentication, and secure communication
"""

import hashlib
import hmac
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from cryptography.fernet import Fernet
import json

class EncryptionManager:
    """Manages encryption/decryption for IoT data"""
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption manager
        
        Args:
            master_key: Master encryption key (generates new one if None)
        """
        if master_key:
            self.master_key = master_key.encode()
        else:
            # Generate a new master key
            self.master_key = Fernet.generate_key()
        
        self.cipher = Fernet(self.master_key)
        self.encryption_enabled = True
        self.total_encrypted = 0
        self.total_decrypted = 0
        
    def encrypt_data(self, data: str) -> Tuple[str, str]:
        """
        Encrypt data string
        
        Args:
            data: Plain text data to encrypt
            
        Returns:
            Tuple of (encrypted_data, encryption_method)
        """
        if not self.encryption_enabled:
            return data, "none"
        
        try:
            encrypted = self.cipher.encrypt(data.encode())
            self.total_encrypted += 1
            return base64.b64encode(encrypted).decode(), "AES-256"
        except Exception as e:
            print(f"Encryption error: {e}")
            return data, "failed"
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted plain text
        """
        if not self.encryption_enabled:
            return encrypted_data
        
        try:
            decoded = base64.b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            self.total_decrypted += 1
            return decrypted.decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return encrypted_data
    
    def encrypt_sensor_data(self, sensor_data: Dict) -> Dict:
        """
        Encrypt sensor data dictionary
        
        Args:
            sensor_data: Dictionary containing sensor information
            
        Returns:
            Dictionary with encrypted sensitive fields
        """
        if not self.encryption_enabled:
            return sensor_data
        
        encrypted_data = sensor_data.copy()
        
        # Encrypt sensitive fields
        sensitive_fields = ['value', 'location', 'room']
        for field in sensitive_fields:
            if field in encrypted_data:
                encrypted_value, method = self.encrypt_data(str(encrypted_data[field]))
                encrypted_data[f'{field}_encrypted'] = encrypted_value
                encrypted_data[f'{field}_encryption'] = method
                # Keep original for compatibility, mark as encrypted
                encrypted_data[field] = f"[ENCRYPTED]"
        
        encrypted_data['encryption_enabled'] = True
        encrypted_data['encryption_timestamp'] = datetime.now().isoformat()
        
        return encrypted_data
    
    def get_master_key_string(self) -> str:
        """Get master key as base64 string for storage"""
        return base64.b64encode(self.master_key).decode()
    
    def get_statistics(self) -> Dict:
        """Get encryption statistics"""
        return {
            'enabled': self.encryption_enabled,
            'total_encrypted': self.total_encrypted,
            'total_decrypted': self.total_decrypted,
            'algorithm': 'AES-256 (Fernet)'
        }


class AuthenticationManager:
    """Manages device authentication and access control"""
    
    def __init__(self):
        self.authenticated_devices = {}
        self.failed_attempts = {}
        self.max_failed_attempts = 3
        self.lockout_duration = timedelta(minutes=5)
        self.session_tokens = {}
        
    def generate_device_token(self, device_id: str) -> str:
        """Generate authentication token for device"""
        token = secrets.token_urlsafe(32)
        self.session_tokens[device_id] = {
            'token': token,
            'created': datetime.now(),
            'expires': datetime.now() + timedelta(hours=24)
        }
        return token
    
    def authenticate_device(self, device_id: str, token: str) -> bool:
        """
        Authenticate device with token
        
        Args:
            device_id: Device identifier
            token: Authentication token
            
        Returns:
            True if authenticated, False otherwise
        """
        # Check if device is locked out
        if device_id in self.failed_attempts:
            attempts, lockout_until = self.failed_attempts[device_id]
            if datetime.now() < lockout_until:
                return False
            else:
                # Lockout expired, clear failed attempts
                del self.failed_attempts[device_id]
        
        # Check token
        if device_id in self.session_tokens:
            session = self.session_tokens[device_id]
            if session['token'] == token and datetime.now() < session['expires']:
                self.authenticated_devices[device_id] = datetime.now()
                return True
        
        # Failed authentication
        self._record_failed_attempt(device_id)
        return False
    
    def _record_failed_attempt(self, device_id: str):
        """Record failed authentication attempt"""
        if device_id in self.failed_attempts:
            attempts, _ = self.failed_attempts[device_id]
            attempts += 1
        else:
            attempts = 1
        
        if attempts >= self.max_failed_attempts:
            lockout_until = datetime.now() + self.lockout_duration
            self.failed_attempts[device_id] = (attempts, lockout_until)
        else:
            self.failed_attempts[device_id] = (attempts, datetime.now())
    
    def is_device_authenticated(self, device_id: str) -> bool:
        """Check if device is currently authenticated"""
        return device_id in self.authenticated_devices
    
    def get_statistics(self) -> Dict:
        """Get authentication statistics"""
        return {
            'authenticated_devices': len(self.authenticated_devices),
            'active_sessions': len(self.session_tokens),
            'locked_devices': len([d for d, (a, t) in self.failed_attempts.items() 
                                   if datetime.now() < t and a >= self.max_failed_attempts])
        }


class SecureMessageValidator:
    """Validates message integrity using HMAC"""
    
    def __init__(self, secret_key: Optional[bytes] = None):
        self.secret_key = secret_key or secrets.token_bytes(32)
        self.validated_messages = 0
        self.failed_validations = 0
    
    def generate_signature(self, message: str) -> str:
        """Generate HMAC signature for message"""
        signature = hmac.new(
            self.secret_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def validate_message(self, message: str, signature: str) -> bool:
        """
        Validate message signature
        
        Args:
            message: Original message
            signature: HMAC signature to verify
            
        Returns:
            True if valid, False otherwise
        """
        expected_signature = self.generate_signature(message)
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if is_valid:
            self.validated_messages += 1
        else:
            self.failed_validations += 1
        
        return is_valid
    
    def sign_data(self, data: Dict) -> Dict:
        """Add signature to data dictionary"""
        data_copy = data.copy()
        message = json.dumps(data_copy, sort_keys=True)
        signature = self.generate_signature(message)
        data_copy['signature'] = signature
        data_copy['signed_at'] = datetime.now().isoformat()
        return data_copy
    
    def get_statistics(self) -> Dict:
        """Get validation statistics"""
        return {
            'validated_messages': self.validated_messages,
            'failed_validations': self.failed_validations,
            'success_rate': (self.validated_messages / 
                           (self.validated_messages + self.failed_validations) * 100
                           if (self.validated_messages + self.failed_validations) > 0 else 0)
        }


class SecurityManager:
    """Main security manager coordinating all security features"""
    
    def __init__(self, enable_encryption: bool = True, enable_authentication: bool = True):
        self.encryption = EncryptionManager() if enable_encryption else None
        self.authentication = AuthenticationManager() if enable_authentication else None
        self.message_validator = SecureMessageValidator()
        
        self.security_events = []
        self.max_events = 1000
        
    def secure_sensor_data(self, sensor_data: Dict, device_id: str) -> Dict:
        """
        Apply all security measures to sensor data
        
        Args:
            sensor_data: Raw sensor data
            device_id: Device identifier
            
        Returns:
            Secured data dictionary
        """
        secured_data = sensor_data.copy()
        
        # Add device authentication status
        if self.authentication:
            secured_data['authenticated'] = self.authentication.is_device_authenticated(device_id)
        
        # Encrypt sensitive data
        if self.encryption:
            secured_data = self.encryption.encrypt_sensor_data(secured_data)
        
        # Add message signature
        secured_data = self.message_validator.sign_data(secured_data)
        
        # Add security metadata
        secured_data['security_level'] = self._calculate_security_level()
        secured_data['secured_at'] = datetime.now().isoformat()
        
        return secured_data
    
    def _calculate_security_level(self) -> str:
        """Calculate overall security level"""
        features = []
        if self.encryption and self.encryption.encryption_enabled:
            features.append('encryption')
        if self.authentication:
            features.append('authentication')
        features.append('integrity')
        
        if len(features) >= 3:
            return 'high'
        elif len(features) >= 2:
            return 'medium'
        else:
            return 'low'
    
    def log_security_event(self, event_type: str, message: str, severity: str = 'info'):
        """Log security event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'message': message,
            'severity': severity
        }
        self.security_events.append(event)
        
        # Keep only recent events
        if len(self.security_events) > self.max_events:
            self.security_events = self.security_events[-self.max_events:]
    
    def get_security_status(self) -> Dict:
        """Get comprehensive security status"""
        status = {
            'security_level': self._calculate_security_level(),
            'timestamp': datetime.now().isoformat()
        }
        
        if self.encryption:
            status['encryption'] = self.encryption.get_statistics()
        
        if self.authentication:
            status['authentication'] = self.authentication.get_statistics()
        
        status['message_validation'] = self.message_validator.get_statistics()
        status['recent_events'] = len(self.security_events)
        
        return status
    
    def authenticate_all_devices(self, device_ids: list):
        """Authenticate all devices in the system"""
        if not self.authentication:
            return
        
        for device_id in device_ids:
            token = self.authentication.generate_device_token(device_id)
            self.authentication.authenticate_device(device_id, token)
            self.log_security_event('authentication', 
                                   f'Device {device_id} authenticated',
                                   'info')
