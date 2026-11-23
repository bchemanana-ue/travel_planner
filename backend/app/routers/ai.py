from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..database import get_db
from .. import models, schemas
from .auth import get_current_user


router = APIRouter(
    prefix="/ai",
    tags=["AI Integration"]
)


@router.post("/plans")
def save_ai_plan(
    plan: schemas.AITripPlanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Проверяем положительность ID мест
    if any(place_id <= 0 for place_id in plan.place_ids):
        raise HTTPException(
            status_code=400,
            detail="ID мест должны быть положительными числами"
        )

    # Проверяем отсутствие повторяющихся мест
    if len(plan.place_ids) != len(set(plan.place_ids)):
        raise HTTPException(
            status_code=400,
            detail="В списке есть повторяющиеся места"
        )

    try:
        # Получаем все места из базы данных
        places = []

        if plan.place_ids:
            places = db.query(models.Place).filter(
                models.Place.id.in_(plan.place_ids)
            ).all()

        # Проверяем, что все места существуют
        places_by_id = {
            place.id: place
            for place in places
        }

        for place_id in plan.place_ids:
            if place_id not in places_by_id:
                raise HTTPException(
                    status_code=404,
                    detail=f"Место с ID {place_id} не найдено"
                )

        # Создаём поездку
        new_trip = models.Trip(
            title=plan.title,
            destination=plan.destination,
            days=plan.days,
            user_id=current_user.id
        )

        db.add(new_trip)
        db.flush()

        # Добавляем места в маршрут
        for place_id in plan.place_ids:
            connection = models.TripPlace(
                trip_id=new_trip.id,
                place_id=place_id
            )

            db.add(connection)

        # Если AI передал бюджет, сохраняем его
        if plan.budget is not None:

            transport = Decimal(str(plan.budget.transport))
            accommodation = Decimal(str(plan.budget.accommodation))
            food = Decimal(str(plan.budget.food))
            activities = Decimal(str(plan.budget.activities))

            subtotal = (
                transport
                + accommodation
                + food
                + activities
            )

            reserve = subtotal * Decimal("0.10")
            total = subtotal + reserve

            new_budget = models.Budget(
                trip_id=new_trip.id,
                transport=transport,
                accommodation=accommodation,
                food=food,
                activities=activities,
                reserve=reserve,
                total=total
            )

            db.add(new_budget)

        # Сохраняем все изменения одной транзакцией
        db.commit()
        db.refresh(new_trip)

        return {
            "message": "План путешествия успешно сохранён",
            "trip_id": new_trip.id,
            "title": new_trip.title,
            "destination": new_trip.destination,
            "days": new_trip.days,
            "place_ids": plan.place_ids,
            "budget_created": plan.budget is not None
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Не удалось сохранить план путешествия"
        )