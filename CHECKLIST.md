# Чеклист по тестовому заданию

Идём по порядку: сначала чтобы всё просто завелось, потом тесты как страховка, потом слои, потом оптимизация, потом фронт, в конце README для ревьюера.

---

## 0. Поднять систему

- [x] Починить Postgres: внутри контейнера слушает `5432`, с хоста проброс типа `5433:5432` (или `5434:5432`). В `.env` для бэка — `PGPORT=5432`
- [x] Свести имя брокера: в env одно, в коде worker то же самое (`CELERY_BROKER_URL` vs `REDIS_URL`)
- [x] Healthcheck для Postgres + `depends_on` с `service_healthy`
- [x] Worker зависит от redis
- [x] Миграции не руками «когда вспомнил»: entrypoint `alembic upgrade head && uvicorn…` или отдельный migrator
- [x] Общий volume на storage между API и worker (сейчас оба смотрят в `./backend` — хрупко)
- [x] `compose up` и руками проверить: upload → list → download → alerts

---

## 1. Зафиксировать бизнес-логику тестами

Без этого рефакторинг — лотерея. API контракт не трогаем: `/files`, `/alerts`, multipart `title + file`, Swagger на `:8000/docs`.

- [x] пустой файл
- [x] `.exe` / опасные расширения → suspicious
- [x] файл больше 10MB
- [x] PDF с кривым MIME
- [x] удаление файла, когда на нём уже есть alerts (тест `xfail`: FK без cascade — упадёт; фикс в пункте 3)
- [x] смена title

---

## 2. Рефакторинг бэка — инфраструктура

Не надо Clean Architecture на 40 файлов. Нормальный modular monolith.

- [ ] `core/config.py` — pydantic-settings, без `os.environ.get` по всему коду
- [ ] `core/enums.py` — статусы и уровни алертов
- [ ] `db/session.py` — один engine на процесс, lifespan на create/dispose
- [ ] `api/deps.py` + роутеры `files` / `alerts` + обработчики ошибок
- [ ] `main.py` — `create_app()`, lifespan (mkdir storage и всё такое)

Сигнатуры эндпоинтов пока не меняем.

Примерная раскладка:

```
backend/src/
  main.py
  api/          deps, routers
  core/         config, enums
  db/           session, models
  repositories/
  services/     file, storage, scanning, metadata, alerting
  workers/      celery_app, tasks
  schemas/
```

---

## 3. Рефакторинг бэка — домен

- [ ] Репозитории — единственное место, где `session.execute`
- [ ] `file_service` — upload / update / delete / download
- [ ] `storage` — абстракция диска (`save` / `open` / `delete`, со стримом), чтобы потом можно было сунуть S3
- [ ] scan / metadata / alerting — обычные функции без FastAPI и Celery внутри
- [ ] Свои ошибки (`FileNotFound`, `EmptyFile` …) → ловятся в API. Из сервисов `HTTPException` не кидаем
- [ ] При удалении файла — cascade alerts или явное удаление
- [ ] Relationships в моделях

Прогнать тесты из пункта 1.

Правила, которые стоит держать в голове (и потом коротко написать в README):

1. Роут знает только схему и сервис, не SQLAlchemy и не диск.
2. Сервис не знает про HTTP.

---

## 4. Неочевидная оптимизация

Вот это и есть «дополнительная задача», а не пагинация / кэш списка / переезд на S3 / выкинуть Celery.

Сейчас: три таски → три сессии → три SELECT одной строки → лишние круги через Redis → metadata читает файл целиком в память. Upload тоже буферит весь файл в RAM API.

- [ ] Одна таска `process_uploaded_file(file_id)` (или явный chain), без трёх ручных `.delay`
- [ ] Одна сессия, одна транзакция, один SELECT файла
- [ ] Один проход по файлу: и heuristics, и metadata
- [ ] Не `read_bytes()` целиком: строки/символы чанками, PDF — искать `/Type /Page` в буфере
- [ ] Upload стримом: писать чанками, size на лету, лимит до записи в БД
- [ ] Убрать `run_in_worker_loop` с глобальным loop — это антипаттерн. В worker лучше sync SQLAlchemy, либо loop на задачу / `async_to_sync`

Для ревьюера одной фразой: схлопнул три I/O-таски в один pass + streaming upload, файл не держим в памяти дважды.

---

## 5. Слои фронта

Сейчас всё в одном `page.tsx`. Redux не нужен.

```
frontend/src/
  app/                 page только собирает экран
  shared/api|types|lib
  features/files       hooks + ui (таблица, модалка)
  features/alerts      hooks + ui
  widgets/dashboard
```

- [ ] Один api-client: `NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'`
- [ ] В page нет `fetch` и нет знания URL бэка
- [ ] Хуки решают «когда грузить», UI — «как показать»
- [ ] Пока статус `uploaded` / `processing` — короткий polling (2–3 сек), или хотя бы refetch после upload с паузой
- [ ] В UI добавить rename и delete — API уже умеет, иначе рефакторинг чисто косметический
- [ ] Починить favicon (`app/icon` или `/favicon.ico`, не `/public/...`)

---

## 6. README для ревьюера

Коротко и по делу:

- [ ] как запустить
- [ ] ASCII-схема слоёв (буквально 5–7 строк)
- [ ] какие баги нашли
- [ ] инварианты бизнес-логики (таблица heuristics)
- [ ] что за оптимизация и какой от неё эффект
- [ ] почему не микросервисы / Kafka / S3
- [ ] что сознательно не делали (auth, ClamAV, пагинация…) и почему


