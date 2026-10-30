# DevLab Backend

FastAPI-приложение и миграции PostgreSQL. Запуск API не создаёт таблицы и не применяет миграции автоматически.

## Структура приложения

```text
app/
├── main.py                     # создание FastAPI и подключение роутеров
├── api/
│   ├── routes/
│   │   ├── course_catalog.py   # каталог курсов
│   │   ├── git_course.py       # открытие Git-песочницы
│   │   └── cli.py              # подключение CLI и приём снимков
│   └── schemas/
│       ├── course_catalog.py   # ответ каталога
│       ├── git_course.py       # сессия и шаги курса
│       ├── snapshot.py         # конверт запроса со снимком
│       ├── git_state.py        # содержимое состояния Git
│       └── cli.py              # запрос/ответ подключения CLI
└── db/
    ├── base.py                 # DeclarativeBase и соглашения имён
    ├── config.py               # URL подключения из окружения
    ├── session.py              # AsyncEngine и AsyncSession
    └── models/
        ├── course.py          # courses, course_steps
        └── practice.py        # practice_sessions, practice_snapshots
```

`api/schemas` описывает HTTP-данные, `db/models` — хранение. Alembic импортирует общую Base и регистрирует модели из db/models. Перенос Python-модулей не меняет таблицы и не требует отдельной миграции.

## Контракт страниц и API

| Страница | Метод и API | Ответ |
| --- | --- | --- |
| `/catalog` | `GET /api/v1/catalog` | Список курсов: id=slug, title, description, status, position |
| `/git-course` | `POST /api/v1/git-course`, без тела | session_id, generation, steps |

POST Git находит курс по slug=git, атомарно создаёт или возвращает активную сессию, затем читает её шаги по course_id. Повторное/параллельное открытие не меняет поколение, ключ и даты существующей сессии. Неизвестный курс возвращает 404. Создание подключения CLI и выдача ключа здесь не выполняются.

## Таблицы

SQLAlchemy-модели находятся в `app/db/models/`, отдельно от Pydantic-моделей HTTP в `app/api/schemas/`.

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

Для online-команд нужен доступ к PostgreSQL и переменная `DATABASE_URL` вида `postgresql+psycopg://USER:PASSWORD@HOST:5432/DB` либо `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`. В URL специальные символы пароля нужно кодировать; набор `POSTGRES_*` этого не требует. `.env` автоматически не читается локальным Alembic. Compose публикует PostgreSQL на `127.0.0.1:5432`. При локальном запуске задавать POSTGRES_HOST=127.0.0.1; внутри Docker используется postgres.

Будущие изменения моделей оформлять новой ревизией:

```sh
.venv/bin/alembic revision --autogenerate -m "описание изменения"
```

Autogenerate требует доступа к БД; перед применением проверять сгенерированный файл. Уже применённые миграции не редактировать. Downgrade начальной миграции удаляет обе таблицы вместе с данными, поэтому не использовать его для обычного обновления.

Настройка основана на [документации Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html) и [PostgreSQL-диалекте SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#psycopg).

## Сессии приложения

`app/db/session.py`: один лениво создаваемый AsyncEngine на процесс, async_sessionmaker и зависимость get_session с async with. Запросы и commit выполняются с await, автоматического commit нет. AsyncSession нельзя разделять между конкурентными задачами. Psycopg 3 используется в асинхронном режиме; URL остаётся postgresql+psycopg. Alembic online использует асинхронное подключение и run_sync для операций миграции.

## Модель входящего снимка

`app/api/schemas/snapshot.py` описывает `SnapshotReq`, `git_state.py` — вложенные модели состояния. Это подготовка контракта, а не готовая ручка приёма снимков.

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

`app/db/models/practice.py` содержит `PracticeSession` и `PracticeSnapshot`; обе модели зарегистрированы в общей metadata для Alembic. Для этих таблиц добавлена отдельная миграция `8ca2ebb96c2b`; применение выполняется вручную. Начальная миграция курсов не меняется.

- `practice_sessions`: UUID (`uuid4` задаётся Python), курс, статус active/closed, поколение (0 до первого CLI), хеш ключа, время создания/последнего подключения/закрытия. Частичный уникальный индекс разрешает одну active-сессию на курс. `closed_at` обязателен только при closed.
- `practice_snapshots`: session_id как PK/FK, положительные schema_version/generation/version, JSONB-объект state и received_at. PK ограничивает хранение одним последним снимком. При замене снимка received_at нужно обновлять явно.

Все новые внешние ключи используют RESTRICT: закрытие не означает удаление. Временная разница поколений сессии и последнего снимка допустима. Проверка ключа, принятие только новых версий и атомарная выдача поколения реализуются будущими обработчиками; модели сами этого не обеспечивают.

Жизненный цикл описан в [practice-sessions.md](../docs/practice-sessions.md). Alembic autogenerate требует подключение к текущей БД; выполнять его из окружения с доступом к БД и правом записи в `alembic/versions` (Compose монтирует каталог миграций только для чтения).

## Проверки

Из корня проекта:

```sh
PYTHONPATH=backend backend/.venv/bin/python -m unittest discover -s backend/tests -v
```

Проверки снимков используют временные Git-репозитории. Проверки ручки Git требуют PostgreSQL и включаются явно; они создают и удаляют отдельные временные схемы, не меняя прикладные таблицы:

```sh
docker compose exec -T -e RUN_DB_TESTS=1 backend python - < backend/tests/test_git_course.py
```

Проверяются параллельное открытие одной сессии, сохранение поколения, сортировка/принадлежность шагов, создание после закрытой сессии и отсутствие курса. Для локального запуска можно указать `TEST_DATABASE_URL`; по умолчанию берутся обычные переменные подключения. Без RUN_DB_TESTS проверки PostgreSQL пропускаются.

## Подключение CLI и приём снимков

`POST /api/v1/cli-connect` принимает course_slug, находит активную сессию, увеличивает generation, выдаёт новый ключ и сохраняет только SHA-256 ключа. `POST /api/v1/cli-send-snapshot` принимает SnapshotReq и заголовок Authorization: Bearer. Ответ подтверждает session_id, generation и version после commit. Повтор той же версии с тем же содержимым не обновляет received_at; старые версии/поколения и противоречащие повторы отклоняются.

CLI уже использует каталог и обе ручки для подключения и начального снимка. Постоянная отправка ещё отсутствует. Реальные запросы подключения и начальной доставки проверены; отдельные интеграционные проверки всех веток приёма (ошибки ключей, версий, поколений, повторы и конкуренция) ещё нужны. Код обработчиков — `app/api/routes/cli.py`, модели — `app/api/schemas/cli.py` и `snapshot.py`.
