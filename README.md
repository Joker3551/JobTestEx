## Stack
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Docker
- Pytest


## Run with Docker
Создать .env в /app и прописать туда:
```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/app_db
```
Открыть терминал и прописать:
```bash
docker-compose up --build
```
Зайти на localhost:8000/docs
Провести тесты Pytest:
```bash
docker exec -it fastapi_app bash
PYTHONPATH=/app pytest tests/
```