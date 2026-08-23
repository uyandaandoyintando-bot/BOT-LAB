from __future__ import annotations

from flask import Flask, jsonify

from backend.config import Config

from backend.routes.products import products_bp
from backend.routes.licenses import licenses_bp
from backend.routes.admin import admin_bp

from database.database import initialize_database


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # ========================================================
    # DATABASE
    # ========================================================

    initialize_database()

    # ========================================================
    # API ROUTES
    # ========================================================

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

    # ========================================================
    # HEALTH CHECK
    # ========================================================

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "service": "BOT-LAB",
            }
        ), 200

    # ========================================================
    # ROOT
    # ========================================================

    @app.get("/")
    def index():
        return jsonify(
            {
                "name": "BOT-LAB API",
                "status": "online",
                "version": "1.0.0",
            }
        ), 200

    # ========================================================
    # 404
    # ========================================================

    @app.errorhandler(404)
    def not_found(error):
        return jsonify(
            {
                "error": "Endpoint not found",
            }
        ), 404

    # ========================================================
    # 500
    # ========================================================

    @app.errorhandler(500)
    def server_error(error):
        return jsonify(
            {
                "error": "Internal server error",
            }
        ), 500

    return app


# ============================================================
# APPLICATION INSTANCE
# ============================================================

app = create_app()


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=False,
    )
