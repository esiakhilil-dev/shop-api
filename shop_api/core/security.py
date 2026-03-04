from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from fastapi import Depends, HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from shop_api.core.config import settings
from shop_api.db.deps import get_db
from shop_api.models.user import UserDB
from shop_api.core.security import decode_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
def hash_password(password: str) -> str:
    # bcrypt only uses first 72 bytes
    pw = password.encode("utf-8")[:72]
    return pwd_context.hash(pw.decode("utf-8", errors="ignore"))

def verify_password(password: str, hashed: str) -> bool:
    pw = password.encode("utf-8")[:72]
    return pwd_context.verify(pw.decode("utf-8", errors="ignore"), hashed)

def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)

    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserDB:
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(UserDB).filter(UserDB.id == int(sub)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )