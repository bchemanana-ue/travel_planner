from app.database import SessionLocal
from app.models import User

db = SessionLocal()

try:
    user = db.query(User).filter(
        User.max_user_id == "test_user_001"
    ).first()

    if user is None:
        print("Пользователь не найден!")

    else:
        user.role = "admin"
        db.commit()

        print("Пользователь успешно стал администратором!")
        print("ID:", user.id)
        print("Роль:", user.role)

finally:
    db.close()