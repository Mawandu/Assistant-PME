# hashing.py
from passlib.context import CryptContext

# Configure le contexte de hachage, en utilisant bcrypt comme algorithme par défaut
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Hash():
    @staticmethod
    def bcrypt(password: str) -> str:
        """Hache un mot de passe en utilisant bcrypt."""
        # Truncate password to 72 bytes to comply with bcrypt limit
        truncated_password = password.encode('utf-8')[:72] # Encode to bytes first
        return pwd_context.hash(truncated_password) # Hash the truncated bytes

    @staticmethod
    def verify(hashed_password: str, plain_password: str) -> bool:
        """Vérifie si un mot de passe en clair correspond à un mot de passe haché."""
        # Also truncate the plain password during verification
        truncated_password = plain_password.encode('utf-8')[:72]
        return pwd_context.verify(truncated_password, hashed_password)
