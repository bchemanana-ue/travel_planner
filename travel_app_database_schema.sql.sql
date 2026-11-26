# Генерация чистого SQL-скрипта на основе методички
# Структура БД для MVP приложения планирования путешествий

sql_script = """
-- База данных MVP приложения для планирования путешествий
-- Сгенерировано на основе методички (6-7 недель, 8-12 регионов, 100-300 мест)
-- Совместимо с PostgreSQL и SQLite

-- Таблица регионов (8-12 целевых регионов)
CREATE TABLE regions (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(200),
    examples TEXT
);

-- Справочник типов мест (из раздела 5 структуры запроса)
CREATE TABLE place_types (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL, -- forest, mountains, lake, sea, city, village, national_park
    ru VARCHAR(50) NOT NULL
);

-- Справочник активностей
CREATE TABLE activities (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL, -- hiking, fishing, swimming, sightseeing, glamping, rafting, museums
    ru VARCHAR(50) NOT NULL
);

-- Каталог мест (100-300 объектов для MVP)
CREATE TABLE places (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    region_id INTEGER NOT NULL,
    place_type_id INTEGER NOT NULL,
    description TEXT,
    lat DECIMAL(9, 6), -- Широта
    lon DECIMAL(9, 6), -- Долгота
    price_from INTEGER, -- Минимальная цена за сутки/ночь
    price_to INTEGER,   -- Максимальная цена
    rating DECIMAL(3, 1) DEFAULT 0.0, -- Оценка 0.0-5.0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(id),
    FOREIGN KEY (place_type_id) REFERENCES place_types(id)
);

-- Связь мест и активностей (многие-ко-многим)
CREATE TABLE place_activities (
    place_id INTEGER NOT NULL,
    activity_id INTEGER NOT NULL,
    PRIMARY KEY (place_id, activity_id),
    FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE,
    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
);

-- Таблица поездок пользователей
CREATE TABLE trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(100) NOT NULL, -- Telegram user_id или UUID
    departure_city VARCHAR(100),
    destination_place_id INTEGER,
    dates VARCHAR(100), -- JSON или строка с датами
    duration_days INTEGER,
    travelers_count INTEGER,
    budget_total INTEGER,
    transport_preference VARCHAR(50), -- train, car, bus
    comfort_level VARCHAR(50), -- budget, comfort, premium
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (destination_place_id) REFERENCES places(id)
);

-- Индексы для быстрого поиска (раздел 6 методички)
CREATE INDEX idx_places_region ON places(region_id);
CREATE INDEX idx_places_type ON places(place_type_id);
CREATE INDEX idx_places_rating ON places(rating DESC);
CREATE INDEX idx_places_price_from ON places(price_from);
CREATE INDEX idx_places_price_to ON places(price_to);
CREATE INDEX idx_trips_user ON trips(user_id);
CREATE INDEX idx_trips_dates ON trips(dates);

-- Заполнение справочника регионов (12 регионов из методички)
INSERT INTO regions (id, name, type, examples) VALUES
(1, 'Подмосковье', 'Лес, глэмпинг, дача', 'Парки, турбазы, глэмпинги'),
(2, 'Тверская область', 'Озёра, лес, Волга', 'Селигер, турбазы, гостевые дома'),
(3, 'Ярославская область', 'Волга, Золотое кольцо', 'Малые города, базы отдыха'),
(4, 'Владимирская область', 'История, природа', 'Суздаль, Муром, лесные базы'),
(5, 'Калужская область', 'Заповедники, деревни', 'Экотропы, усадьбы, глэмпинги'),
(6, 'Карелия', 'Озёра, скалы, лес', 'Ладога, маршруты, кемпинги'),
(7, 'Ленинградская область', 'Финский залив, лес', 'Кемпинги, парки, базы'),
(8, 'Псковская область', 'История, озёра', 'Пушкинские Горы, Изборск, озёра'),
(9, 'Рязанская область', 'Лес, реки, усадьбы', 'Мещёра, сплавы, турбазы'),
(10, 'Тульская область', 'Города, музеи, природа', 'Ясная Поляна, Куликово поле'),
(11, 'Костромская область', 'Лес, Волга, малые города', 'Кострома, Плёс, базы отдыха'),
(12, 'Кавказ / Домбай', 'Горы, походы', 'Горные маршруты, гостевые дома');

-- Заполнение типов мест
INSERT INTO place_types (id, name, ru) VALUES
(1, 'forest', 'Лес'),
(2, 'mountains', 'Горы'),
(3, 'lake', 'Озеро'),
(4, 'sea', 'Море'),
(5, 'city', 'Город'),
(6, 'village', 'Деревня'),
(7, 'national_park', 'Национальный парк');

-- Заполнение активностей
INSERT INTO activities (id, name, ru) VALUES
(1, 'hiking', 'Походы'),
(2, 'fishing', 'Рыбалка'),
(3, 'swimming', 'Купание'),
(4, 'sightseeing', 'Экскурсии'),
(5, 'glamping', 'Глэмпинг'),
(6, 'rafting', 'Сплавы'),
(7, 'museums', 'Музеи');

COMMIT;
"""

# Сохраняем SQL-скрипт в файл
with open('travel_app_database_schema.sql', 'w', encoding='utf-8') as f:
    f.write(sql_script)

print("Файл travel_app_database_schema.sql успешно создан")
print("Содержимое файла:")
print(sql_script)