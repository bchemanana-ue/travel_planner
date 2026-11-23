from app.database import SessionLocal
from app.models import User

db = SessionLocal()

user = db.query(User).filter(User.id == 1).first()

if user is None:
    test_user = User(
        max_user_id="test_user_001",
        display_name="Тестовый пользователь"
    )

    db.add(test_user)
    db.commit()

    print("Тестовый пользователь создан!")
else:
    print("Тестовый пользователь уже существует!")

db.close()