from decimal import Decimal

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..database import get_db
from .. import models, schemas
from .auth import get_current_user


router = APIRouter(
    prefix="/budgets",
    tags=["Budgets"]
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
            detail="Не удалось сохранить изменения"
        )


# Расчёт общей стоимости и резерва
def calculate_totals(budget):
    transport = Decimal(str(budget.transport))
    accommodation = Decimal(str(budget.accommodation))
    food = Decimal(str(budget.food))
    activities = Decimal(str(budget.activities))

    subtotal = (
        transport
        + accommodation
        + food
        + activities
    )

    reserve = subtotal * Decimal("0.10")
    total = subtotal + reserve

    return reserve, total


# Создание бюджета
@router.post("/{trip_id}")
def calculate_budget(
    trip_id: Annotated[int, Path(gt=0)],
    budget: schemas.BudgetCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()

    if trip is None:
        raise HTTPException(
            status_code=404,
            detail="Поездка не найдена"
        )

    existing_budget = db.query(models.Budget).filter(
        models.Budget.trip_id == trip_id
    ).first()

    if existing_budget is not None:
        raise HTTPException(
            status_code=400,
            detail="Бюджет для этой поездки уже существует"
        )

    reserve, total = calculate_totals(budget)

    new_budget = models.Budget(
        trip_id=trip_id,
        transport=budget.transport,
        accommodation=budget.accommodation,
        food=budget.food,
        activities=budget.activities,
        reserve=reserve,
        total=total
    )

    db.add(new_budget)

    save_changes(db, new_budget)

    return new_budget


# Получение мест поездки
@router.get("/{trip_id}/places")
def get_trip_places(
    trip_id: Annotated[int, Path(gt=0)],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()

    if trip is None:
        raise HTTPException(
            status_code=404,
            detail="Поездка не найдена"
        )

    places = db.query(models.Place).join(
        models.TripPlace,
        models.Place.id == models.TripPlace.place_id
    ).filter(
        models.TripPlace.trip_id == trip_id
    ).all()

    return places


# Получение бюджета
@router.get("/{trip_id}")
def get_budget(
    trip_id: Annotated[int, Path(gt=0)],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()

    if trip is None:
        raise HTTPException(
            status_code=404,
            detail="Поездка не найдена"
        )

    budget = db.query(models.Budget).filter(
        models.Budget.trip_id == trip_id
    ).first()

    if budget is None:
        raise HTTPException(
            status_code=404,
            detail="Бюджет для этой поездки не найден"
        )

    return budget


# Изменение бюджета
@router.put("/{trip_id}")
def update_budget(
    trip_id: Annotated[int, Path(gt=0)],
    budget_data: schemas.BudgetCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()

    if trip is None:
        raise HTTPException(
            status_code=404,
            detail="Поездка не найдена"
        )

    budget = db.query(models.Budget).filter(
        models.Budget.trip_id == trip_id
    ).first()

    if budget is None:
        raise HTTPException(
            status_code=404,
            detail="Бюджет для этой поездки не найден"
        )

    reserve, total = calculate_totals(budget_data)

    budget.transport = budget_data.transport
    budget.accommodation = budget_data.accommodation
    budget.food = budget_data.food
    budget.activities = budget_data.activities
    budget.reserve = reserve
    budget.total = total

    save_changes(db, budget)

    return budget


# Удаление бюджета
@router.delete("/{trip_id}")
def delete_budget(
    trip_id: Annotated[int, Path(gt=0)],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == trip_id,
        models.Trip.user_id == current_user.id
    ).first()

    if trip is None:
        raise HTTPException(
            status_code=404,
            detail="Поездка не найдена"
        )

    budget = db.query(models.Budget).filter(
        models.Budget.trip_id == trip_id
    ).first()

    if budget is None:
        raise HTTPException(
            status_code=404,
            detail="Бюджет для этой поездки не найден"
        )

    db.delete(budget)

    save_changes(db)

    return {
        "message": "Бюджет успешно удалён"
    }