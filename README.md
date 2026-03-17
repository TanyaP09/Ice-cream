

## Быстрый старт (Docker)

```bash
docker compose up --build
```

API будет доступен на `http://localhost:3000`.
Фронт: `/login`, `/register`, `/app`.
Документация FastAPI: `http://localhost:3000/docs`.

## Ручной запуск (без Docker)

1. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Поднять Postgres (например через Docker) и применить `db/init.sql`.
3. Создать `.env` (см. `.env.example`).
4. Запустить:
   ```bash
   uvicorn src.main:app --reload --port 3000
   ```

## Основные эндпоинты

### Auth

`POST /auth/register`
```json
{
  "name": "Anna",
  "email": "anna@mail.com",
  "password": "secret",
  "weight": 60,
  "height": 170,
  "age": 22,
  "sex": "f",
  "region": "Moscow"
}
```

`POST /auth/login`
```json
{ "email": "anna@mail.com", "password": "secret" }
```

Ответ:
```json
{ "token": "JWT_TOKEN" }
```

### Access (требуется токен)

`GET /users/me`
Header: `Authorization: Bearer JWT_TOKEN`

### Ice creams (CRUD)

`GET /ice-creams` (публичный)

`POST /ice-creams`
```json
{
  "name": "Vanilla",
  "calories": 200,
  "carbohydrates": 24,
  "proteins": 4,
  "fats": 10,
  "sugar": 18,
  "rysk": 2
}
```

`PUT /ice-creams/:id` и `DELETE /ice-creams/:id` — тоже есть.

### Entries (что пользователь ел)

`POST /entries`
```json
{
  "ice_cream_id": 1,
  "eaten_date": "2026-03-17",
  "amount_grams": 150
}
```

`GET /entries` — возвращает список с уже посчитанными калориями и БЖУ.

`GET /entries/summary?date=2026-03-17` — суммарные значения за день.

`PUT /entries/:id` и `DELETE /entries/:id` — редактирование и удаление.

## Что внутри

- `src/main.py` — основной сервер и маршруты (FastAPI).
- `static/login.html` — страница входа.
- `static/register.html` — страница регистрации.
- `static/app.html` — главная страница.
- `static/styles.css` — стили.
- `static/app.js` — логика запросов к API.
- `db/init.sql` — схема базы и сиды для мороженного.
- `docker-compose.yml` — два контейнера: API и Postgres.
- `Dockerfile` — сборка бэка.

## Почему так

- JWT даёт "access" — токен нужен для приватных эндпоинтов.
- Все CRUD-операции есть: add/update/remove/access.
- БД хранит пользователей, мороженное и связь "кто что съел и когда".

