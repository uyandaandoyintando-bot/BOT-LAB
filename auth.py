from __future__ import annotations

from functools import wraps

from flask import jsonify, request

from backend.config import Config


def require_admin_key(view):
    """
    Protect an endpoint with the BOT-LAB admin API key.

    The client must send:

        Authorization: Bearer YOUR_ADMIN_API_KEY
    """

    @wraps(view)
    def wrapped(*args, **kwargs):
        expected_key = Config.ADMIN_API_KEY

        if not expected_key:
            return jsonify(
                {
                    "error": "Admin authentication is not configured"
                }
            ), 503

        authorization = request.headers.get(
            "Authorization",
            "",
        )

        if not authorization.startswith("Bearer "):
            return jsonify(
                {
                    "error": "Admin authentication required"
                }
            ), 401

        supplied_key = authorization[7:].strip()

        if not supplied_key:
            return jsonify(
                {
                    "error": "Admin authentication required"
                }
            ), 401

        if supplied_key != expected_key:
            return jsonify(
                {
                    "error": "Invalid admin credentials"
                }
            ), 403

        return view(*args, **kwargs)

    return wrapped
