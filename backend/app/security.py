import os
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from pwdlib import PasswordHash

ALGORITHM = "HS256"
SECRET = os.getenv("JWT_SECRET", "")
password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)

def create_access_token(subject: str) -> str:
    if len(SECRET) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters.")
    payload = {"sub": subject, "exp": datetime.now(timezone.utc) + timedelta(hours=12)}
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def decode_subject(token: str) -> str | None:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGORITHM]).get("sub")
    except JWTError:
        return None
