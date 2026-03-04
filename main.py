from fastapi import FastAPI
import shop_api.models
from shop_api.db.base import Base
from shop_api.db.session import engine
from fastapi import Depends, FastAPI, Header, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session
from shop_api.core.security import get_current_user

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
    pw = payload.password
    print("PW len chars:", len(pw), "bytes:", len(pw.encode("utf-8")))
    # Check username unique -> 409
    existing = db.query(UserDB).filter(UserDB.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    print("DEBUG password length:", len(payload.password), "value:", repr(payload.password[:30]))
    
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

    token = create_access_token(subject=user.username)    
    return TokenOut(access_token=token)



@app.get("/me", response_model=UserOut)
def me(current_user: UserDB = Depends(get_current_user)):
    return UserOut(id=current_user.id, username=current_user.username, is_admin=current_user.is_admin)