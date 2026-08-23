from __future__ import annotations

from flask import Flask, jsonify

from backend.config import Config
from backend.routes.products import products_bp
from database.database import initialize_database


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    initialize_database()

    # --------------------------------------------------------
    # API ROUTES
    # --------------------------------------------------------

    app.register_blueprint(
        products_bp,
        url_prefix="/api/products",
    )

    # --------------------------------------------------------
    # HEALTH CHECK
    # --------------------------------------------------------

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "service": "BOT-LAB",
            }
        ), 200

    # --------------------------------------------------------
    # ROOT
    # --------------------------------------------------------

    @app.get("/")
    def index():
        return jsonify(
            {
                "name": "BOT-LAB API",
                "status": "online",
            }
        ), 200

    # --------------------------------------------------------
    # 404
    # --------------------------------------------------------

    @app.errorhandler(404)
    def not_found(error):
        return jsonify(
            {
                "error": "Endpoint not found",
            }
        ), 404

    # --------------------------------------------------------
    # 500
    # --------------------------------------------------------

    @app.errorhandler(500)
    def server_error(error):
        return jsonify(
            {
                "error": "Internal server error",
            }
        ), 500

    return app


# Gunicorn uses:
# backend.app:app

app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=False,
    )
