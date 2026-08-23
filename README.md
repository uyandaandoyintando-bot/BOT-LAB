# BOT-LAB

BOT-LAB is a modular Discord digital-product shop. Discord slash commands call the Flask API; the API owns PostgreSQL persistence, PayPal verification, licensing, and secure downloads. Production data never passes through the bot process.

## Layout

`bot/` contains Discord commands and HTTP client code. `backend/` contains Flask app, auth, routes, and services. `database/` contains SQLAlchemy models and Alembic migrations. `tests/` contains isolated API/service tests.

## Local setup

1. Install Python 3.11+ and PostgreSQL.
2. Copy `.env.example` to `.env` and fill values locally only.
3. Create a virtual environment and run `pip install -r requirements.txt`.
4. Set `DATABASE_URL` to a PostgreSQL URL, for example `postgresql+psycopg://user:password@localhost/botlab`.
5. Run `alembic upgrade head`.
6. Run the API with `flask --app backend.app:create_app run --host 0.0.0.0 --port 8000`.
7. Run the bot separately with `python -m bot.main`.

For local tests, the suite sets a temporary SQLite URL automatically; production remains PostgreSQL.

## Railway deployment

1. Push the complete repository to GitHub. Upload the Python source directories (`bot`, `backend`, `database`), `tests`, `requirements.txt`, `Dockerfile`, `railway.toml`, `alembic.ini`, `.env.example`, `.gitignore`, `README.md`, and `database/migrations`.
2. Do **not** upload `.env`, credentials, downloaded product files containing secrets, or any generated `__pycache__` files.
3. In Railway, create a new project from the GitHub repository and add a PostgreSQL service.
4. Add the variables from `.env.example` to the API service. Railway supplies `DATABASE_URL` from the PostgreSQL service. Set `PAYPAL_MODE=sandbox` until live testing is complete.
5. Set `DOWNLOAD_ROOT=downloads` and place product archives in that directory, or mount an object-storage-backed filesystem for production.
6. Run `alembic upgrade head` once in a Railway shell before first use. The container listens on `0.0.0.0:$PORT` through Gunicorn and `/health` is the health check.
7. Deploy the bot as a second Railway service from the same repository with `python -m bot.main`, supplying the same `BOT_API_KEY`, Discord variables, and `BOT_API_BASE_URL` pointing to the public API URL.
8. Configure the PayPal webhook URL as `https://<your-api-domain>/api/paypal/webhook` and copy its webhook ID into `PAYPAL_WEBHOOK_ID`.

Use HTTPS for the public API. Rotate `BOT_API_KEY`, Discord, and PayPal credentials through Railway variables, never GitHub.