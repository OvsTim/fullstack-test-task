# File exchanger — заметки для ревьюера

MVP файлообменника: загрузка файлов, эвристический скан, алерты. Стек: FastAPI + Celery/Redis + Postgres + Next.js.

Задача — рефакторинг без смены бизнес-логики. API-контракт (`/files`, `/alerts`, multipart `title + file`) не менялся.

---

## Как запустить

```bash
docker compose -f docker-compose.dev.yml up --build
```

- фронт: http://localhost:3000/test
- бэк (Swagger): http://localhost:8000/docs

Postgres с хоста: `localhost:5434` (внутри сети контейнеров слушает `5432`). Миграции гонятся сами при старте API: `alembic upgrade head && uvicorn…`.

Тесты (нужен поднятый Postgres из compose):

```bash
cd backend
uv sync --group dev
uv run pytest
```

---

## Слои

```
HTTP / Celery
    ↓
api/  (роуты, схемы, HTTP-ошибки)
    ↓
services/  (upload, scan, metadata, alerting, storage)
    ↓
repositories/  (единственное место с session.execute)
    ↓
db/  + диск (LocalStorage)
```

Правила: роут знает схему и сервис, не SQLAlchemy и не диск. Сервис не кидает `HTTPException`. Worker вызывает тот же `process_uploaded_file`, что и тесты.

Фронт:

```
app/page          собирает экран, без fetch
widgets/dashboard orchestration + polling
features/files|alerts   хуки («когда») + ui («как»)
shared/api|types|lib    один api-client
```

---

## Что было сломано и что починили

### Инфраструктура (без этого `compose up` не собирался в рабочий контур)

| Было | Стало |
|---|---|
| Postgres проброшен как `5433:5433`, в `.env` `PGPORT=5433` — контейнер слушает 5432, бэк ходил не туда | `5434:5432`, внутри сети `PGPORT=5432` |
| Брокер в env — `CELERY_BROKER_URL`, в worker — `REDIS_URL` | одно имя: `CELERY_BROKER_URL` |
| Нет healthcheck, worker не ждал Redis, API не ждал Postgres | `service_healthy` + depends_on |
| Миграции руками | entrypoint `alembic upgrade head && uvicorn` |
| Storage «общий» только потому что оба контейнера bind-mount'или `./backend` | именованный volume `file-storage` |

### Домен

- Удаление файла с алертами падало на FK. Добавлены `ON DELETE CASCADE` и relationship `cascade="all, delete-orphan"`.
- Сервис кидал `HTTPException`, конфиг читался через `os.environ.get` в нескольких местах, engine создавался и в API, и в worker отдельно. Теперь: `pydantic-settings`, один engine на процесс, доменные ошибки (`EmptyFile`, `FileNotFound`, …) ловятся в API.

### Фронт

- Всё жило в одном `page.tsx` с захардкоженным `http://localhost:8000`.
- API умел rename/delete — UI нет. Добавлены модалки.
- После upload статус зависал в `uploaded` до ручного refresh. Пока `uploaded` / `processing` — polling раз в 2.5 с.
- Favicon указывал на `/public/favicon.ico` (так Next не раздаёт). Теперь `app/icon.ico`.

---

## Инварианты скана (не менялись)

Пустой файл — ошибка `400 File is empty`, не `clean`. Heuristics:

| Условие | Результат |
|---|---|
| расширение `.exe` / `.bat` / `.cmd` / `.sh` / `.js` | `suspicious` |
| размер > 10 MB | `suspicious` |
| `.pdf` и MIME не `application/pdf` и не `application/octet-stream` | `suspicious` |
| иначе | `clean` (`no threats found`) |

Несколько причин склеиваются через `", "`. PDF с `application/pdf` или `application/octet-stream` — clean.

Алерты после обработки: `info` / `warning` / `critical` в зависимости от `failed` / `requires_attention`.

Это покрыто тестами в `backend/tests/`.

---

## Оптимизация

Исходный pipeline: три Celery-таски (`scan` → `metadata` → `alert`) → три круга через Redis → три сессии → три `SELECT` одной строки. Upload делал `await file.read()` целиком в RAM API. Metadata читала файл целиком (`read_text` / `read_bytes`). В worker крутился глобальный asyncio loop (`run_in_worker_loop`).

Сейчас:

- одна таска `process_uploaded_file(file_id)`;
- одна sync-сессия, одна транзакция, один `SELECT`;
- heuristics смотрят только имя / MIME / size — второй раз файл для скана не читается;
- metadata — один проход чанками 64 KB (текст считает строки/символы, PDF ищет `/Type /Page` в буфере с overlap, чтобы маркер на границе чанка не потерялся);
- upload стримом: чанки на диск, size на лету, пустой файл отбрасывается до записи в БД;
- worker на sync SQLAlchemy, без глобального loop.

Эффект: файл не держим в памяти дважды, нет трёх лишних hop'ов через Redis и трёх повторных чтений строки файла.

---

## Почему не микросервисы / Kafka / S3

Это MVP с одним процессом обработки файла. Резать на сервисы, тащить брокер сообщений «посерьёзнее Redis» или объектное хранилище здесь не закрывает ни один реальный инвариант — только добавляет операционную сложность. Storage уже спрятан за `LocalStorage.save_stream / open / delete`: если понадобится S3, меняется адаптер, не сервис.

Celery оставлен: асинхронная обработка после upload — часть текущего контракта (`uploaded` → `processing` → `processed`), а не то, что нужно «выкинуть ради упрощения».

---

## Что сознательно не делали

- **Auth** — в задании нет пользователей, контракт публичный.
- **ClamAV / антивирус** — скан задан эвристиками, подмена ломает инварианты.
- **Пагинация / кэш списка / Redux / TanStack Query** — объём данных MVP, лишняя абстракция.
- **Tailwind / shadcn** — в проекте уже Bootstrap.
- **Смена API-контракта** — ревьюер должен увидеть тот же `/files`, `/alerts`, Swagger на `:8000/docs`.
