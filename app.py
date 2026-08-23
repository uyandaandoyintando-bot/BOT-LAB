from __future__ import annotations

from flask import Flask, jsonify

from backend.config import Config
from database.database import initialize_database


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    initialize_database()

    # --------------------------------------------------------
    # Health
    # --------------------------------------------------------

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "service": "BOT-LAB",
            }
        )

    # --------------------------------------------------------
    # Root
    # --------------------------------------------------------

    @app.get("/")
    def index():
        return jsonify(
            {
                "name": "BOT-LAB API",
                "status": "online",
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=False,
    )
