from __future__ import annotations

import os
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from database.database import Base, engine
from .routes import products, orders, paypal, licenses, downloads

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(BOT_API_KEY=os.getenv("BOT_API_KEY", ""), ADMIN_ROLE_ID=os.getenv("DISCORD_ADMIN_ROLE_ID", ""),
                      DOWNLOAD_ROOT=os.getenv("DOWNLOAD_ROOT", "downloads"), PAYPAL_MODE=os.getenv("PAYPAL_MODE", "sandbox"),
                      PAYPAL_CLIENT_ID=os.getenv("PAYPAL_CLIENT_ID", ""), PAYPAL_CLIENT_SECRET=os.getenv("PAYPAL_CLIENT_SECRET", ""),
                      PAYPAL_WEBHOOK_ID=os.getenv("PAYPAL_WEBHOOK_ID", ""))
    if test_config: app.config.update(test_config)
    Base.metadata.create_all(engine)
    limiter = Limiter(key_func=get_remote_address, app=app, default_limits=["300 per minute"])
    app.register_blueprint(products.bp); app.register_blueprint(orders.bp); app.register_blueprint(paypal.bp)
    app.register_blueprint(licenses.bp); app.register_blueprint(downloads.bp)
    @app.get("/health")
    def health(): return jsonify({"status": "ok", "service": "BOT-LAB"})
    @app.errorhandler(404)
    def not_found(_): return jsonify({"error": "not_found"}), 404
    @app.errorhandler(Exception)
    def safe_error(_): return jsonify({"error": "internal_server_error"}), 500
    return app