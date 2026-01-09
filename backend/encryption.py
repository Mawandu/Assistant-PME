# encryption.py
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

load_dotenv()

# Récupère la clé principale depuis l'environnement
ENCRYPTION_KEY_STR = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY_STR:
    raise ValueError("ENCRYPTION_KEY environment variable not set. Generate one with 'openssl rand -hex 32'.")

# Convertit la clé hexadécimale en bytes
try:
    ENCRYPTION_KEY = bytes.fromhex(ENCRYPTION_KEY_STR)
    if len(ENCRYPTION_KEY) < 32: # Assure une longueur minimale pour la dérivation
         raise ValueError("ENCRYPTION_KEY must be at least 32 bytes (64 hex chars).")
except ValueError:
     raise ValueError("Invalid ENCRYPTION_KEY format in .env, expected hex.")


# Utilisation d'un salt statique (pour la dérivation de clé), acceptable ici car
# la clé principale est déjà secrète. Pour une sécurité accrue, on pourrait stocker
# un salt différent par donnée cryptée, mais cela complexifie la gestion.
# Assurez-vous que ce salt n'est pas trivial.
SALT = b'q\x8c\x1f\x9a\xee\xc5\x1f\xbf\xf6u\xd8\x81^\x07\xb1\xd1' # Changez ceci pour votre projet

# Dérive une clé utilisable par Fernet à partir de la clé principale et du salt
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=SALT,
    iterations=480000, # Nombre d'itérations recommandé
)
# Fernet attend une clé encodée en base64 URL-safe
derived_key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY))
fernet = Fernet(derived_key)

def encrypt_data(data: str) -> str:
    """Crypte une chaîne de caractères et retourne le résultat encodé en base64."""
    if not isinstance(data, str):
        raise TypeError("Data to encrypt must be a string.")
    encrypted_bytes = fernet.encrypt(data.encode('utf-8'))
    return encrypted_bytes.decode('utf-8') # Retourne une string

def decrypt_data(encrypted_data: str) -> str:
    """Décrypte une chaîne encodée en base64 et retourne la chaîne originale."""
    if not isinstance(encrypted_data, str):
         raise TypeError("Encrypted data must be a string.")
    try:
        decrypted_bytes = fernet.decrypt(encrypted_data.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        # Gérer les erreurs de décryptage (ex: token invalide, clé incorrecte)
        # Logguez l'erreur ici pour le débogage
        print(f"Decryption failed: {e}") # À remplacer par un vrai logging
        raise ValueError("Could not decrypt data. It might be corrupted or the key is wrong.")
