# DevLab

Базовый шаблон DevLab — сервиса курсов по разным технологиям.

## Сборка без запуска

Нужен Docker с Compose:

```sh
cp .env.example .env
docker compose build
```

Команда только собирает образы backend и nginx (с frontend внутри), контейнеры не запускает. PostgreSQL использует готовый образ `postgres:17-alpine`.

## Запуск вручную

После сборки применить образы и запустить приложение: `docker compose up -d --force-recreate`. Пересборка сама по себе не обновляет уже работающие контейнеры.

Главная страница: http://localhost:8080. Frontend: `/catalog` — каталог курсов, `/` переводит на `/catalog`; неизвестные пути показывают страницу 404. Backend: `GET /api/v1/catalog`. Каталог получает данные из API. Каталог читает записи PostgreSQL; статус planned отображается как «В разработке». Автоматические API docs отключены.

```sh
curl http://localhost:8080/api/v1/catalog
docker compose ps
docker compose logs -f
```

Nginx собирает React + Vite в отдельном этапе Dockerfile, раздаёт статику и проксирует `/api/`. Backend и PostgreSQL не публикуют порты на хост. Локальная конфигурация использует HTTP и доступна только на loopback; домен, TLS и WebSocket будут настроены при реализации соответствующих функций.

## PostgreSQL

Данные хранятся в именованном Docker volume `devlab_postgres_data`. Перезапуск контейнера, пересборка и `docker compose down` сохраняют данные. `docker compose down -v` удаляет volume вместе с данными — не используйте эту команду, если данные нужны. Volume не заменяет резервную копию.

База подготовлена как отдельный сервис. Модели таблиц курсов и шагов, а также миграции Alembic подготовлены в backend (см. [backend/README.md](backend/README.md)); применять миграции нужно вручную. Каталог использует асинхронные SQLAlchemy-сессии; для него требуются применённая миграция и корректные параметры подключения. Сессии и синхронизация ещё не реализованы. В `cli/` есть первая локальная версия CLI с интерактивным bash; установка и запуск описаны в [cli/README.md](cli/README.md).

## Разработка без Docker

Backend (Python 3.13):

```sh
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Frontend (Node.js 22):

```sh
cd frontend
npm ci
npm run dev
```

Vite проксирует `/api/` на localhost:8000. Production-сборка: `npm run build`. Описание дизайн-системы — `frontend/DESIGN.md`, токены — `frontend/src/tokens.css`.

## Адреса

| Режим | Главная | Курсы | API |
| --- | --- | --- | --- |
| Docker / nginx | http://localhost:8080/ | http://localhost:8080/catalog | http://localhost:8080/api/v1/ |
| Vite dev | http://localhost:5173/ | http://localhost:5173/catalog | http://localhost:5173/api/v1/ |
| Vite preview | http://localhost:4173/ | http://localhost:4173/catalog | http://localhost:4173/api/v1/ |

Для Vite dev и preview отдельно запустите backend на порту 8000. Порт 8000 обслуживает JSON API, а не HTML-страницы. Прокси nginx и Vite сохраняют `/api/v1/` в запросах. Адреса frontend собраны в `frontend/src/routes.js`; backend использует APIRouter с префиксом `/api/v1`.

Страница Git: `/git-course`, переход «Открыть» в каталоге. Данные страницы запрашиваются через `GET /api/v1/git-course`; пока это заглушка, синхронизация CLI и граф репозитория ещё не подключены.
