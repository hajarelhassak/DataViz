"""
AuthController — Endpoints d'authentification.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)

from services.auth_service import (
    AuthService,
    AuthenticationError,
)


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth",
)


# =========================================================
# LOGIN
# =========================================================

@auth_bp.post("/login")
def login():

    payload = request.get_json(
        silent=True
    ) or {}


    email = str(
        payload.get("email", "")
    ).strip().lower()


    password = str(
        payload.get("password", "")
    )


    if not email or not password:

        return jsonify({
            "error": "Email et mot de passe requis."
        }), 400


    try:

        user = AuthService.authenticate(
            email=email,
            password=password,
            ip_address=request.remote_addr,
        )


        tokens = AuthService.generate_tokens(
            user
        )


        return jsonify({

            "access_token":
                tokens["access_token"],

            "refresh_token":
                tokens["refresh_token"],

            "user":
                user.to_dict(),

        }), 200


    except AuthenticationError as exc:

        return jsonify({
            "error": str(exc)
        }), 401


# =========================================================
# REFRESH
# =========================================================

@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():

    identity = get_jwt_identity()


    access_token = create_access_token(
        identity=identity
    )


    return jsonify({
        "access_token": access_token
    }), 200


# =========================================================
# ME
# =========================================================

@auth_bp.get("/me")
@jwt_required()
def me():

    user_id = get_jwt_identity()


    user = AuthService.get_current_user(
        user_id
    )


    if user is None:

        return jsonify({
            "error": "Utilisateur introuvable."
        }), 404


    return jsonify(
        user.to_dict()
    ), 200