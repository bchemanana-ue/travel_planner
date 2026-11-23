import json
import hmac
import hashlib

from urllib.parse import urlencode
from datetime import datetime, timezone

from app.main import app
from app.database import get_db
from app import models
from app.routers.auth import get_current_user
from app.max_auth import validate_max_init_data

from fastapi.testclient import TestClient


# Создаём тестовые данные MAX с правильной подписью
def create_max_init_data(user_id, bot_token):
    params = {
        "auth_date": str(
            int(datetime.now(timezone.utc).timestamp())
        ),
        "user": json.dumps({
            "id": user_id,
            "first_name": "Test",
            "last_name": "User"
        })
    }

    launch_params = "\n".join(
        f"{key}={value}"
        for key, value in sorted(params.items())
    )

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()

    signature = hmac.new(
        key=secret_key,
        msg=launch_params.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()

    params["hash"] = signature

    return urlencode(params)


# Проверяем правильность подписи MAX
def test_validate_max_init_data(monkeypatch):
    bot_token = "test_bot_token"

    monkeypatch.setenv("MAX_BOT_TOKEN", bot_token)

    init_data = create_max_init_data(
        user_id=12345,
        bot_token=bot_token
    )

    user = validate_max_init_data(init_data)

    assert user["id"] == 12345
    assert user["first_name"] == "Test"


# Проверяем отклонение неправильной подписи
def test_validate_invalid_signature(monkeypatch):
    bot_token = "test_bot_token"

    monkeypatch.setenv("MAX_BOT_TOKEN", bot_token)

    init_data = create_max_init_data(
        user_id=12345,
        bot_token=bot_token
    )

    init_data = init_data.replace(
        "Test",
        "Wrong"
    )

    try:
        validate_max_init_data(init_data)
        assert False, "Ожидалась ошибка авторизации"

    except ValueError:
        pass


# Проверяем отсутствие токена
def test_validate_without_bot_token(monkeypatch):
    monkeypatch.delenv("MAX_BOT_TOKEN", raising=False)

    try:
        validate_max_init_data("some_data")
        assert False, "Ожидалась ошибка отсутствующего токена"

    except ValueError as error:
        assert "токен" in str(error).lower()

# Проверяем регистрацию нового пользователя через MAX
def test_max_auth_creates_user(
    unauthenticated_client,
    db_session,
    monkeypatch
):
    bot_token = "test_bot_token"
    monkeypatch.setenv("MAX_BOT_TOKEN", bot_token)

    init_data = create_max_init_data(
        user_id=12345,
        bot_token=bot_token
    )

    response = unauthenticated_client.post(
        "/auth/max",
        headers={"X-Max-Init-Data": init_data}
    )

    assert response.status_code == 200
    assert response.json()["max_user_id"] == "12345"

    # Проверяем, что пользователь действительно появился в БД
    user = db_session.query(models.User).filter(
        models.User.max_user_id == "12345"
    ).first()

    assert user is not None
    assert user.role == "user"


# Проверяем повторную авторизацию без создания дубликата
def test_max_auth_existing_user(
    unauthenticated_client,
    db_session,
    monkeypatch
):
    bot_token = "test_bot_token"
    monkeypatch.setenv("MAX_BOT_TOKEN", bot_token)

    init_data = create_max_init_data(
        user_id=12345,
        bot_token=bot_token
    )

    first_response = unauthenticated_client.post(
        "/auth/max",
        headers={"X-Max-Init-Data": init_data}
    )

    second_response = unauthenticated_client.post(
        "/auth/max",
        headers={"X-Max-Init-Data": init_data}
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert (
        first_response.json()["user_id"]
        == second_response.json()["user_id"]
    )

    users_count = db_session.query(models.User).filter(
        models.User.max_user_id == "12345"
    ).count()

    assert users_count == 1


# Проверяем доступ зарегистрированного пользователя
def test_max_auth_allows_registered_user(
    unauthenticated_client,
    monkeypatch
):
    bot_token = "test_bot_token"
    monkeypatch.setenv("MAX_BOT_TOKEN", bot_token)

    init_data = create_max_init_data(
        user_id=12345,
        bot_token=bot_token
    )

    # Сначала регистрируем пользователя
    auth_response = unauthenticated_client.post(
        "/auth/max",
        headers={"X-Max-Init-Data": init_data}
    )

    assert auth_response.status_code == 200

    # Затем обращаемся к защищённому маршруту
    response = unauthenticated_client.get(
        "/trips/",
        headers={"X-Max-Init-Data": init_data}
    )

    assert response.status_code == 200

# Проверяем запрос без данных авторизации
def test_max_auth_without_header(unauthenticated_client):
    response = unauthenticated_client.post("/auth/max")

    assert response.status_code == 401


# Проверяем отклонение устаревших данных MAX
def test_max_auth_expired_data(monkeypatch):
    bot_token = "test_bot_token"
    monkeypatch.setenv("MAX_BOT_TOKEN", bot_token)

    params = {
        "auth_date": str(
            int(datetime.now(timezone.utc).timestamp()) - 7200
        ),
        "user": json.dumps({
            "id": 12345,
            "first_name": "Test"
        })
    }

    launch_params = "\n".join(
        f"{key}={value}"
        for key, value in sorted(params.items())
    )

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()

    signature = hmac.new(
        key=secret_key,
        msg=launch_params.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()

    params["hash"] = signature

    init_data = urlencode(params)

    try:
        validate_max_init_data(init_data)
        assert False, "Ожидалась ошибка устаревших данных"
    except ValueError as error:
        assert "устарели" in str(error)

# Проверяем, что новый пользователь не становится администратором
def test_new_user_cannot_become_admin(
    unauthenticated_client,
    db_session,
    monkeypatch
):
    bot_token = "test_bot_token"
    monkeypatch.setenv("MAX_BOT_TOKEN", bot_token)

    init_data = create_max_init_data(
        user_id=54321,
        bot_token=bot_token
    )

    response = unauthenticated_client.post(
        "/auth/max",
        headers={"X-Max-Init-Data": init_data}
    )

    assert response.status_code == 200

    user = db_session.query(models.User).filter(
        models.User.max_user_id == "54321"
    ).first()

    assert user is not None
    assert user.role == "user"


# Проверяем, что обычный пользователь не имеет доступа к админским функциям
def test_regular_user_cannot_access_admin_places(
    client
):
    response = client.post(
        "/places/",
        json={
            "name": "Тестовое место",
            "description": "Описание",
            "category": "Достопримечательность",
            "region": "Татарстан",
            "average_price": 1000
        }
    )

    assert response.status_code == 403


# Проверяем, что без авторизации нельзя получить поездки
def test_unauthenticated_user_cannot_access_trips(
    unauthenticated_client
):
    response = unauthenticated_client.get("/trips/")

    assert response.status_code == 401


# Проверяем, что неправильный ID пользователя отклоняется
def test_validate_invalid_user_id(monkeypatch):
    bot_token = "test_bot_token"
    monkeypatch.setenv("MAX_BOT_TOKEN", bot_token)

    init_data = create_max_init_data(
        user_id=-123,
        bot_token=bot_token
    )

    try:
        validate_max_init_data(init_data)
        assert False, "Ожидалась ошибка некорректного ID"

    except ValueError:
        pass