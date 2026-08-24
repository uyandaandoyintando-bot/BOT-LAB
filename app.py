from __future__ import annotations

from flask import Flask, jsonify

from backend.config import Config
from backend.routes.admin import admin_bp
from backend.routes.licenses import licenses_bp
from backend.routes.paypal import paypal_bp
from backend.routes.products import products_bp
from database.database import initialize_database


def create_app() -> Flask:
    app = Flask(__name__)

    # --------------------------------------------------------
    # Configuration
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
        admin_bp,
        url_prefix="/api/admin",
    )

    app.register_blueprint(
        licenses_bp,
        url_prefix="/api/licenses",
    )

    app.register_blueprint(
        paypal_bp,
        url_prefix="/api/paypal",
    )

    app.register_blueprint(
        products_bp,
        url_prefix="/api/products",
    )

    # --------------------------------------------------------
    # Health check
    # --------------------------------------------------------

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "BOT-LAB",
        }), 200

    # --------------------------------------------------------
    # API information
    # --------------------------------------------------------

    @app.get("/")
    def index():
        return jsonify({
            "service": "BOT-LAB",
            "status": "online",
            "endpoints": {
                "health": "/health",
                "products": "/api/products",
                "licenses": "/api/licenses",
                "paypal": "/api/paypal",
                "admin": "/api/admin",
            },
        }), 200

    # --------------------------------------------------------
    # 404 handler
    # --------------------------------------------------------

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Not found",
        }), 404

    # --------------------------------------------------------
    # General error handler
    # --------------------------------------------------------

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "Internal server error",
        }), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=False,
                      )
