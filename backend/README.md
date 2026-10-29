# DevLab Backend

FastAPI-приложение и миграции PostgreSQL. Запуск API не создаёт таблицы и не применяет миграции автоматически.

## Таблицы

SQLAlchemy-модели находятся в `app/schemas/`, отдельно от Pydantic-моделей HTTP в `app/models/`.

- `courses`: `id` (identity), уникальный `slug`, `title`, `description`, `status`, `position`, `created_at`, `updated_at`.
- `course_steps`: `id` (identity), `course_id`, `slug`, `position`, `title`, `content` (JSONB), `created_at`, `updated_at`.

Все поля обязательны. Позиции положительные, считаются с 1. Статусы курса: `planned`, `available`, `archived`. Названия шагов и наполнение не являются прогрессом пользователя.

Внешний ключ связывает шаг с курсом; удаление курса с шагами запрещено (`RESTRICT`). Внутри курса уникальны позиции и slug шагов. Уникальное ограничение `(course_id, position)` создаёт индекс, пригодный для выборки шагов курса в нужном порядке; отдельный дублирующий индекс не нужен. В запросах явно использовать `ORDER BY position`.

`content` — JSON-объект. Например:

```json
{"blocks": [{"type": "text", "text": "Открой терминал."}, {"type": "code", "language": "bash", "text": "devlab"}]}
```

База проверяет, что это объект. Состав блоков — будущий контракт API, отдельная валидация блоков пока не реализована. При обновлении через ORM присваивать новый объект `content`: вложенные изменения словаря на месте не отслеживаются автоматически.

Даты имеют часовой пояс. `created_at` и начальный `updated_at` задаёт PostgreSQL. Последующие изменения `updated_at` обслуживает SQLAlchemy; для прямых SQL UPDATE значение нужно задавать явно, триггера нет.

## Применение миграции вручную через Docker

Из корня проекта, с настроенным `.env`:

```sh
docker compose up -d postgres
docker compose build backend
```

Дождаться готовности PostgreSQL (`docker compose ps`). Просмотреть SQL без применения:

```sh
docker compose run --rm --no-deps backend alembic upgrade head --sql
```

Применить, когда готов:

```sh
docker compose run --rm --no-deps backend alembic upgrade head
docker compose run --rm --no-deps backend alembic current
```

Миграция `20261030_0001` создаёт только таблицы и ограничения, без курсов и шагов. Каталог API пока остаётся статическим. Наличие подготовленного файла миграции не означает, что он уже применён к твоей базе.

Параметры `POSTGRES_*` передаются backend из Compose. При использовании существующего volume они должны совпадать с учётными данными, с которыми база была создана; изменение `.env` не меняет пароль существующей базы. Секреты не хранятся в `alembic.ini`.

## Локальный Alembic

Из `backend/`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/alembic upgrade head --sql
```

Для online-команд нужен доступ к PostgreSQL и переменная `DATABASE_URL` вида `postgresql+psycopg://USER:PASSWORD@HOST:5432/DB` либо `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`. В URL специальные символы пароля нужно кодировать; набор `POSTGRES_*` этого не требует. `.env` автоматически не читается локальным Alembic. Compose не публикует порт PostgreSQL на хост, поэтому для текущего окружения удобнее запуск через Docker.

Будущие изменения моделей оформлять новой ревизией:

```sh
.venv/bin/alembic revision --autogenerate -m "описание изменения"
```

Autogenerate требует доступа к БД; перед применением проверять сгенерированный файл. Уже применённые миграции не редактировать. Downgrade начальной миграции удаляет обе таблицы вместе с данными, поэтому не использовать его для обычного обновления.

Настройка основана на [документации Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html) и [PostgreSQL-диалекте SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#psycopg).
