"""
Modèle SchemaMetadata — cache du schéma d'une connexion cliente.

Stocke uniquement les métadonnées :
- tables
- colonnes
- types
- relations éventuelles
- recommandations IA

Aucune donnée métier brute n'est stockée.
"""

from __future__ import annotations

import json
import uuid

from datetime import datetime, timezone

from app.extensions import db


# ==========================================================
# UTILITAIRE UUID
# ==========================================================

def _uuid() -> str:
    return str(uuid.uuid4())


# ==========================================================
# SCHEMA METADATA
# ==========================================================

class SchemaMetadata(db.Model):

    __tablename__ = "schema_metadata"

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
        unique=True,
        index=True,
    )

    # ======================================================
    # SCHEMA
    # ======================================================

    schema_json = db.Column(
        db.Text,
        nullable=False,
        default="{}",
    )

    explored_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ======================================================
    # ANALYSE IA
    # ======================================================

    ai_processed = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    detected_domain = db.Column(
        db.String(150),
        nullable=True,
    )

    recommended_kpis_json = db.Column(
        db.Text,
        nullable=True,
    )

    recommended_charts_json = db.Column(
        db.Text,
        nullable=True,
    )

    # ======================================================
    # RELATION
    # ======================================================

    connection = db.relationship(
        "Connection",
        back_populates="schema_metadata",
    )

    # ======================================================
    # SCHEMA
    # ======================================================

    def set_schema(self, schema: dict) -> None:
        """
        Enregistre le schéma sous forme JSON.
        """

        if not isinstance(schema, dict):
            raise ValueError(
                "Le schéma doit être un dictionnaire."
            )

        self.schema_json = json.dumps(
            schema,
            ensure_ascii=False,
        )

        self.explored_at = datetime.now(timezone.utc)

    def get_schema(self) -> dict:
        """
        Retourne le schéma sous forme de dictionnaire.
        """

        if not self.schema_json:
            return {}

        try:
            result = json.loads(
                self.schema_json
            )

            return (
                result
                if isinstance(result, dict)
                else {}
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            return {}

    # ======================================================
    # RECOMMANDATIONS IA
    # ======================================================

    def set_ai_recommendation(
        self,
        result: dict,
    ) -> None:
        """
        Enregistre les recommandations produites par l'IA.
        """

        result = result or {}

        self.ai_processed = True

        self.detected_domain = result.get(
            "domaine_detecte"
        )

        self.recommended_kpis_json = json.dumps(
            result.get(
                "kpi_recommandes",
                [],
            ),
            ensure_ascii=False,
        )

        self.recommended_charts_json = json.dumps(
            result.get(
                "graphiques_recommandes",
                [],
            ),
            ensure_ascii=False,
        )

    def get_recommended_kpis(self) -> list:
        """
        Retourne les KPI recommandés.
        """

        if not self.recommended_kpis_json:
            return []

        try:
            result = json.loads(
                self.recommended_kpis_json
            )

            return (
                result
                if isinstance(result, list)
                else []
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            return []

    def get_recommended_charts(self) -> list:
        """
        Retourne les graphiques recommandés.
        """

        if not self.recommended_charts_json:
            return []

        try:
            result = json.loads(
                self.recommended_charts_json
            )

            return (
                result
                if isinstance(result, list)
                else []
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            return []

    # ======================================================
    # API
    # ======================================================

    def to_dict(self) -> dict:
        """
        Sérialisation JSON-safe.
        """

        return {
            "id": self.id,

            "connection_id": self.connection_id,

            "schema": self.get_schema(),

            "ai_processed": self.ai_processed,

            "domain": self.detected_domain,

            "recommended_kpis":
                self.get_recommended_kpis(),

            "recommended_charts":
                self.get_recommended_charts(),

            "explored_at": (
                self.explored_at.isoformat()
                if self.explored_at
                else None
            ),
        }

    # ======================================================
    # REPRESENTATION
    # ======================================================

    def __repr__(self) -> str:
        return (
            f"<SchemaMetadata "
            f"{self.connection_id}>"
        )