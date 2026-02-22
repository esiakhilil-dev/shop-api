from fastapi import FastAPI

app = FastAPI(title="Shop API v1")

@app.get("/health")
def health():
    return {"status": "ok"}
