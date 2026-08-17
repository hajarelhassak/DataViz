"""
Modèle Project — espace de travail principal.

Un projet représente une analyse DataViz :
- appartient à un utilisateur propriétaire ;
- possède des connexions BDD clientes ;
- possède des KPI calculés localement ;
- possède des dashboards générés.

Le modèle ne contient aucune logique métier.
"""

import uuid
from datetime import datetime, timezone
from app.extensions import db


def _uuid():
    return str(uuid.uuid4())


class Project(db.Model):

    __tablename__ = "projects"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=_uuid
    )

    nom = db.Column(
        db.String(150),
        nullable=False
    )

    entreprise = db.Column(
        db.String(150),
        nullable=True
    )


    owner_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )


    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


    # ==========================
    # Relations
    # ==========================


    owner = db.relationship(
        "User",
        back_populates="projects"
    )


    connections = db.relationship(
        "Connection",
        back_populates="project",
        cascade="all, delete-orphan"
    )


    kpis = db.relationship(
        "KPI",
        back_populates="project",
        cascade="all, delete-orphan"
    )


    dashboards = db.relationship(
        "Dashboard",
        back_populates="project",
        cascade="all, delete-orphan"
    )



    def to_dict(self):

        return {

            "id": self.id,

            "nom": self.nom,

            "entreprise": self.entreprise,

            "owner_id": self.owner_id,

            "created_at":
                self.created_at.isoformat()
                if self.created_at else None
        }



    def __repr__(self):

        return f"<Project {self.nom}>"