"""
UserController — CRUD utilisateurs, réservé aux rôles administrateurs
(RBAC via role_required, Partie 9 du guide).
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from middlewares.rbac import role_required
from models.user import User
from models.role import Role
from repositories.user_repository import UserRepository
from services.audit_service import AuditService
from models.role import Role

user_bp = Blueprint("users", __name__, url_prefix="/api/users")

ADMIN_ROLES = [Role.ADMIN_SYSTEME, Role.ADMIN_APPLICATION]


@user_bp.get("")
@jwt_required()
@role_required(ADMIN_ROLES)
def list_users():
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"
    users = UserRepository.list_all(include_inactive=include_inactive)
    return jsonify([u.to_dict() for u in users]), 200


@user_bp.post("")
@jwt_required()
@role_required(ADMIN_ROLES)
def create_user():
    payload = request.get_json(silent=True) or {}
    required = {"nom", "email", "password", "role"}
    if not required.issubset(payload):
        return jsonify({"error": f"Champs requis : {sorted(required)}"}), 400

    existing = UserRepository.get_by_email(payload["email"].strip().lower())
    if existing:
        return jsonify({"error": "Un utilisateur avec cet email existe déjà."}), 409

    user = UserRepository.create(
        nom=payload["nom"],
        email=payload["email"].strip().lower(),
        password=payload["password"],
        role=Role.query.filter_by(nom=payload["role"]).first(),
        role_nom=payload["role"],
    )
    admin_id = get_jwt_identity()
    AuditService.log(admin_id, "user_created", {"email": user.email}, request.remote_addr)
    return jsonify(user.to_dict()), 201


@user_bp.put("/<user_id>")
@jwt_required()
@role_required(ADMIN_ROLES)
def update_user(user_id):
    user = UserRepository.get_by_id(user_id)
    if user is None:
        return jsonify({"error": "Utilisateur introuvable."}), 404

    payload = request.get_json(silent=True) or {}
    allowed_fields = {"nom", "is_active", "password"}
    fields_to_update = {k: v for k, v in payload.items() if k in allowed_fields}
    updated = UserRepository.update(user, **fields_to_update)
    return jsonify(updated.to_dict()), 200


@user_bp.delete("/<user_id>")
@jwt_required()
@role_required(ADMIN_ROLES)
def deactivate_user(user_id):
    user = UserRepository.get_by_id(user_id)
    if user is None:
        return jsonify({"error": "Utilisateur introuvable."}), 404
    UserRepository.deactivate(user)
    admin_id = get_jwt_identity()
    AuditService.log(admin_id, "user_deactivated", {"email": user.email}, request.remote_addr)
    return jsonify({"message": "Utilisateur désactivé."}), 200