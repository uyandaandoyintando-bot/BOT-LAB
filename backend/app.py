from __future__ import annotations

from flask import Flask, jsonify

from backend.config import Config
from backend.routes.admin import admin_bp
from backend.routes.downloads import downloads_bp
from backend.routes.licenses import licenses_bp
from backend.routes.paypal import paypal_bp
from backend.routes.products import products_bp
from database.database import initialize_database


def create_app() -> Flask:
    app = Flask(__name__)

    # --------------------------------------------------------
    # Basic configuration
    # --------------------------------------------------------

    app.config["JSON_SORT_KEYS"] = False

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    initialize_database()

    # --------------------------------------------------------
    # Routes
    # --------------------------------------------------------

    app.register_blueprint(
        products_bp,
        url_prefix="/api/products",
    )

    app.register_blueprint(
        licenses_bp,
        url_prefix="/api/licenses",
    )

    app.register_blueprint(
        admin_bp,
        url_prefix="/api/admin",
    )

    app.register_blueprint(
        paypal_bp,
        url_prefix="/api/paypal",
    )

    app.register_blueprint(
        downloads_bp,
        url_prefix="/api/downloads",
    )

    # --------------------------------------------------------
    # Health check
    # --------------------------------------------------------

    @app.get("/")
    def index():
        return jsonify({
            "name": "BOT-LAB API",
            "status": "online",
        })

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
        })

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
)
