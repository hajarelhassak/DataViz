"""
Modèles des connexions aux bases de données clientes.

Connection :
Stocke uniquement la configuration nécessaire pour accéder
à une base de données externe.

Important :
- Aucun mot de passe en clair n'est stocké.
- Aucune donnée métier de la base cliente n'est stockée ici.
- Les données clientes sont lues temporairement pour analyse.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.extensions import db


# ==========================================================
# UTILITAIRE UUID
# ==========================================================

def _uuid() -> str:
    """Génère un identifiant UUID unique."""
    return str(uuid.uuid4())


# ==========================================================
# CONNECTION
# ==========================================================

class Connection(db.Model):
    """
    Connexion à une base de données cliente.
    """

    __tablename__ = "connections"

    # ------------------------------------------------------
    # IDENTIFIANT
    # ------------------------------------------------------

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=_uuid,
    )

    # ------------------------------------------------------
    # PROJET
    # ------------------------------------------------------

    project_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "projects.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------
    # NOM
    # ------------------------------------------------------

    nom = db.Column(
        db.String(150),
        nullable=False,
    )

    # ------------------------------------------------------
    # TYPE DE MOTEUR
    # ------------------------------------------------------

    engine_type = db.Column(
        db.String(30),
        nullable=False,
        index=True,
    )

    # ======================================================
    # SQLITE
    # ======================================================

    database_path = db.Column(
        db.Text,
        nullable=True,
    )

    # ======================================================
    # BASES SERVEUR
    # ======================================================

    host = db.Column(
        db.String(255),
        nullable=True,
    )

    port = db.Column(
        db.Integer,
        nullable=True,
    )

    database_name = db.Column(
        db.String(150),
        nullable=True,
    )

    username = db.Column(
        db.String(150),
        nullable=True,
    )

    encrypted_password = db.Column(
        db.Text,
        nullable=True,
    )

    # ======================================================
    # HISTORIQUE DU TEST
    # ======================================================

    last_tested_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    last_test_success = db.Column(
        db.Boolean,
        nullable=True,
    )

    # ======================================================
    # DATES
    # ======================================================

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ======================================================
    # RELATION PROJET
    # ======================================================

    project = db.relationship(
        "Project",
        back_populates="connections",
    )

    # ======================================================
    # TABLES AUTORISEES
    # ======================================================

    selected_tables = db.relationship(
        "SelectedTable",
        back_populates="connection",
        cascade="all, delete-orphan",
        lazy=True,
    )

    # ======================================================
    # METADONNEES DU SCHEMA
    # ======================================================

    schema_metadata = db.relationship(
        "SchemaMetadata",
        back_populates="connection",
        cascade="all, delete-orphan",
        uselist=False,
        lazy=True,
    )

    # ======================================================
    # KPI
    # ======================================================

    kpis = db.relationship(
        "KPI",
        backref="connection",
        cascade="all, delete-orphan",
        lazy=True,
    )

    # ======================================================
    # SERIALIZATION
    # ======================================================

    def to_dict(self) -> dict:
        """
        Transforme la connexion en dictionnaire JSON-safe.

        Le mot de passe chiffré n'est jamais retourné
        au frontend.
        """

        return {
            "id": self.id,
            "project_id": self.project_id,
            "nom": self.nom,
            "engine_type": self.engine_type,

            "database_path": self.database_path,

            "host": self.host,
            "port": self.port,
            "database_name": self.database_name,
            "username": self.username,

            "last_test_success": self.last_test_success,

            "last_tested_at": (
                self.last_tested_at.isoformat()
                if self.last_tested_at
                else None
            ),

            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
        }

    # ======================================================
    # REPRESENTATION
    # ======================================================

    def __repr__(self) -> str:
        return (
            f"<Connection "
            f"{self.id} "
            f"{self.nom} "
            f"{self.engine_type}>"
        )


# ==========================================================
# SELECTED TABLE
# ==========================================================

class SelectedTable(db.Model):
    """
    Liste blanche des tables autorisées pour l'analyse.

    DataViz ne doit lire une table que si elle figure
    dans cette liste.
    """

    __tablename__ = "selected_tables"

    # ------------------------------------------------------
    # IDENTIFIANT
    # ------------------------------------------------------

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=_uuid,
    )

    # ------------------------------------------------------
    # CONNEXION
    # ------------------------------------------------------

    connection_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "connections.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------
    # NOM TABLE
    # ------------------------------------------------------

    table_name = db.Column(
        db.String(255),
        nullable=False,
    )

    # ------------------------------------------------------
    # DATE AJOUT
    # ------------------------------------------------------

    added_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ------------------------------------------------------
    # RELATION CONNECTION
    # ------------------------------------------------------

    connection = db.relationship(
        "Connection",
        back_populates="selected_tables",
    )

    # ------------------------------------------------------
    # REPRESENTATION
    # ------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<SelectedTable "
            f"{self.connection_id} "
            f"{self.table_name}>"
        )