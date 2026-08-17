"""
Modèle AIReport — historique des analyses IA.

Flux :

Schéma BDD
    ↓
Analyse IA
    ↓
Recommandations
    ↓
Calculs locaux
    ↓
Analyse décisionnelle IA

Confidentialité :
- aucune ligne brute stockée ;
- uniquement contexte synthétique ;
- résultats IA JSON.
"""

from __future__ import annotations

import json
import uuid

from datetime import datetime, timezone
from typing import Any, Optional

from app.extensions import db


def _uuid() -> str:
    """Génère un UUID sous forme de chaîne."""
    return str(uuid.uuid4())


class AIReport(db.Model):

    __tablename__ = "ai_reports"

    __table_args__ = (
        db.Index(
            "idx_ai_reports_project",
            "project_id",
        ),
        db.Index(
            "idx_ai_reports_dashboard",
            "dashboard_id",
        ),
        db.Index(
            "idx_ai_reports_status",
            "statut",
        ),
        db.Index(
            "idx_ai_reports_created",
            "created_at",
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
    # RELATIONS
    # ==========================================================

    project_id = db.Column(
        db.String(36),
        db.ForeignKey("projects.id"),
        nullable=False,
    )

    dashboard_id = db.Column(
        db.String(36),
        db.ForeignKey("dashboards.id"),
        nullable=True,
    )

    # ==========================================================
    # PHASE 1 — ANALYSE SCHEMA
    # ==========================================================

    schema_context_json = db.Column(
        db.Text,
        nullable=True,
    )

    detected_domain = db.Column(
        db.String(150),
        nullable=True,
    )

    recommended_kpis_json = db.Column(
        db.Text,
        nullable=True,
    )

    # ==========================================================
    # PHASE 2 — ANALYSE RESULTATS
    # ==========================================================

    prompt_context_json = db.Column(
        db.Text,
        nullable=False,
    )

    resultat_json = db.Column(
        db.Text,
        nullable=True,
    )

    # ==========================================================
    # STATUT
    # ==========================================================

    statut = db.Column(
        db.String(20),
        nullable=False,
        default="success",
    )

    # success | failed | degraded

    erreur_message = db.Column(
        db.String(500),
        nullable=True,
    )

    # ==========================================================
    # PERFORMANCE IA
    # ==========================================================

    response_time_ms = db.Column(
        db.Integer,
        nullable=True,
    )

    tokens_used = db.Column(
        db.Integer,
        nullable=True,
    )

    model_version = db.Column(
        db.String(100),
        nullable=True,
    )

    # ==========================================================
    # DATES
    # ==========================================================

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        onupdate=lambda: datetime.now(
            timezone.utc
        ),
    )

    # ==========================================================
    # RELATIONS SQLALCHEMY
    # ==========================================================

    dashboard = db.relationship(
        "Dashboard",
        back_populates="ai_reports",
    )

    project = db.relationship(
        "Project",
    )

    # ==========================================================
    # KPI RECOMMANDES
    # ==========================================================

    def set_recommended_kpis(
        self,
        data: dict,
    ) -> None:

        if data is None:
            self.recommended_kpis_json = None
            return

        if not isinstance(data, dict):
            raise ValueError(
                "Les KPI recommandés doivent "
                "être un dictionnaire."
            )

        self.recommended_kpis_json = json.dumps(
            data,
            ensure_ascii=False,
        )

    def get_recommended_kpis(self) -> dict:

        if not self.recommended_kpis_json:
            return {}

        try:
            data = json.loads(
                self.recommended_kpis_json
            )

        except (TypeError, ValueError):

            return {}

        return (
            data
            if isinstance(data, dict)
            else {}
        )

    # ==========================================================
    # RESULTAT
    # ==========================================================

    def set_result(
        self,
        result: dict,
    ) -> None:

        if result is None:
            self.resultat_json = None
            return

        if not isinstance(result, dict):
            raise ValueError(
                "Le résultat IA doit "
                "être un dictionnaire."
            )

        self.resultat_json = json.dumps(
            result,
            ensure_ascii=False,
        )

    def get_result(
        self,
    ) -> Optional[dict]:

        if not self.resultat_json:
            return None

        try:
            data = json.loads(
                self.resultat_json
            )

        except (TypeError, ValueError):

            return None

        return (
            data
            if isinstance(data, dict)
            else None
        )

    # ==========================================================
    # SCHEMA
    # ==========================================================

    def set_schema_context(
        self,
        schema: dict,
    ) -> None:

        if schema is None:
            self.schema_context_json = None
            return

        if not isinstance(schema, dict):
            raise ValueError(
                "Le schéma doit être un dictionnaire."
            )

        self.schema_context_json = json.dumps(
            schema,
            ensure_ascii=False,
        )

    def get_schema_context(self) -> Optional[dict]:

        if not self.schema_context_json:
            return None

        try:
            data = json.loads(
                self.schema_context_json
            )

        except (TypeError, ValueError):

            return None

        return (
            data
            if isinstance(data, dict)
            else None
        )

    # ==========================================================
    # SERIALISATION
    # ==========================================================

    def to_dict(self) -> dict[str, Any]:

        return {
            "id": self.id,

            "project_id": self.project_id,

            "dashboard_id": self.dashboard_id,

            "domain": self.detected_domain,

            "recommended_kpis": (
                self.get_recommended_kpis()
            ),

            "result": self.get_result(),

            "statut": self.statut,

            "error": self.erreur_message,

            "response_time_ms": (
                self.response_time_ms
            ),

            "tokens_used": (
                self.tokens_used
            ),

            "model": self.model_version,

            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),

            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            ),
        }

    # ==========================================================
    # REPRESENTATION
    # ==========================================================

    def __repr__(self) -> str:

        return (
            f"<AIReport "
            f"{self.id} "
            f"{self.statut}>"
        )