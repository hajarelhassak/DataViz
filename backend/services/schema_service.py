"""
SchemaService

Responsable de l'analyse structurelle du schéma
d'une base cliente.

Ce service travaille uniquement sur :

- tables
- colonnes
- types
- relations

Aucune ligne de données métier n'est lue.
"""

from __future__ import annotations

from typing import Any


class SchemaService:
    """
    Service responsable de la normalisation
    et de l'analyse structurelle d'un schéma.
    """

    # ==========================================================
    # NORMALISATION
    # ==========================================================

    @staticmethod
    def normalize_schema(
        schema: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Normalise le schéma dans un format interne unique.
        """

        if not isinstance(schema, dict):
            return {
                "tables": []
            }

        tables = schema.get(
            "tables",
            []
        )

        if not isinstance(tables, list):
            return {
                "tables": []
            }

        normalized_tables = []

        for table in tables:

            if not isinstance(table, dict):
                continue

            table_name = (
                table.get("name")
                or table.get("nom")
                or table.get("table_name")
            )

            if not table_name:
                continue

            columns = (
                table.get("columns")
                or table.get("colonnes")
                or []
            )

            normalized_columns = []

            if isinstance(columns, list):

                for column in columns:

                    # --------------------------------------
                    # Format simple :
                    # ["id", "name", "price"]
                    # --------------------------------------

                    if isinstance(column, str):

                        column_name = column.strip()

                        if column_name:
                            normalized_columns.append({
                                "name": column_name,
                                "type": None,
                            })

                        continue

                    # --------------------------------------
                    # Format dictionnaire
                    # --------------------------------------

                    if not isinstance(column, dict):
                        continue

                    column_name = (
                        column.get("name")
                        or column.get("nom")
                        or column.get("column_name")
                    )

                    if not column_name:
                        continue

                    column_type = (
                        column.get("type")
                        or column.get("data_type")
                    )

                    normalized_columns.append({
                        "name": str(column_name).strip(),
                        "type": (
                            str(column_type).strip()
                            if column_type
                            else None
                        ),
                    })

            normalized_tables.append({
                "name": str(table_name).strip(),
                "columns": normalized_columns,
            })

        return {
            "tables": normalized_tables
        }

    # ==========================================================
    # EXTRACTION TABLES
    # ==========================================================

    @staticmethod
    def extract_tables(
        schema: dict[str, Any] | None,
    ) -> list[str]:
        """
        Retourne les noms des tables.
        """

        normalized = (
            SchemaService.normalize_schema(schema)
        )

        return [
            table["name"]
            for table in normalized["tables"]
        ]

    # ==========================================================
    # RELATIONS
    # ==========================================================

    @staticmethod
    def detect_relationships(
        schema: dict[str, Any] | None,
    ) -> list[dict[str, str]]:
        """
        Détecte des relations potentielles
        à partir des conventions de nommage.

        Exemple :

            customers.id
            sales.customer_id

        devient :

            sales.customer_id -> customers.id
        """

        normalized = (
            SchemaService.normalize_schema(schema)
        )

        tables = normalized["tables"]

        relationships = []

        # ------------------------------------------------------
        # INDEX TABLES
        # ------------------------------------------------------

        table_names = {
            table["name"].lower(): table["name"]
            for table in tables
        }

        # ------------------------------------------------------
        # RECHERCHE *_id
        # ------------------------------------------------------

        for table in tables:

            source_table = table["name"]

            for column in table["columns"]:

                column_name = column["name"]

                lower_column = (
                    column_name.lower()
                )

                if not lower_column.endswith("_id"):
                    continue

                target_base = lower_column[:-3]

                possible_targets = [
                    target_base,
                    f"{target_base}s",
                ]

                target_table = None

                for candidate in possible_targets:

                    if candidate in table_names:
                        target_table = (
                            table_names[candidate]
                        )
                        break

                if not target_table:
                    continue

                if (
                    target_table.lower()
                    == source_table.lower()
                ):
                    continue

                relationships.append({
                    "source_table": source_table,
                    "source_column": column_name,
                    "target_table": target_table,
                    "target_column": "id",
                })

        return relationships

    # ==========================================================
    # CONTEXTE IA
    # ==========================================================

    @staticmethod
    def build_ai_schema_context(
        schema: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Construit le contexte structurel envoyé à l'IA.

        Aucune ligne de données métier n'est incluse.
        """

        normalized = (
            SchemaService.normalize_schema(schema)
        )

        relationships = (
            SchemaService.detect_relationships(
                normalized
            )
        )

        return {
            "structure": normalized,
            "relations": relationships,
        }