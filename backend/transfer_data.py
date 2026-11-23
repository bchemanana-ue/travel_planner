import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, select, insert, text


# Загружаем настройки
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Не задан DATABASE_URL в файле .env")


# Подключаем старую SQLite и новую PostgreSQL
sqlite_path = Path(__file__).parent / "travel_planner.db"

sqlite_engine = create_engine(
    f"sqlite:///{sqlite_path}"
)

postgres_engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# Таблицы, данные которых нужно перенести
TABLES = [
    "users",
    "places",
    "trips",
    "budgets",
    "chat_messages",
    "trip_places"
]


# Получаем структуру обеих баз
sqlite_metadata = MetaData()
sqlite_metadata.reflect(bind=sqlite_engine)

postgres_metadata = MetaData()
postgres_metadata.reflect(bind=postgres_engine)


# Проверяем наличие всех таблиц
for table_name in TABLES:
    if table_name not in sqlite_metadata.tables:
        raise ValueError(f"Таблица {table_name} отсутствует в SQLite")

    if table_name not in postgres_metadata.tables:
        raise ValueError(f"Таблица {table_name} отсутствует в PostgreSQL")


# Переносим данные
with sqlite_engine.connect() as sqlite_connection:

    with postgres_engine.begin() as postgres_connection:

        # Проверяем, что целевые таблицы пустые
        for table_name in TABLES:
            table = postgres_metadata.tables[table_name]

            count = postgres_connection.execute(
                select(table).limit(1)
            ).first()

            if count is not None:
                raise ValueError(
                    f"Таблица {table_name} не пустая. Перенос остановлен."
                )

        # Сортируем таблицы с учётом внешних ключей
        ordered_tables = [
            table
            for table in postgres_metadata.sorted_tables
            if table.name in TABLES
        ]

        # Переносим записи
        for postgres_table in ordered_tables:

            sqlite_table = sqlite_metadata.tables[postgres_table.name]

            sqlite_columns = set(sqlite_table.columns.keys())
            postgres_columns = set(postgres_table.columns.keys())

            if not sqlite_columns.issubset(postgres_columns):
                raise ValueError(
                    f"Структура таблицы {postgres_table.name} "
                    "в SQLite и PostgreSQL различается."
                )

            rows = sqlite_connection.execute(
                select(sqlite_table)
            ).mappings().all()

            if rows:
                data = [
                    {
                        column: row[column]
                        for column in sqlite_columns
                    }
                    for row in rows
                ]

                postgres_connection.execute(
                    insert(postgres_table),
                    data
                )

            print(
                f"{postgres_table.name}: перенесено {len(rows)} записей"
            )

        # Обновляем последовательности ID в PostgreSQL
        preparer = postgres_engine.dialect.identifier_preparer

        for table_name in TABLES:
            table = postgres_metadata.tables[table_name]

            if "id" in table.columns:
                quoted_table = preparer.quote(table_name)

                postgres_connection.execute(
                    text(
                        f"""
                        SELECT setval(
                            pg_get_serial_sequence(:table_name, 'id'),
                            COALESCE(MAX(id), 1),
                            MAX(id) IS NOT NULL
                        )
                        FROM {quoted_table}
                        """
                    ),
                    {"table_name": table_name}
                )


print("\nПеренос данных успешно завершён!")

sqlite_engine.dispose()
postgres_engine.dispose()
