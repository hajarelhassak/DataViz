"""
Modèles Dashboard et Chart.

Responsabilité :
Dashboard :
- contient une vue analytique complète.
- regroupe plusieurs graphiques.

Chart :
- représente une visualisation liée à un KPI.

Important :
- aucun calcul ici.
- aucun accès aux données clientes.
- uniquement stockage de configuration.
"""
import json
import uuid
from datetime import datetime, timezone

from app.extensions import db


def _uuid():
    return str(uuid.uuid4())


class Dashboard(db.Model):
    __tablename__ = "dashboards"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=_uuid,
    )

    project_id = db.Column(
        db.String(36),
        db.ForeignKey("projects.id"),
        nullable=False,
    )

    nom = db.Column(
        db.String(150),
        nullable=False,
    )

    layout_json = db.Column(
        db.Text,
        nullable=True,
    )

    generated_by_ai = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
    )

    domain = db.Column(
        db.String(150),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    # ==========================================================
    # RELATIONS
    # ==========================================================

    project = db.relationship(
        "Project",
        back_populates="dashboards",
    )

    charts = db.relationship(
        "Chart",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    kpis = db.relationship(
        "KPI",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        lazy="select",
    )

    ai_reports = db.relationship(
        "AIReport",
        back_populates="dashboard",
        cascade="all, delete-orphan",
    )

    # ==========================================================
    # LAYOUT
    # ==========================================================

    def set_layout(self, layout: dict):
        self.layout_json = json.dumps(
            layout or {},
            ensure_ascii=False,
        )

    def get_layout(self) -> dict:
        if not self.layout_json:
            return {}

        try:
            return json.loads(self.layout_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    # ==========================================================
    # SERIALISATION
    # ==========================================================

    def to_dict(self, include_charts=True) -> dict:
        data = {
            "id": self.id,
            "project_id": self.project_id,
            "nom": self.nom,
            "domain": self.domain,
            "generated_by_ai": self.generated_by_ai,
            "layout": self.get_layout(),
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
        }

        if include_charts:
            data["charts"] = [
                chart.to_dict()
                for chart in self.charts
            ]

        return data

    def __repr__(self):
        return f"<Dashboard {self.nom}>"


class Chart(db.Model):
    __tablename__ = "charts"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=_uuid,
    )

    dashboard_id = db.Column(
        db.String(36),
        db.ForeignKey("dashboards.id"),
        nullable=False,
    )

    kpi_source_id = db.Column(
        db.String(36),
        db.ForeignKey("kpis.id"),
        nullable=True,
    )

    type_graphique = db.Column(
        db.String(30),
        nullable=False,
    )

    titre = db.Column(
        db.String(200),
        nullable=False,
    )

    config_json = db.Column(
        db.Text,
        nullable=False,
    )

    generated_by_ai = db.Column(
        db.Boolean,
        default=True,
    )

    # ==========================================================
    # RELATIONS
    # ==========================================================

    dashboard = db.relationship(
        "Dashboard",
        back_populates="charts",
    )

    kpi_source = db.relationship(
        "KPI",
        back_populates="charts",
    )

    # ==========================================================
    # CONFIG
    # ==========================================================

    def set_config(self, config: dict):
        self.config_json = json.dumps(
            config or {},
            ensure_ascii=False,
        )

    def get_config(self) -> dict:
        if not self.config_json:
            return {}

        try:
            return json.loads(self.config_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    # ==========================================================
    # SERIALISATION
    # ==========================================================

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type_graphique,
            "title": self.titre,
            "config": self.get_config(),
            "kpi_source_id": self.kpi_source_id,
            "generated_by_ai": self.generated_by_ai,
        }

    def __repr__(self):
        return (
            f"<Chart "
            f"{self.type_graphique} - "
            f"{self.titre}>"
        )