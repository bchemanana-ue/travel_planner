from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..database import get_db
from .. import models, schemas
from .auth import get_current_user


router = APIRouter(
    prefix="/trips",
    tags=["Trips"]
)


# Универсальная обработка ошибок сохранения
def commit_changes(db: Session):
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Не удалось сохранить изменения"
        )


# Получение всех поездок пользователя
@router.get("/")
def get_trips(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    trips = db.query(models.Trip).filter(
        models.Trip.user_id == current_user.id
    ).all()

    return trips


# Получение одной поездки
@router.get("/{trip_id}")
def get_trip(
    trip_id: int,
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

    return trip


# Создание поездки
@router.post("/")
def create_trip(
    trip: schemas.TripCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    new_trip = models.Trip(
        title=trip.title,
        destination=trip.destination,
        days=trip.days,
        user_id=current_user.id
    )

    db.add(new_trip)
    commit_changes(db)
    db.refresh(new_trip)

    return new_trip


# Удаление поездки
@router.delete("/{trip_id}")
def delete_trip(
    trip_id: int,
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

    try:
        # Отвязываем сообщения от удаляемой поездки
        db.query(models.ChatMessage).filter(
            models.ChatMessage.trip_id == trip_id
        ).update(
            {models.ChatMessage.trip_id: None},
            synchronize_session=False
        )

        # Удаляем связанные записи
        db.query(models.TripPlace).filter(
            models.TripPlace.trip_id == trip_id
        ).delete(synchronize_session=False)

        db.query(models.Budget).filter(
            models.Budget.trip_id == trip_id
        ).delete(synchronize_session=False)

        db.delete(trip)
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Не удалось удалить поездку"
        )

    return {
        "message": "Поездка успешно удалена"
    }


# Изменение поездки
@router.put("/{trip_id}")
def update_trip(
    trip_id: int,
    updated_trip: schemas.TripCreate,
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

    trip.title = updated_trip.title
    trip.destination = updated_trip.destination
    trip.days = updated_trip.days

    commit_changes(db)
    db.refresh(trip)

    return trip


# Добавление места в поездку
@router.post("/add-place")
def add_place_to_trip(
    data: schemas.TripPlaceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    trip = db.query(models.Trip).filter(
        models.Trip.id == data.trip_id,
        models.Trip.user_id == current_user.id
    ).first()

    if trip is None:
        raise HTTPException(
            status_code=404,
            detail="Поездка не найдена"
        )

    place = db.query(models.Place).filter(
        models.Place.id == data.place_id
    ).first()

    if place is None:
        raise HTTPException(
            status_code=404,
            detail="Место не найдено"
        )

    existing = db.query(models.TripPlace).filter(
        models.TripPlace.trip_id == data.trip_id,
        models.TripPlace.place_id == data.place_id
    ).first()

    if existing is not None:
        raise HTTPException(
            status_code=400,
            detail="Это место уже добавлено в поездку"
        )

    connection = models.TripPlace(
        trip_id=data.trip_id,
        place_id=data.place_id
    )

    db.add(connection)
    commit_changes(db)

    return {
        "message": "Место успешно добавлено в поездку",
        "trip_id": data.trip_id,
        "place_id": data.place_id
    }


# Получение мест конкретной поездки
@router.get("/{trip_id}/places")
def get_trip_places(
    trip_id: int,
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