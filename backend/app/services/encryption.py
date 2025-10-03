import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.config import settings


class EncryptionService:
    def __init__(self):
        self.secret_key = settings.secret_key.encode()
        self._fernet = None
    
    def _get_fernet(self) -> Fernet:
        """Get or create Fernet instance for encryption/decryption."""
        if self._fernet is None:
            # Derive key from secret key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'vas_salt',  # In production, use a random salt per encryption
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.secret_key))
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt_credentials(self, username: str, password: str) -> str:
        """Encrypt device credentials."""
        try:
            fernet = self._get_fernet()
            credentials = f"{username}:{password}"
            encrypted_data = fernet.encrypt(credentials.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            print(f"Error encrypting credentials: {e}")
            return ""
    
    def decrypt_credentials(self, encrypted_credentials: str) -> tuple:
        """Decrypt device credentials."""
        try:
            fernet = self._get_fernet()
            encrypted_data = base64.urlsafe_b64decode(encrypted_credentials.encode())
            decrypted_data = fernet.decrypt(encrypted_data)
            credentials = decrypted_data.decode()
            username, password = credentials.split(":", 1)
            return username, password
        except Exception as e:
            print(f"Error decrypting credentials: {e}")
            return "", ""
    
    def encrypt_text(self, text: str) -> str:
        """Encrypt any text data."""
        try:
            fernet = self._get_fernet()
            encrypted_data = fernet.encrypt(text.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            print(f"Error encrypting text: {e}")
            return ""
    
    def decrypt_text(self, encrypted_text: str) -> str:
        """Decrypt any text data."""
        try:
            fernet = self._get_fernet()
            encrypted_data = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted_data = fernet.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            print(f"Error decrypting text: {e}")
            return ""


# Global instance
encryption_service = EncryptionService() 