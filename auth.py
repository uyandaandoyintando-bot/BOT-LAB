from __future__ import annotations

from functools import wraps
from flask import current_app, jsonify, request


def require_bot_key(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        expected = current_app.config["BOT_API_KEY"]
        if not expected or request.headers.get("X-Bot-Api-Key") != expected:
            return jsonify({"error": "unauthorized"}), 401
        return view(*args, **kwargs)
    return wrapped


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        configured_role = current_app.config["ADMIN_ROLE_ID"]
        if not configured_role or request.headers.get("X-Admin-Role-Id") != configured_role:
            return jsonify({"error": "forbidden"}), 403
        return view(*args, **kwargs)
    return wrapped