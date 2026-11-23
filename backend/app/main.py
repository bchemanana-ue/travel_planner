from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .routers import trips, places, budgets, chat, auth, ai


app = FastAPI(
    title="Travel Planner",
    description="Приложение для планирования путешествий",
    version="1.0.0"
)


# Подключение роутеров
app.include_router(trips.router)
app.include_router(places.router)
app.include_router(budgets.router)
app.include_router(chat.router)
app.include_router(auth.router)
app.include_router(ai.router)


# Главная страница
@app.get("/")
def home():
    return {"message": "Travel Planner работает!"}


# Простая проверка работы приложения
@app.get("/health")
def health_check():
    return {"status": "ok"}


# Проверка готовности приложения и базы данных
@app.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "database": "connected"
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not ready",
                "database": "unavailable"
            }
        )