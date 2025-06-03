import os
import logging
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from src.config import config

logger = logging.getLogger('secure_config')

class SecureConfig:
    """Secure API key management with encryption"""
    
    def __init__(self, master_key=None):
        """
        Initialize the secure configuration manager
        
        Args:
            master_key: Optional master key for encryption, if not provided will use env var or generate
        """
        self.encryption_enabled = config.get("security", "encryption_enabled", False)
        
        if not self.encryption_enabled:
            logger.warning("Encryption is disabled. API keys will be stored in plain text.")
            self.key = None
            self.cipher = None
            return
            
        # Get or generate encryption key
        if master_key:
            self.key = self._derive_key(master_key)
        else:
            env_key = os.environ.get('ENCRYPTION_KEY')
            if env_key:
                try:
                    # Try to decode the key from base64
                    self.key = base64.urlsafe_b64decode(env_key)
                    logger.info("Using encryption key from environment variable")
                except Exception:
                    # If not valid base64, derive a key from it
                    self.key = self._derive_key(env_key)
                    logger.info("Derived encryption key from environment variable")
            else:
                self.key = Fernet.generate_key()
                logger.warning(f"Generated new encryption key: {self.key.decode()}. Store this in your env variables.")
        
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, password, salt=b'tradingbot'):
        """Derive a key from a password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_api_key(self, api_key):
        """Encrypt an API key"""
        if not self.encryption_enabled or not self.cipher:
            return api_key
            
        try:
            return self.cipher.encrypt(api_key.encode()).decode()
        except Exception as e:
            logger.error(f"Error encrypting API key: {e}")
            return api_key
    
    def decrypt_api_key(self, encrypted_key):
        """Decrypt an API key"""
        if not self.encryption_enabled or not self.cipher:
            return encrypted_key
            
        try:
            if isinstance(encrypted_key, str):
                encrypted_key = encrypted_key.encode()
            return self.cipher.decrypt(encrypted_key).decode()
        except Exception as e:
            logger.error(f"Error decrypting API key: {e}")
            return encrypted_key
    
    def secure_log(self, api_key):
        """Get a masked version of an API key for logging"""
        if not api_key:
            return None
            
        if len(api_key) <= 8:
            return "****"
            
        return api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:] 