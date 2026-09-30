from datetime import datetime, timezone, timedelta
from typing import Optional
import jwt
import bcrypt
import hashlib
from bson import ObjectId

from app.database.connection import get_db
from app.config import get_settings


def hash_password(password: str) -> str:
    """Hash a password securely using SHA-256 pre-hashing + bcrypt."""
    pw_bytes = hashlib.sha256(password.encode('utf-8')).digest()
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against stored bcrypt hash."""
    try:
        pw_bytes = hashlib.sha256(plain_password.encode('utf-8')).digest()
        return bcrypt.checkpw(pw_bytes, hashed_password.encode('utf-8'))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.PyJWTError:
        return None


def format_user_doc(user_doc: dict) -> dict:
    return {
        "id": str(user_doc["_id"]),
        "email": user_doc["email"],
        "full_name": user_doc.get("full_name"),
        "created_at": user_doc.get("created_at")
    }


async def register_user(email: str, password: str, full_name: Optional[str] = None) -> dict:
    db = get_db()
    email_clean = email.strip().lower()
    
    # Check if user already exists
    existing = await db.users.find_one({"email": email_clean})
    if existing:
        raise ValueError("User with this email already exists")

    hashed_pw = hash_password(password)
    now = datetime.now(timezone.utc)

    user_doc = {
        "email": email_clean,
        "password_hash": hashed_pw,
        "full_name": full_name,
        "created_at": now,
        "updated_at": now
    }

    res = await db.users.insert_one(user_doc)
    user_doc["_id"] = res.inserted_id
    return format_user_doc(user_doc)


async def authenticate_user(email: str, password: str) -> Optional[dict]:
    db = get_db()
    email_clean = email.strip().lower()
    user = await db.users.find_one({"email": email_clean})
    if not user:
        return None
    if not verify_password(password, user.get("password_hash", "")):
        return None
    return format_user_doc(user)


async def get_user_by_id(user_id: str) -> Optional[dict]:
    if not ObjectId.is_valid(user_id):
        return None
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return None
    return format_user_doc(user)
