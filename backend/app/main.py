from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .config import settings
from .routers import router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BudgetBuddy API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router)


@app.get("/")
def root():
    return {"message": "BudgetBuddy Backend is Running"}


@app.get("/health")
def health():
    return {"status": "ok"}