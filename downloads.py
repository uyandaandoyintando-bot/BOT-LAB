from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from database.database import SessionLocal
from database.models import DownloadToken, License


downloads_bp = Blueprint("downloads", __name__)


def hash_token(token: str) -> str:
    return hashlib.sha512(
        token.strip().encode("utf-8")
    ).hexdigest()


# ============================================================
# CREATE DOWNLOAD TOKEN
# ============================================================

@downloads_bp.post("/token")
def create_download_token():
    data = request.get_json(silent=True) or {}

    license_key = str(
        data.get("license_key", "")
    ).strip()

    if not license_key:
        return jsonify({
            "error": "license_key is required"
        }), 400

    license_hash = hashlib.sha512(
        license_key.encode("utf-8")
    ).hexdigest()

    with SessionLocal() as db:
        license_record = (
            db.query(License)
            .filter(
                License.license_key_hash
                == license_hash
            )
            .first()
        )

        if license_record is None:
            return jsonify({
                "error": "Invalid license key"
            }), 404

        if license_record.status != "active":
            return jsonify({
                "error": "License is not active"
            }), 403

        if (
            license_record.expires_at
            and datetime.utcnow()
            >= license_record.expires_at
        ):
            license_record.status = "expired"
            db.commit()

            return jsonify({
                "error": "License has expired"
            }), 403

        raw_token = secrets.token_urlsafe(32)

        token = DownloadToken(
            token_hash=hash_token(raw_token),
            license_id=license_record.id,
            expires_at=(
                datetime.utcnow()
                + timedelta(minutes=15)
            ),
            download_count=0,
            max_downloads=3,
            revoked=False,
        )

        db.add(token)
        db.commit()

        return jsonify({
            "success": True,
            "download_token": raw_token,
            "expires_at": token.expires_at.isoformat(),
        }), 201


# ============================================================
# DOWNLOAD
# ============================================================

@downloads_bp.get("/<token>")
def download(token: str):
    token_hash = hash_token(token)

    with SessionLocal() as db:
        download_token = (
            db.query(DownloadToken)
            .filter(
                DownloadToken.token_hash
                == token_hash
            )
            .first()
        )

        if download_token is None:
            return jsonify({
                "error": "Invalid download token"
            }), 404

        if download_token.revoked:
            return jsonify({
                "error": "Download token has been revoked"
            }), 403

        if (
            datetime.utcnow()
            >= download_token.expires_at
        ):
            return jsonify({
                "error": "Download token has expired"
            }), 403

        if (
            download_token.download_count
            >= download_token.max_downloads
        ):
            return jsonify({
                "error": "Download limit reached"
            }), 403

        license_record = db.get(
            License,
            download_token.license_id,
        )

        if license_record is None:
            return jsonify({
                "error": "License not found"
            }), 404

        if license_record.status != "active":
            return jsonify({
                "error": "License is not active"
            }), 403

        download_url = os.getenv(
            "DOWNLOAD_BASE_URL",
            "",
        ).strip()

        if not download_url:
            return jsonify({
                "error": (
                    "Download URL is not configured"
                )
            }), 503

        download_token.download_count += 1
        db.commit()

        return jsonify({
            "success": True,
            "download_url": download_url,
            "downloads_remaining": (
                download_token.max_downloads
                - download_token.download_count
            ),
        }), 200
