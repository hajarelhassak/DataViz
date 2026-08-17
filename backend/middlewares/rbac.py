"""
Middleware RBAC — décorateur @role_required appliqué sur les routes
sensibles (Partie 9 du guide). La vérification se fait TOUJOURS côté
backend, jamais seulement côté frontend (le frontend cache des boutons,
le backend refuse des actions — Partie 14).
"""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def role_required(allowed_roles: list[str]):
    """
    Usage:
        @role_required(['admin_application', 'admin_systeme'])
        def some_view(): ...
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in allowed_roles:
                return jsonify({"error": "Accès refusé : permissions insuffisantes."}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator