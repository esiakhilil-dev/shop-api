from fastapi import FastAPI

from shop_api.db.base import Base
from shop_api.db.session import engine
from shop_api.models import user, product, order  # noqa: F401

app = FastAPI(title="Shop API v1")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}