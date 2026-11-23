from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..database import get_db
from .. import models, schemas
from .auth import get_current_admin


router = APIRouter(
    prefix="/places",
    tags=["Places"]
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


# Получение всех мест
@router.get("/")
def get_places(
    db: Session = Depends(get_db)
):
    places = db.query(models.Place).all()

    return places


# Создание места
@router.post("/")
def create_place(
    place: schemas.PlaceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    new_place = models.Place(
        name=place.name,
        description=place.description,
        category=place.category,
        region=place.region,
        latitude=place.latitude,
        longitude=place.longitude,
        average_price=place.average_price
    )

    db.add(new_place)

    save_changes(db, new_place)

    return new_place


# Получение одного места
@router.get("/{place_id}")
def get_place(
    place_id: int = Path(gt=0),
    db: Session = Depends(get_db)
):
    place = db.query(models.Place).filter(
        models.Place.id == place_id
    ).first()

    if place is None:
        raise HTTPException(
            status_code=404,
            detail="Место не найдено"
        )

    return place


# Удаление места
@router.delete("/{place_id}")
def delete_place(
    place_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    place = db.query(models.Place).filter(
        models.Place.id == place_id
    ).first()

    if place is None:
        raise HTTPException(
            status_code=404,
            detail="Место не найдено"
        )

    existing_connection = db.query(models.TripPlace).filter(
        models.TripPlace.place_id == place_id
    ).first()

    if existing_connection is not None:
        raise HTTPException(
            status_code=409,
            detail="Нельзя удалить место, которое добавлено в маршрут поездки"
        )

    db.delete(place)

    save_changes(db)

    return {
        "message": "Место успешно удалено"
    }


# Изменение места
@router.put("/{place_id}")
def update_place(
    place_id: int = Path(gt=0),
    place_data: schemas.PlaceCreate = ...,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    place = db.query(models.Place).filter(
        models.Place.id == place_id
    ).first()

    if place is None:
        raise HTTPException(
            status_code=404,
            detail="Место не найдено"
        )

    place.name = place_data.name
    place.description = place_data.description
    place.category = place_data.category
    place.region = place_data.region
    place.latitude = place_data.latitude
    place.longitude = place_data.longitude
    place.average_price = place_data.average_price

    save_changes(db, place)

    return place