from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..database import get_db
from .. import models, schemas
from .auth import get_current_user


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


# Сохранение изменений в базе данных
def save_changes(db: Session, instance=None):
    try:
        db.commit()

        if instance is not None:
            db.refresh(instance)

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Не удалось сохранить сообщение"
        )


# Отправка сообщения пользователя
@router.post("/messages")
def create_message(
    message: schemas.ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not message.content.strip():
        raise HTTPException(
            status_code=422,
            detail="Сообщение не может быть пустым"
        )

    if message.trip_id is not None:
        trip = db.query(models.Trip).filter(
            models.Trip.id == message.trip_id,
            models.Trip.user_id == current_user.id
        ).first()

        if trip is None:
            raise HTTPException(
                status_code=404,
                detail="Поездка не найдена или не принадлежит пользователю"
            )

    new_message = models.ChatMessage(
        user_id=current_user.id,
        trip_id=message.trip_id,
        role="user",
        content=message.content
    )

    db.add(new_message)

    save_changes(db, new_message)

    return new_message


# Сохранение ответа AI
def save_assistant_message(
    user_id: int,
    content: str,
    db: Session,
    trip_id: int | None = None
):
    if not content or not content.strip():
        raise HTTPException(
            status_code=422,
            detail="Ответ AI не может быть пустым"
        )

    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )

    if trip_id is not None:
        trip = db.query(models.Trip).filter(
            models.Trip.id == trip_id,
            models.Trip.user_id == user_id
        ).first()

        if trip is None:
            raise HTTPException(
                status_code=404,
                detail="Поездка не найдена"
            )

    assistant_message = models.ChatMessage(
        user_id=user_id,
        trip_id=trip_id,
        role="assistant",
        content=content
    )

    db.add(assistant_message)

    save_changes(db, assistant_message)

    return assistant_message


# Получение истории переписки
@router.get("/messages")
def get_messages(
    trip_id: Annotated[int, Query(gt=0)] | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.ChatMessage).filter(
        models.ChatMessage.user_id == current_user.id
    )

    if trip_id is not None:
        trip = db.query(models.Trip).filter(
            models.Trip.id == trip_id,
            models.Trip.user_id == current_user.id
        ).first()

        if trip is None:
            raise HTTPException(
                status_code=404,
                detail="Поездка не найдена"
            )

        query = query.filter(
            models.ChatMessage.trip_id == trip_id
        )

    messages = query.order_by(
        models.ChatMessage.created_at
    ).all()

    return messages