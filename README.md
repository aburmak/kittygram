## Kittygram (backend)

Это REST API: есть **котики** (`cats`) и **подборки** (`kitty_collections`) — можно сделать публичными или приватными, повесить теги, кидать в избранное чужие открытые подборки. Авторизация по токену, документация через Swagger/ReDoc, есть Docker.

Исходник курса был на Django 3.2. Здесь стоит **Django 5.0** и DRF 3.15, чтобы нормально жило на **Python 3.11+** (вплоть до 3.13).

## Что нужно установить

- Python **3.11+** (удобнее всего 3.12) **или** Docker.
- База — SQLite, файл `db.sqlite3` появится после миграций.

## Как запустить у себя

```bash
python3 -m venv env
source env/bin/activate   # Windows: env\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Админка: http://127.0.0.1:8000/admin/
- API: http://127.0.0.1:8000/api/v1/
- Swagger: http://127.0.0.1:8000/api/docs/swagger/
- ReDoc: http://127.0.0.1:8000/api/docs/redoc/
- Схема OpenAPI: http://127.0.0.1:8000/api/schema/

Старый адрес `/cats/` редиректит на `/api/v1/cats/`.

## Токен (например для Postman)

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"ВАШ_ЛОГИН","password":"ВАШ_ПАРОЛЬ"}'
```

В заголовке запросов:

`Authorization: Token <ключ из ответа>`

В Swagger в Authorize → tokenAuth нужно вписать **целиком**:

`Token <ключ из ответа>`

Пример: `Token fwrfjqkcndks`

## Docker

```bash
docker compose up --build
```

Слушает порт **8000**. Переменные по умолчанию в `docker-compose.yml`; свой секрет и т.д. — через `.env` по образцу `.env.example`.

## Эндпоинты вкратце

| Метод | URL | Кто может |
|-------|-----|-----------|
| GET | `/api/v1/cats/` | все |
| POST | `/api/v1/cats/` | все |
| GET | `/api/v1/collections/` | все (гости видят только публичные, не staff) |
| POST | `/api/v1/collections/` | залогиненный |
| GET | `/api/v1/collections/my/` | залогиненный |
| GET | `/api/v1/collections/favorites/` | залогиненный |
| POST | `/api/v1/collections/{id}/add_cat/` | владелец или staff |
| DELETE | `/api/v1/collections/{id}/remove_cat/` | владелец или staff |
| POST/DELETE | `/api/v1/collections/{id}/favorite/` | залогиненный |
| GET | `/api/v1/tags/` | все |

У списка подборок есть фильтры: `visibility`, `owner`, `tag` (slug), плюс `search`, `ordering`; пагинация `?page=1`, по 10 записей на страницу.

## Тесты

```bash
python manage.py test
```

## Лицензия

Смотри [LICENSE](LICENSE).
