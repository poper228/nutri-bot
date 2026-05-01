# nutri-bot

Telegram-бот для нутрициолога: распознаёт анализы (фото/PDF), ищет отклонения, подтягивает релевантные куски из учебных лекций (RAG) и выдаёт готовый разбор.

## Стек

- Python 3.11+, aiogram 3.x
- PostgreSQL (основные данные) + Qdrant (векторная БД для RAG)
- LLM: Gemini 2.0 Flash (бесплатный тир) с абстракцией `LLMProvider` (можно переключить на Claude API через .env)
- Эмбеддинги: `intfloat/multilingual-e5-large` (sentence-transformers, локально)
- Docker + docker-compose, Alembic, pytest

## Архитектура

```
app/
├── bot/             # aiogram-обработчики (тонкий слой)
├── services/        # бизнес-логика
├── repositories/    # работа с БД
├── models/          # SQLAlchemy + Pydantic
├── infrastructure/  # внешние API (LLM, OCR, vector DB)
└── core/            # конфиг, логирование, DI
```

Правила: bot не знает про БД и LLM. Services не знают про Telegram.

## Запуск (dev)

```bash
uv sync                              # установить зависимости
docker compose up -d                 # поднять Postgres + Qdrant
uv run alembic upgrade head          # применить миграции
uv run python -m app.bot             # запустить бота (позже)
```
