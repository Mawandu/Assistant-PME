# routers/user.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, hashing # Importez vos modules
from database import get_db

router = APIRouter(
    prefix="/api/v1/users", # Préfixe pour toutes les routes de ce router
    tags=['Users'] # Tag pour la documentation Swagger/OpenAPI
)

@router.post("/", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_request: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Crée un nouvel utilisateur.
    Requiert un email et un mot de passe (min 8 caractères).
    """
    # Vérifier si l'utilisateur existe déjà
    existing_user = db.query(models.User).filter(models.User.email == user_request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{user_request.email}' already exists."
        )

    # Hasher le mot de passe
    hashed_password = hashing.Hash.bcrypt(user_request.password)

    # Créer le nouvel utilisateur (TODO: Associer à un Tenant plus tard)
    # Pour l'instant, on suppose qu'un tenant_id est fourni ou on utilise un tenant par défaut
    # Ceci devra être amélioré lors de la gestion des tenants
    # Exemple temporaire (à remplacer par une vraie logique)
    default_tenant_id = None # Remplacez par une logique pour obtenir/créer un tenant
    first_tenant = db.query(models.Tenant).first()
    if first_tenant:
        default_tenant_id = first_tenant.id
    else:
         raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail="No default tenant found. Create a tenant first."
         )


    new_user = models.User(
        email=user_request.email,
        password_hash=hashed_password,
        full_name=user_request.full_name,
        tenant_id=default_tenant_id # ATTENTION: Logique temporaire
        # Le rôle par défaut est 'USER' (défini dans models.py)
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user) # Récupère l'ID généré et autres valeurs par défaut
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create user: {e}"
        )

    return new_user

# Ajoutez d'autres endpoints pour les utilisateurs ici (GET, PUT, DELETE...) si nécessaire
