from sqlalchemy import inspect, text

from app.database import engine


inspector = inspect(engine)

columns = [
    column["name"]
    for column in inspector.get_columns("users")
]

if "role" not in columns:
    with engine.begin() as connection:
        connection.execute(
            text("""
                ALTER TABLE users
                ADD COLUMN role VARCHAR NOT NULL DEFAULT 'user'
            """)
        )

    print("Колонка role успешно добавлена!")

else:
    print("Колонка role уже существует!")


with engine.connect() as connection:
    users = connection.execute(
        text("SELECT id, max_user_id, role FROM users")
    ).fetchall()

    for user in users:
        print(user)