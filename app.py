from flask import Flask, jsonify

from backend.config import Config
from backend.routes.products import products_bp
from backend.routes.orders import orders_bp
from backend.routes.paypal import paypal_bp
from backend.routes.licenses import licenses_bp
from backend.routes.downloads import downloads_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # --------------------------------------------------------
    # ROUTES
    # --------------------------------------------------------

    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")
    app.register_blueprint(paypal_bp, url_prefix="/api/paypal")
    app.register_blueprint(licenses_bp, url_prefix="/api/licenses")
    app.register_blueprint(downloads_bp, url_prefix="/api/download")

    # --------------------------------------------------------
    # HEALTH CHECK
    # --------------------------------------------------------

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "BOT-LAB"
        }), 200

    # --------------------------------------------------------
    # ROOT
    # --------------------------------------------------------

    @app.get("/")
    def index():
        return jsonify({
            "name": "BOT-LAB API",
            "status": "online"
        }), 200

    # --------------------------------------------------------
    # ERROR HANDLERS
    # --------------------------------------------------------

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Not found"
        }), 404

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "error": "Internal server error"
        }), 500

    return app


# ------------------------------------------------------------
# LOCAL DEVELOPMENT
# ------------------------------------------------------------

app = create_app()


if __name__ == "__main__":
    import os

    port = int(os.getenv("PORT", "8000"))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
