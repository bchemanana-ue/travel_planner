from app import models
# ==============================
# 1. Проверка работы приложения
# ==============================

def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Travel Planner работает!"


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ==============================
# 2. Проверка авторизации
# ==============================

def test_trips_without_auth(unauthenticated_client):
    response = unauthenticated_client.get("/trips/")

    assert response.status_code == 401


def test_chat_without_auth(unauthenticated_client):
    response = unauthenticated_client.get("/chat/messages")

    assert response.status_code == 401


# ==============================
# 3. Проверка поездок
# ==============================

def test_create_trip(client):
    response = client.post(
        "/trips/",
        json={
            "title": "Выходные в Казани",
            "destination": "Казань",
            "days": 3
        }
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Выходные в Казани"
    assert response.json()["destination"] == "Казань"


def test_create_trip_invalid_days(client):
    response = client.post(
        "/trips/",
        json={
            "title": "Длинная поездка",
            "destination": "Казань",
            "days": 5
        }
    )

    assert response.status_code == 422


def test_get_trips(client):
    client.post(
        "/trips/",
        json={
            "title": "Поездка в Москву",
            "destination": "Москва",
            "days": 2
        }
    )

    response = client.get("/trips/")

    assert response.status_code == 200
    assert len(response.json()) == 1


# ==============================
# 4. Проверка каталога мест
# ==============================

def test_get_places(client):
    response = client.get("/places/")

    assert response.status_code == 200


def test_create_place_without_admin(client):
    response = client.post(
        "/places/",
        json={
            "name": "Казанский кремль",
            "description": "Исторический комплекс",
            "category": "Достопримечательность",
            "region": "Татарстан",
            "average_price": 600
        }
    )

    assert response.status_code == 403


def test_create_place_as_admin(admin_client):
    response = admin_client.post(
        "/places/",
        json={
            "name": "Казанский кремль",
            "description": "Исторический комплекс",
            "category": "Достопримечательность",
            "region": "Татарстан",
            "average_price": 600
        }
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Казанский кремль"


def test_create_place_negative_price(admin_client):
    response = admin_client.post(
        "/places/",
        json={
            "name": "Тестовое место",
            "description": "Описание",
            "category": "Музей",
            "region": "Татарстан",
            "average_price": -100
        }
    )

    assert response.status_code == 422


# ==============================
# 5. Проверка бюджета
# ==============================

def test_create_budget(client):
    trip_response = client.post(
        "/trips/",
        json={
            "title": "Поездка в Казань",
            "destination": "Казань",
            "days": 3
        }
    )

    trip_id = trip_response.json()["id"]

    response = client.post(
        f"/budgets/{trip_id}",
        json={
            "transport": 3000,
            "accommodation": 5000,
            "food": 2000,
            "activities": 1000
        }
    )

    assert response.status_code == 200
    assert response.json()["reserve"] == 1100
    assert response.json()["total"] == 12100


def test_get_budget(client):
    trip_response = client.post(
        "/trips/",
        json={
            "title": "Поездка в Москву",
            "destination": "Москва",
            "days": 2
        }
    )

    trip_id = trip_response.json()["id"]

    client.post(
        f"/budgets/{trip_id}",
        json={
            "transport": 1000,
            "accommodation": 2000,
            "food": 1000,
            "activities": 500
        }
    )

    response = client.get(f"/budgets/{trip_id}")

    assert response.status_code == 200
    assert response.json()["total"] == 4950


def test_create_budget_negative_value(client):
    trip_response = client.post(
        "/trips/",
        json={
            "title": "Поездка",
            "destination": "Казань",
            "days": 2
        }
    )

    trip_id = trip_response.json()["id"]

    response = client.post(
        f"/budgets/{trip_id}",
        json={
            "transport": -100,
            "accommodation": 1000,
            "food": 500,
            "activities": 200
        }
    )

    assert response.status_code == 422


# ==============================
# 6. Проверка чата
# ==============================

def test_create_chat_message(client):
    response = client.post(
        "/chat/messages",
        json={
            "content": "Хочу спланировать поездку в Казань"
        }
    )

    assert response.status_code == 200
    assert response.json()["role"] == "user"


def test_get_chat_messages(client):
    client.post(
        "/chat/messages",
        json={
            "content": "Привет!"
        }
    )

    response = client.get("/chat/messages")

    assert response.status_code == 200
    assert len(response.json()) == 1


# ==============================
# 7. Проверка интеграции с AI
# ==============================

def test_create_ai_plan(client, db_session):
    # Создаём тестовое место непосредственно в тестовой базе
    place = models.Place(
        name="Казанский кремль",
        description="Исторический комплекс",
        category="Достопримечательность",
        region="Татарстан",
        average_price=600
    )

    db_session.add(place)
    db_session.commit()
    db_session.refresh(place)

    # Создаём план путешествия
    response = client.post(
        "/ai/plans",
        json={
            "title": "Выходные в Казани",
            "destination": "Казань",
            "days": 3,
            "place_ids": [place.id],
            "budget": {
                "transport": 3000,
                "accommodation": 5000,
                "food": 2000,
                "activities": 1000
            }
        }
    )

    assert response.status_code == 200
    assert response.json()["destination"] == "Казань"
    assert response.json()["budget_created"] is True


def test_ai_plan_invalid_days(client):
    response = client.post(
        "/ai/plans",
        json={
            "title": "Длинное путешествие",
            "destination": "Казань",
            "days": 5,
            "place_ids": []
        }
    )

    assert response.status_code == 422


def test_ai_plan_missing_place(client):
    response = client.post(
        "/ai/plans",
        json={
            "title": "Поездка",
            "destination": "Казань",
            "days": 2,
            "place_ids": [999]
        }
    )

    assert response.status_code == 404


def test_ai_plan_duplicate_places(client):
    response = client.post(
        "/ai/plans",
        json={
            "title": "Поездка",
            "destination": "Казань",
            "days": 2,
            "place_ids": [1, 1]
        }
    )

    assert response.status_code == 400

# ==============================
# 8. Проверка удаления поездки
# ==============================

def test_delete_trip_with_related_data(client, db_session):
    # 1. Создаём поездку
    trip_response = client.post(
        "/trips/",
        json={
            "title": "Поездка для удаления",
            "destination": "Казань",
            "days": 2
        }
    )

    trip_id = trip_response.json()["id"]

    # 2. Создаём место
    place = models.Place(
        name="Казанский кремль",
        category="Достопримечательность",
        region="Татарстан"
    )

    db_session.add(place)
    db_session.commit()
    db_session.refresh(place)

    # 3. Добавляем место в поездку
    place_response = client.post(
        "/trips/add-place",
        json={
            "trip_id": trip_id,
            "place_id": place.id
        }
    )

    assert place_response.status_code == 200

    # 4. Создаём бюджет
    budget_response = client.post(
        f"/budgets/{trip_id}",
        json={
            "transport": 1000,
            "accommodation": 2000,
            "food": 1000,
            "activities": 500
        }
    )

    assert budget_response.status_code == 200

    # 5. Создаём сообщение чата, связанное с поездкой
    chat_response = client.post(
        "/chat/messages",
        json={
            "trip_id": trip_id,
            "content": "Планирую поездку в Казань"
        }
    )

    assert chat_response.status_code == 200

    # 6. Удаляем поездку
    delete_response = client.delete(
        f"/trips/{trip_id}"
    )

    assert delete_response.status_code == 200

    # 7. Проверяем, что поездка удалена
    assert db_session.query(models.Trip).filter(
        models.Trip.id == trip_id
    ).first() is None

    # 8. Проверяем удаление связей с местами
    assert db_session.query(models.TripPlace).filter(
        models.TripPlace.trip_id == trip_id
    ).count() == 0

    # 9. Проверяем удаление бюджета
    assert db_session.query(models.Budget).filter(
        models.Budget.trip_id == trip_id
    ).first() is None

    # 10. Проверяем, что сообщение сохранилось,
    # но связь с поездкой была удалена
    db_session.expire_all()

    message = db_session.query(models.ChatMessage).filter(
        models.ChatMessage.content == "Планирую поездку в Казань"
    ).first()

    assert message is not None
    assert message.trip_id is None
