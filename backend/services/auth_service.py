"""
AuthService — gestion de l'authentification.

Responsabilités :
- validation des identifiants ;
- génération JWT ;
- récupération utilisateur courant ;
- préparation RBAC ;
- traçabilité des connexions.
"""

from __future__ import annotations

from typing import Optional

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
)

from models.user import User
from repositories.user_repository import UserRepository
from services.audit_service import AuditService


class AuthenticationError(Exception):
    """Erreur métier d'authentification."""
    pass


class AuthService:

    @staticmethod
    def authenticate(
        email: str,
        password: str,
        ip_address: str | None = None,
    ) -> User:

        email = email.strip().lower()


        user = UserRepository.get_by_email(
            email
        )


        # =====================================================
        # UTILISATEUR INVALIDE
        # =====================================================

        if user is None or not user.is_active:

            AuditService.log(
                None,
                "login_failed",
                {
                    "email": email,
                    "reason": "invalid_user",
                },
                ip_address,
                level="WARNING",
            )


            raise AuthenticationError(
                "Identifiants incorrects."
            )


        # =====================================================
        # MOT DE PASSE INCORRECT
        # =====================================================

        if not user.check_password(password):

            AuditService.log(
                user.id,
                "login_failed",
                {
                    "email": email,
                    "reason": "wrong_password",
                },
                ip_address,
                level="WARNING",
            )


            raise AuthenticationError(
                "Identifiants incorrects."
            )


        # =====================================================
        # LOGIN REUSSI
        # =====================================================

        AuditService.log(
            user.id,
            "login_success",
            {
                "email": email,
                "role": (
                    user.role.nom
                    if user.role
                    else None
                ),
            },
            ip_address,
        )


        return user


    @staticmethod
    def generate_tokens(
        user: User,
    ) -> dict:

        role = (
            user.role.nom
            if user.role
            else None
        )


        access_token = create_access_token(

            identity=str(user.id),

            additional_claims={
                "role": role,
                "type": "access",
            },
        )


        refresh_token = create_refresh_token(

            identity=str(user.id),

            additional_claims={
                "type": "refresh",
            },
        )


        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }


    @staticmethod
    def get_current_user(
        user_id: str,
    ) -> Optional[User]:

        return UserRepository.get_by_id(
            user_id
        )