"""
AuditService — gestion centralisée des journaux d'audit.

Responsabilités :
- tracer les actions importantes ;
- protéger les informations sensibles ;
- fournir les logs pour le dashboard administrateur.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from app.extensions import db
from models.audit_log import AuditLog


SENSITIVE_KEYS = {
    "password",
    "encrypted_password",
    "mot_de_passe",
    "secret",
    "api_key",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "connection_string",
}


class AuditService:

    @staticmethod
    def _sanitize(value):

        if isinstance(value, dict):

            return {
                key: (
                    "***"
                    if str(key).lower() in SENSITIVE_KEYS
                    else AuditService._sanitize(val)
                )
                for key, val in value.items()
            }

        if isinstance(value, list):

            return [
                AuditService._sanitize(item)
                for item in value
            ]

        return value

    @staticmethod
    def log(
        user_id=None,
        action=None,
        details=None,
        ip_address=None,
        level="INFO",
    ):
        """
        Enregistre un événement d'audit.

        `level` est accepté pour compatibilité avec les services
        existants, mais n'est pas envoyé au modèle AuditLog.
        """

        safe_details = AuditService._sanitize(
            details or {}
        )

        try:

            entry = AuditLog(
                user_id=user_id,
                action=action,
                details_json=json.dumps(
                    safe_details,
                    ensure_ascii=False,
                    default=str,
                ),
                ip_address=ip_address,
                created_at=datetime.now(timezone.utc),
            )

            db.session.add(entry)
            db.session.commit()

            return entry

        except Exception:

            db.session.rollback()

            raise

    @staticmethod
    def list_recent(limit=100):

        return (
            AuditLog.query
            .order_by(
                AuditLog.created_at.desc()
            )
            .limit(limit)
            .all()
        )

    @staticmethod
    def count_actions(action):

        return (
            AuditLog.query
            .filter_by(action=action)
            .count()
        )