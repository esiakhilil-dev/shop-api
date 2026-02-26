from fastapi import FastAPI

from shop_api.db.base import Base
from shop_api.db.session import engine
from shop_api.models import user, product, order  # noqa: F401
from fastapi import Depends, FastAPI, Header, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from shop_api.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from shop_api.db.base import Base
from shop_api.db.deps import get_db
from shop_api.db.session import engine
from shop_api.models.user import UserDB
from shop_api.models import product, order  # noqa: F401  (keeps models registered)
from shop_api.schemas.user import TokenOut, UserCreate, UserLogin, UserOut
app = FastAPI(title="Shop API v1")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    # Check username unique -> 409
    existing = db.query(UserDB).filter(UserDB.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    user = UserDB(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(id=user.id, username=user.username, is_admin=user.is_admin)


@app.post("/login", response_model=TokenOut)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(subject=str(user.id))
    return TokenOut(access_token=token)


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> UserDB:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@app.get("/me", response_model=UserOut)
def me(current_user: UserDB = Depends(get_current_user)):
    return UserOut(id=current_user.id, username=current_user.username, is_admin=current_user.is_admin)