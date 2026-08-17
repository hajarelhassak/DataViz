"""
Modèle KPI — résultat d'un calcul analytique.

Flux :

Schéma BDD
    ↓
AIService
    ↓
Plan KPI
    ↓
AnalyticsService
    ↓
Calcul local
    ↓
KPI sauvegardé

IMPORTANT :
- aucune donnée brute cliente n'est stockée ;
- uniquement des résultats agrégés.
"""

from __future__ import annotations

import json
import uuid

from datetime import datetime, timezone

from app.extensions import db


def _uuid() -> str:
    """Génère un UUID."""
    return str(uuid.uuid4())


class KPI(db.Model):

    __tablename__ = "kpis"

    __table_args__ = (
        db.Index(
            "idx_kpis_project",
            "project_id",
        ),
        db.Index(
            "idx_kpis_connection",
            "connection_id",
        ),
        db.Index(
            "idx_kpis_dashboard",
            "dashboard_id",
        ),
    )

    # ==========================================================
    # IDENTIFIANT
    # ==========================================================

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=_uuid,
    )

    # ==========================================================
    # RELATIONS / CLÉS ÉTRANGÈRES
    # ==========================================================

    project_id = db.Column(
        db.String(36),
        db.ForeignKey("projects.id"),
        nullable=False,
    )

    connection_id = db.Column(
        db.String(36),
        db.ForeignKey("connections.id"),
        nullable=True,
    )

    dashboard_id = db.Column(
        db.String(36),
        db.ForeignKey("dashboards.id"),
        nullable=True,
    )

    # ==========================================================
    # SOURCE
    # ==========================================================

    table_name = db.Column(
        db.String(255),
        nullable=False,
    )

    column_name = db.Column(
        db.String(255),
        nullable=True,
    )

    source_columns_json = db.Column(
        db.Text,
        nullable=True,
    )

    # ==========================================================
    # DEFINITION
    # ==========================================================

    nom = db.Column(
        db.String(150),
        nullable=False,
    )

    operation = db.Column(
        db.String(50),
        nullable=False,
    )

    formule = db.Column(
        db.String(255),
        nullable=False,
    )

    # ==========================================================
    # RESULTAT
    # ==========================================================

    valeur = db.Column(
        db.Float,
        nullable=True,
    )

    unite = db.Column(
        db.String(50),
        nullable=True,
    )

    # numeric | categorical | temporal
    column_type = db.Column(
        db.String(30),
        nullable=True,
    )

    # ==========================================================
    # ORIGINE
    # ==========================================================

    generated_by_ai = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    # ==========================================================
    # DATE
    # ==========================================================

    calculated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ==========================================================
    # RELATIONS SQLALCHEMY
    # ==========================================================

    # Un KPI appartient à un projet.
    #
    # Cette relation nécessite :
    #
    # Project.kpis = db.relationship(
    #     "KPI",
    #     back_populates="project"
    # )

    project = db.relationship(
        "Project",
        back_populates="kpis",
    )

    # Un KPI peut être associé à un dashboard.
    #
    # Cette relation nécessite dans Dashboard :
    #
    # kpis = db.relationship(
    #     "KPI",
    #     back_populates="dashboard",
    #     cascade="all, delete-orphan"
    # )

    dashboard = db.relationship(
        "Dashboard",
        back_populates="kpis",
    )

    # Un KPI peut être utilisé comme source
    # de plusieurs graphiques.
    #
    # Cette relation correspond à :
    #
    # Chart.kpi_source = db.relationship(
    #     "KPI",
    #     back_populates="charts"
    # )

    charts = db.relationship(
        "Chart",
        back_populates="kpi_source",
    )

    # ==========================================================
    # SOURCE COLUMNS
    # ==========================================================

    def set_source_columns(
        self,
        columns: list[str],
    ) -> None:
        """
        Stocke la liste des colonnes sources sous forme JSON.

        Exemple :

        [
            "prix",
            "quantite",
            "date"
        ]
        """

        if columns is None:
            self.source_columns_json = None
            return

        if not isinstance(columns, list):
            raise ValueError(
                "columns doit être une liste."
            )

        normalized = [
            str(column).strip()
            for column in columns
            if str(column).strip()
        ]

        self.source_columns_json = json.dumps(
            normalized,
            ensure_ascii=False,
        )

    def get_source_columns(self) -> list[str]:
        """
        Retourne la liste des colonnes sources.
        """

        if not self.source_columns_json:
            return []

        try:
            data = json.loads(
                self.source_columns_json
            )

        except (TypeError, ValueError, json.JSONDecodeError):
            return []

        return (
            data
            if isinstance(data, list)
            else []
        )

    # ==========================================================
    # SERIALISATION
    # ==========================================================

    def to_dict(self) -> dict:
        """
        Transforme le KPI en dictionnaire
        utilisable par l'API Flask.
        """

        return {
            "id": self.id,

            "project_id": self.project_id,

            "connection_id": self.connection_id,

            "dashboard_id": self.dashboard_id,

            "table": self.table_name,

            "column": self.column_name,

            "source_columns": (
                self.get_source_columns()
            ),

            "name": self.nom,

            "operation": self.operation,

            "formula": self.formule,

            "value": self.valeur,

            "unit": self.unite,

            "type": self.column_type,

            "generated_by_ai": (
                self.generated_by_ai
            ),

            "calculated_at": (
                self.calculated_at.isoformat()
                if self.calculated_at
                else None
            ),
        }

    # ==========================================================
    # REPRESENTATION
    # ==========================================================

    def __repr__(self) -> str:
        return (
            f"<KPI "
            f"{self.nom}="
            f"{self.valeur}>"
        )