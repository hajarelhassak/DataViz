"""
Modèle User — utilisateurs de DataViz.

Les mots de passe utilisateurs sont :
- hashés avec bcrypt ;
- jamais récupérables.

Ce modèle ne gère pas l'authentification.
La logique est dans AuthService.
"""

import uuid

from datetime import datetime, timezone

import bcrypt

from app.extensions import db



def _uuid():
    return str(uuid.uuid4())



class User(db.Model):

    __tablename__ = "users"



    id = db.Column(
        db.String(36),
        primary_key=True,
        default=_uuid
    )



    nom = db.Column(
        db.String(100),
        nullable=False
    )



    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )



    password_hash = db.Column(
        db.String(255),
        nullable=False
    )



    role_id = db.Column(
        db.String(36),
        db.ForeignKey("roles.id"),
        nullable=False
    )



    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )



    created_at = db.Column(
        db.DateTime,
        default=lambda:
            datetime.now(timezone.utc)
    )



    # ======================
    # Relations
    # ======================


    role = db.relationship(
        "Role",
        back_populates="users"
    )


    projects = db.relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan"
    )


    audit_logs = db.relationship(
        "AuditLog",
        back_populates="user"
    )



    # ======================
    # Password
    # ======================


    def set_password(
        self,
        plain_password:str
    ):

        salt = bcrypt.gensalt(
            rounds=12
        )


        self.password_hash = (
            bcrypt
            .hashpw(
                plain_password.encode("utf-8"),
                salt
            )
            .decode("utf-8")
        )



    def check_password(
        self,
        plain_password:str
    )->bool:


        return bcrypt.checkpw(

            plain_password.encode("utf-8"),

            self.password_hash.encode("utf-8")
        )



    # ======================
    # Serialization
    # ======================


    def to_dict(self):

        return {

            "id":self.id,

            "nom":self.nom,

            "email":self.email,

            "role":
                self.role.nom
                if self.role else None,

            "is_active":self.is_active,

            "created_at":
                self.created_at.isoformat()
                if self.created_at else None
        }



    def __repr__(self):

        return f"<User {self.email}>"