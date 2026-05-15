# Лабораторная работа №12. AI-ассистированная разработка
**Студент:** *Платов Артем Русланович*\
**Группа:** *220032-11*\
**Вариант:** *16*\
**Сложность:** *Средняя*
---
# Система управления ЖКХ

REST API для учёта и обработки лицевых счетов в системе жилищно-коммунального хозяйства (ЖКХ). Позволяет создавать, просматривать, обновлять и удалять лицевые счета, а также запускать ежемесячные начисления пеней, скидок и комиссий.

Стек: **FastAPI + SQLAlchemy + Pydantic + Alembic + PostgreSQL/SQLite + Docker**

---

## Установка и запуск

### Локально (без Docker)

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.\.venv\Scripts\activate       # Windows

pip install -r requirements.txt

alembic upgrade head

uvicorn app.main:app --reload
```

Приложение будет доступно на `http://localhost:8000`.  
Swagger UI: `http://localhost:8000/docs`.

### Через Docker

```bash
docker compose up --build
```

PostgreSQL и приложение поднимутся вместе.  
Приложение доступно на `http://localhost:8000`.

### Запуск тестов

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./housing.db` | URL подключения к базе данных (SQLite или PostgreSQL) |
| `POSTGRES_USER` | `housing` | Пользователь PostgreSQL (только в docker-compose) |
| `POSTGRES_PASSWORD` | `housing_pass` | Пароль PostgreSQL (только в docker-compose) |
| `POSTGRES_DB` | `housing_db` | Имя базы PostgreSQL (только в docker-compose) |

---

## API-эндпоинты

### GET `/bills/` — список всех лицевых счетов

**Request:**
```
GET /bills/
```

**Response 200:**
```json
[
  {
    "id": 1,
    "account_number": "EL-12345",
    "address": "ул. Ленина, д.1, кв.1",
    "owner_name": "Иванов И.И.",
    "readings": 1500,
    "accruals": 3500,
    "payments": 3000,
    "requests": "",
    "debt": 500
  }
]
```

---

### POST `/bills/` — создать новый лицевой счёт

**Request:**
```json
{
  "account_number": "EL-12345",
  "address": "ул. Ленина, д.1, кв.1",
  "owner_name": "Иванов И.И.",
  "readings": 1500,
  "accruals": 3500,
  "payments": 3000,
  "requests": ""
}
```

**Response 201:**
```json
{
  "id": 1,
  "account_number": "EL-12345",
  "address": "ул. Ленина, д.1, кв.1",
  "owner_name": "Иванов И.И.",
  "readings": 1500,
  "accruals": 3500,
  "payments": 3000,
  "requests": "",
  "debt": 500
}
```

**Response 409** — дубликат номера счёта:
```json
{
  "detail": "Лицевой счёт с таким номером уже существует"
}
```

**Response 422** — невалидные данные (пустые поля, отрицательные числа):
```json
{
  "detail": [
    {"type": "string_too_short", "loc": ["body", "account_number"], "msg": "String should have at least 1 character"},
    {"type": "greater_than_equal", "loc": ["body", "readings"], "msg": "Input should be greater than or equal to 0", "ctx": {"ge": 0}}
  ]
}
```

---

### GET `/bills/{id}` — получить счёт по ID

**Request:**
```
GET /bills/1
```

**Response 200:**
```json
{
  "id": 1,
  "account_number": "EL-12345",
  "address": "ул. Ленина, д.1, кв.1",
  "owner_name": "Иванов И.И.",
  "readings": 1500,
  "accruals": 3500,
  "payments": 3000,
  "requests": "",
  "debt": 500
}
```

**Response 404:**
```json
{
  "detail": "Лицевой счёт не найден"
}
```

---

### PUT `/bills/{id}` — частичное обновление счёта

**Request:**
```json
{
  "readings": 1600,
  "payments": 3500
}
```

**Response 200:**
```json
{
  "id": 1,
  "account_number": "EL-12345",
  "address": "ул. Ленина, д.1, кв.1",
  "owner_name": "Иванов И.И.",
  "readings": 1600,
  "accruals": 3500,
  "payments": 3500,
  "requests": "",
  "debt": 0
}
```

**Response 404:**
```json
{
  "detail": "Лицевой счёт не найден"
}
```

---

### DELETE `/bills/{id}` — удалить счёт

**Request:**
```
DELETE /bills/1
```

**Response 204** — нет тела ответа.

**Response 404:**
```json
{
  "detail": "Лицевой счёт не найден"
}
```

---

## Модель данных

| Поле | Тип | Описание |
|---|---|---|
| `id` | int (PK) | Уникальный идентификатор |
| `account_number` | str, unique | Номер лицевого счёта (напр. `EL-12345`) |
| `address` | str | Адрес помещения |
| `owner_name` | str | ФИО владельца |
| `readings` | int (>= 0) | Показания счётчика |
| `accruals` | int (>= 0) | Начисления |
| `payments` | int (>= 0) | Оплаты |
| `requests` | str | Заявки (текст) |
| `debt` | int (computed) | Задолженность = accruals - payments |

---

## Структура проекта

```
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── app/
│   ├── __init__.py
│   ├── main.py          # Точка входа FastAPI
│   ├── database.py      # Подключение к БД
│   ├── models.py        # SQLAlchemy модель
│   ├── schemas.py       # Pydantic схемы
│   ├── crud.py          # Бизнес-логика
│   └── routers/
│       ├── __init__.py
│       └── bills.py     # Эндпоинты
└── tests/
    ├── __init__.py
    └── test_bills.py    # Тесты
```
