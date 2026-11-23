import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app import models
from app.routers.auth import get_current_user


# Отдельная временная база данных SQLite
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Создание и удаление тестовой базы
@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# Тестовый пользователь
@pytest.fixture
def test_user(db_session):
    user = models.User(
        max_user_id="pytest_user",
        display_name="Тестовый пользователь",
        role="user"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


# Тестовый администратор
@pytest.fixture
def admin_user(db_session):
    user = models.User(
        max_user_id="pytest_admin",
        display_name="Тестовый администратор",
        role="admin"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


# Вспомогательная функция для создания клиента
@pytest.fixture
def client_factory(db_session):
    original_overrides = app.dependency_overrides.copy()

    def override_get_db():
        yield db_session

    def create_client(user=None):
        app.dependency_overrides[get_db] = override_get_db

        if user is not None:
            def override_get_current_user():
                return user

            app.dependency_overrides[get_current_user] = (
                override_get_current_user
            )

        return TestClient(app)

    yield create_client

    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


# Клиент обычного пользователя
@pytest.fixture
def client(client_factory, test_user):
    with client_factory(test_user) as test_client:
        yield test_client


# Клиент администратора
@pytest.fixture
def admin_client(client_factory, admin_user):
    with client_factory(admin_user) as test_client:
        yield test_client


# Клиент без авторизации
@pytest.fixture
def unauthenticated_client(client_factory):
    with client_factory() as test_client:
        yield test_client