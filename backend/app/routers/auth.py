from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..database import get_db
from .. import models
from ..max_auth import validate_max_init_data


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# Получение текущего авторизованного пользователя
def get_current_user(
    db: Session = Depends(get_db),
    x_max_init_data: str | None = Header(default=None)
):
    if not x_max_init_data:
        raise HTTPException(
            status_code=401,
            detail="Необходима авторизация через MAX"
        )

    try:
        max_user = validate_max_init_data(x_max_init_data)

    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Недействительные данные авторизации MAX"
        )

    max_user_id = str(max_user["id"])

    user = db.query(models.User).filter(
        models.User.max_user_id == max_user_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Пользователь не авторизован"
        )

    return user


# Проверка прав администратора
def get_current_admin(
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Недостаточно прав. Требуется роль администратора."
        )

    return current_user


# Авторизация и регистрация через MAX
@router.post("/max")
def authenticate_max(
    db: Session = Depends(get_db),
    x_max_init_data: str | None = Header(default=None)
):
    if not x_max_init_data:
        raise HTTPException(
            status_code=401,
            detail="Данные авторизации MAX отсутствуют"
        )

    try:
        max_user = validate_max_init_data(x_max_init_data)

    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Не удалось проверить авторизацию MAX"
        )

    max_user_id = str(max_user["id"])

    user = db.query(models.User).filter(
        models.User.max_user_id == max_user_id
    ).first()

    if user is None:
        display_name = " ".join(
            filter(None, [
                max_user.get("first_name"),
                max_user.get("last_name")
            ])
        ) or None

        user = models.User(
            max_user_id=max_user_id,
            display_name=display_name
        )

        try:
            db.add(user)
            db.commit()
            db.refresh(user)

        except SQLAlchemyError:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail="Не удалось создать пользователя"
            )

    return {
        "message": "Авторизация прошла успешно",
        "user_id": user.id,
        "max_user_id": user.max_user_id,
        "display_name": user.display_name
    }