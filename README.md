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

Nginx собирает React + Vite в отдельном этапе Dockerfile, раздаёт статику и проксирует `/api/`. Backend доступен только во внутренней сети; PostgreSQL публикует порт 5432 только на loopback для локальной разработки. Локальная конфигурация использует HTTP и доступна только на loopback; WebSocket проксируется через /ws/; домен и TLS пока не настроены.

## PostgreSQL

Данные хранятся в именованном Docker volume `devlab_postgres_data`. Перезапуск контейнера, пересборка и `docker compose down` сохраняют данные. `docker compose down -v` удаляет volume вместе с данными — не используйте эту команду, если данные нужны. Volume не заменяет резервную копию.

База подготовлена как отдельный сервис. Модели таблиц курсов и шагов, а также миграции Alembic подготовлены в backend (см. [backend/README.md](backend/README.md)); применять миграции нужно вручную. Каталог использует асинхронные SQLAlchemy-сессии; для него требуются применённая миграция и корректные параметры подключения. Сессии и постоянная фоновая доставка из CLI реализованы; браузер получает последний снимок по HTTP и обновляется по событиям WebSocket. В `cli/` есть первая локальная версия CLI с интерактивным bash; установка и запуск описаны в [cli/README.md](cli/README.md).

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

Страница Git: `/git-course`, переход «Открыть» в каталоге. Данные страницы запрашиваются через `POST /api/v1/git-course`; ручка создаёт/возвращает активную сессию и возвращает session_id, generation и шаги Git из PostgreSQL в поле steps. Frontend отображает шаги из API: текстовые блоки и команды. CLI подключается и передаёт начальный и изменившиеся снимки; браузер отображает реальный граф коммитов, HEAD, ветки, индекс, рабочие файлы, конфликты и незавершённые операции.

Структура backend: HTTP-маршруты — `backend/app/api/routes`, Pydantic-контракты — `backend/app/api/schemas`, SQLAlchemy-таблицы — `backend/app/db/models`. Подробная карта файлов и API — в [backend/README.md](backend/README.md).

CLI получает курсы и подключается к активной сессии до выбора папки, в фоне отправляет начальный и последующие изменившиеся снимки с очередью и повторными попытками. Настройки сервера, локальный режим и текущие ограничения — в [cli/README.md](cli/README.md).

### Обновление состояния в браузере

После открытия Git браузер подключает `/ws/practice-sessions/{session_id}` и читает `/api/v1/practice-sessions/{session_id}/snapshot`. Сигнал после commit вызывает повторное чтение. При разрыве соединения последнее состояние остаётся на экране, WebSocket переподключается; HTTP дополнительно сверяется каждые 10 секунд. Версии сравниваются вместе с поколением. Присутствие CLI подтверждается отдельным heartbeat каждые 10 секунд с арендой 35 секунд.

Граф показывает до лимита коммитов снимка, связи родителей, ссылки и HEAD. Ссылки на объекты вне истории перечисляются отдельно (в том числе annotated tags). Содержимое файлов, diff и сообщения коммитов не передаются. Плавные изменения и режим уменьшенного движения закреплены в `frontend/DESIGN.md`. Frontend-проверки: `node --test frontend/src/practiceState.test.js` и `npm --prefix frontend run build`.

Наблюдавшиеся линии веток сохраняют цвет и принадлежность коммитов после merge/fast-forward. Оформление хранится в sessionStorage текущей вкладки по сессии и папке, исторические подписи отличаются от живых refs. Архив снимков на сервере не добавляется; отсутствующие в текущем снимке коммиты не дорисовываются. После закрытия вкладки или без наблюдения до fast-forward восстановить прежнее оформление нельзя.
