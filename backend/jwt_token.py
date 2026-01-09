# token.py
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration JWT ---
# IMPORTANT: Générez une clé secrète forte et unique pour votre production !
# Vous pouvez la générer avec : openssl rand -hex 32
# Stockez-la dans votre fichier .env
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "une_cle_secrete_faible_pour_le_dev")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)) # Token expire après 30 min par défaut

class TokenData(BaseModel):
    """Modèle Pydantic pour les données contenues dans le token."""
    email: str | None = None
    user_id: str | None = None
    tenant_id: str | None = None

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crée un nouveau token d'accès JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception: Exception) -> TokenData:
    """Vérifie un token JWT et retourne les données qu'il contient."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub") # "sub" est souvent utilisé pour le sujet (ici, l'email)
        user_id: str | None = payload.get("user_id")
        tenant_id: str | None = payload.get("tenant_id")

        if email is None or user_id is None or tenant_id is None:
            raise credentials_exception # Si des infos manquent

        token_data = TokenData(email=email, user_id=user_id, tenant_id=tenant_id)
    except JWTError:
        raise credentials_exception # Si le token est invalide ou expiré
    return token_data
