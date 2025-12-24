This is a FastAPI demo project

| Functions | Packages |
| --------- | -------- |
| Package and Project Manager | uv |
| Virtual Environment | venv |
| Environment Variables | python-dotenv |
| Database | PostgreSQL |
| DBAPI | asyncpg |
| ORM | SQLModel, SQLAlchemy |
| Password hashing | passlib |
| Authentication | OAuth2 with JWT (FastAPI,  PyJWT) |
| Testing | httpx, pytest, pytest-asyncio |
| Schema Migration | alembic |

### Steps to run dev:
1. `uv venv` to create virtual environment
2. `source .venv/bin/activate` to activate virtual environment
3. `uv sync` to install packages
4.  create .env by copying .env.sample
5. `openssl rand -hex 32` to generate secret key
6. use psql to create role and development database
```
CREATE USER fastapi_demo_project_user WITH PASSWORD 'postgres' CREATEDB LOGIN;
CREATE DATABASE fastapi_demo_project;
ALTER DATABASE fastapi_demo_project OWNER TO fastapi_demo_project_user;
```
7. `alembic upgrade head` to migrate database
8. `python -m pytest` to run tests
9. `uvicorn app.main:app --reload --log-level info` to start development server
10. visit localhost:8000/docs to try APIs
