# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Header
import uuid
from fastapi.security import OAuth2PasswordRequestForm # Formulaire standard pour login
from sqlalchemy.orm import Session
import models, schemas, hashing,jwt_token as token # Importez vos modules
from jwt_token import verify_token
from database import get_db
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

router = APIRouter(
    tags=['Authentication']
)

@router.post("/api/v1/auth/login")
async def login(
    request: OAuth2PasswordRequestForm = Depends(), # Utilise le formulaire standard
    db: Session = Depends(get_db)
):
    """
    Connecte un utilisateur et retourne un token d'accès JWT.
    Attend 'username' (qui sera l'email ici) et 'password' dans le corps de la requête (form-data).
    """
    user = db.query(models.User).filter(models.User.email == request.username).first()

    # Vérifier si l'utilisateur existe
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid Credentials" # Message générique pour la sécurité
        )

    # Vérifier si le mot de passe est correct
    if not hashing.Hash.verify(user.password_hash, request.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Ou 401 Unauthorized, mais 404 est plus discret
            detail="Invalid Credentials"
        )

    # Si tout est OK, créer le token JWT
    # Le 'sub' (sujet) est souvent l'identifiant unique, ici l'email
    access_token_data = {
        "sub": user.email,
        "user_id": str(user.id), # Convertir UUID en string pour JWT
        "tenant_id": str(user.tenant_id)
        # Vous pouvez ajouter d'autres infos comme le rôle si nécessaire
        # "role": user.role.value
    }
    access_token = token.create_access_token(data=access_token_data)

    # Retourne le token et le type (standard OAuth2)
    return {"access_token": access_token, "token_type": "bearer"}

    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

def get_or_create_session_user(db: Session, client_id: str) -> models.User:
    """
    Finds or creates a user/tenant isolated for this client_id (session).
    """
    email = f"{client_id}@session.temp"
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if user:
        return user
        
    print(f"DEBUG: Creating new session user for {client_id}")
    # Create isolated tenant
    try:
        new_tenant = models.Tenant(company_name=f"Session {client_id}", subscription_tier=models.SubscriptionTier.STARTER)
        db.add(new_tenant)
        db.commit()
        db.refresh(new_tenant)
        
        # Create user
        # We need a dummy hash. 
        # hashed_pw = hashing.Hash.bcrypt("session") # Assuming hashing is available
        # Actually, let's just use a fixed string if verify checks it, but for session user we don't login via pwd usually.
        # But to be safe, valid hash.
        hashed_pw = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW" # "secret"
        
        new_user = models.User(
            email=email,
            password_hash=hashed_pw, 
            full_name="Guest User",
            tenant_id=new_tenant.id,
            role=models.UserRole.ADMIN
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        # Fallback to finding again if race condition
        user = db.query(models.User).filter(models.User.email == email).first()
        if user: return user
        raise e

async def get_current_user_or_default(
    token: str = Depends(oauth2_scheme_optional),
    x_client_id: str | None = Header(default=None),
    db: Session = Depends(get_db)
) -> models.User:
    if token:
        try:
             # We use a dummy exception here because we want to fallback if it fails
            dummy_exception = HTTPException(status_code=401)
            token_data = verify_token(token, dummy_exception)
            user = db.query(models.User).filter(models.User.email == token_data.email).first()
            if user:
                return user
        except Exception:
            pass # Fallback if token is invalid or expired
            
    # Check for Session Header
    if x_client_id:
        return get_or_create_session_user(db, x_client_id)
            
    # Fallback: Get first user in the DB (Legacy / Dev)
    # This is for dev/MVP to allow uploads without a full login flow in frontend
    user = db.query(models.User).first()
    if user:
        return user
    
    # Should not happen in seeded DB, but valid fallback
    raise HTTPException(status_code=401, detail="No default user found")
