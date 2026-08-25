from __future__ import annotations

from functools import wraps

from flask import jsonify, request

from backend.config import Config


def require_admin_key(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        configured_key = Config.ADMIN_API_KEY

        if not configured_key:
            return jsonify({
                "error": "Admin API key is not configured"
            }), 503

        supplied_key = request.headers.get(
            "X-Admin-Key",
            "",
        )

        if supplied_key != configured_key:
            return jsonify({
                "error": "Unauthorized"
            }), 401

        return view(*args, **kwargs)

    return wrapped
