from fastapi import FastAPI
from app.routes import enrollment, chunks, utterances, webhooks

app = FastAPI(title="Selective Speaker Backend", version="0.1.0")

app.include_router(enrollment.router)
app.include_router(chunks.router)
app.include_router(utterances.router)
app.include_router(webhooks.router)


@app.get("/")
def root():
    return {"message": "Selective Speaker Backend API", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


# Uvicorn: uvicorn app.main:app --reload

