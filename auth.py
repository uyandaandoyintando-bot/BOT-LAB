from __future__ import annotations

import hmac
import os
from functools import wraps

from flask import jsonify, request


def get_admin_api_key() -> str:
    return os.getenv("ADMIN_API_KEY", "").strip()


def require_admin_key(view):
    """
    Protect an admin endpoint with:

        Authorization: Bearer YOUR_ADMIN_API_KEY
    """

    @wraps(view)
    def wrapped(*args, **kwargs):
        configured_key = get_admin_api_key()

        if not configured_key:
            return jsonify({
                "error": "Admin API is not configured"
            }), 503

        authorization = request.headers.get(
            "Authorization",
            "",
        ).strip()

        if not authorization.startswith("Bearer "):
            return jsonify({
                "error": "Authorization required"
            }), 401

        supplied_key = authorization[
            len("Bearer "):
        ].strip()

        if not supplied_key:
            return jsonify({
                "error": "Authorization required"
            }), 401

        if not hmac.compare_digest(
            supplied_key,
            configured_key,
        ):
            return jsonify({
                "error": "Invalid admin credentials"
            }), 403

        return view(*args, **kwargs)

    return wrapped
