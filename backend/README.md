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

Миграция `20261030_0001` создаёт только таблицы и ограничения, без курсов и шагов. Каталог API читает таблицу courses через AsyncSession. Наличие подготовленного файла миграции не означает, что он уже применён к твоей базе.

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

## Сессии приложения

`app/db/session.py`: один лениво создаваемый AsyncEngine на процесс, async_sessionmaker и зависимость get_session с async with. Запросы и commit выполняются с await, автоматического commit нет. AsyncSession нельзя разделять между конкурентными задачами. Psycopg 3 используется в асинхронном режиме; URL остаётся postgresql+psycopg. Alembic online использует асинхронное подключение и run_sync для операций миграции.

## Модель входящего снимка

`app/models/snapshots/snapshot.py` описывает `SnapshotReq`, `state.py` — вложенные модели состояния. Это подготовка контракта, а не готовая ручка приёма снимков.

В `state` передаётся именно поле `state` локального файла CLI, без обёртки `generator/version/updated_at`. Версия доставки, поколение и сессия находятся на верхнем уровне запроса.

Дискриминатор `kind` выбирает один из трёх форматов:

- `repository`: `path`, `head`, `branch`, `head_kind`, `files`, `refs`, `commits`, `history_limit`, `operations`.
- `no_repository`: выбранная `path` без Git-репозитория.
- `unavailable`: недоступная `path`.

Коммит содержит полный `id` и `parents`; принимаются SHA-1 и SHA-256. Родители могут быть вне ограниченной истории. В текущем контракте предел истории — до 200 коммитов.

Файл содержит `path`, отдельные символы `index` и `worktree` из porcelain, `conflict` и необязательный `original_path`. Пробел в статусе значим. Для переименования/копирования исходный путь обязателен.

`refs` сохраняет формат текущего CLI: строки `refs/heads/main <хеш>` / `refs/tags/v1 <хеш>`. Ссылка тега не обязана указывать непосредственно на коммит. `operations` содержит признаки merge, cherry-pick, revert, rebase и bisect, которые собирает CLI.

Для `unborn` HEAD пустой, ветка указана; для `branch` указаны оба значения; для `detached` есть HEAD без ветки. Неизвестные поля, некорректные хеши и противоречивые состояния отклоняются. Полная семантическая проверка Git и сетевой лимит размера запроса в эти модели не входят.

Проверка моделей на настоящих временных репозиториях:

```sh
PYTHONPATH=backend backend/.venv/bin/python -m unittest discover -s backend/tests -v
```

## Модели сессий песочницы

`app/schemas/snapshot.py` содержит `PracticeSession` и `PracticeSnapshot`; обе модели зарегистрированы в общей metadata для Alembic. Миграцию для этих таблиц нужно создать и применить отдельно: начальная миграция курсов не меняется.

- `practice_sessions`: UUID (`uuid4` задаётся Python), курс, статус active/closed, поколение (0 до первого CLI), хеш ключа, время создания/последнего подключения/закрытия. Частичный уникальный индекс разрешает одну active-сессию на курс. `closed_at` обязателен только при closed.
- `practice_snapshots`: session_id как PK/FK, положительные schema_version/generation/version, JSONB-объект state и received_at. PK ограничивает хранение одним последним снимком. При замене снимка received_at нужно обновлять явно.

Все новые внешние ключи используют RESTRICT: закрытие не означает удаление. Временная разница поколений сессии и последнего снимка допустима. Проверка ключа, принятие только новых версий и атомарная выдача поколения реализуются будущими обработчиками; модели сами этого не обеспечивают.

Жизненный цикл описан в [practice-sessions.md](../docs/practice-sessions.md). Alembic autogenerate требует подключение к текущей БД; выполнять его из окружения с доступом к БД и правом записи в `alembic/versions` (Compose монтирует каталог миграций только для чтения).
