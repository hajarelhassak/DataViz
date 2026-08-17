"""
AIKPISelectorService — sélection intelligente des KPI.

Architecture :

BDD cliente
    ↓
SchemaService
    ↓
AIKPISelectorService
    ↓
Google Gemini API
    ↓
Plan analytique JSON
    ↓
AnalyticsService
    ↓
Calculs locaux réels

CONFIDENTIALITÉ
---------------
Aucune donnée brute cliente n'est envoyée à Gemini.

Gemini reçoit uniquement :
    - noms des tables
    - noms des colonnes
    - types des colonnes

Gemini ne reçoit jamais :
    - lignes de données
    - DataFrame
    - valeurs métier
    - résultats SQL
"""

from __future__ import annotations

import json
import logging
from typing import Any

import requests
from flask import current_app


logger = logging.getLogger(__name__)


class AIKPISelectorError(Exception):
    """Erreur du service de sélection des KPI."""

    pass


# ==============================================================
# PROMPT SYSTÈME
# ==============================================================

SYSTEM_PROMPT = """
Tu es le moteur d'intelligence artificielle décisionnelle de DataViz.

Tu es spécialisé en :

- Business Intelligence
- Data Analytics
- KPI
- Data Visualization
- analyse de schémas relationnels

IMPORTANT :

Tu analyses UNIQUEMENT le SCHÉMA d'une base de données.

Tu ne reçois aucune ligne de données.

Le schéma contient uniquement :

- les noms des tables
- les noms des colonnes
- les types des colonnes

Tu dois :

1. Identifier le domaine métier probable.
2. Identifier les tables pertinentes.
3. Identifier les colonnes pertinentes.
4. Proposer les KPI les plus utiles.
5. Déterminer l'opération nécessaire pour chaque KPI.
6. Proposer les graphiques adaptés.

RÈGLES ABSOLUES :

- Ne jamais inventer une table.
- Ne jamais inventer une colonne.
- Ne jamais inventer une valeur.
- Utiliser uniquement les tables et colonnes présentes dans le schéma.
- Ne jamais demander les lignes de données.
- Ne jamais demander un DataFrame.
- Ne jamais calculer toi-même une valeur réelle.
- Les calculs réels seront effectués localement par AnalyticsService.
- Si aucun KPI pertinent ne peut être déterminé, retourner une liste vide.
- Retourner uniquement un JSON valide.
- Aucun Markdown.
- Aucun texte avant ou après le JSON.

FORMAT OBLIGATOIRE :

{
    "domaine_detecte": "",
    "kpi_recommandes": [
        {
            "nom": "",
            "table": "",
            "column": "",
            "operation": "",
            "description": ""
        }
    ],
    "graphiques_recommandes": []
}

OPERATIONS AUTORISÉES :

- count
- sum
- avg
- min
- max
- count_distinct

Le champ "column" doit obligatoirement correspondre
à une colonne existante dans la table indiquée.

Pour un COUNT général d'une table, utiliser "*" uniquement
si nécessaire.

Les graphiques peuvent utiliser :

- bar
- line
- pie
- area
- scatter
- heatmap
- table
"""


# ==============================================================
# SERVICE
# ==============================================================

class AIKPISelectorService:

    # ==========================================================
    # CONSTRUCTION DU PROMPT
    # ==========================================================

    @staticmethod
    def build_prompt(schema_info: dict) -> str:
        """
        Construit le prompt utilisateur à partir du schéma.

        IMPORTANT :
        schema_info doit contenir uniquement des informations
        structurelles sur la base.
        """

        sanitized_schema = AIKPISelectorService._sanitize_schema(
            schema_info
        )

        return f"""
Voici le schéma de la base de données cliente.

IMPORTANT :
Aucune ligne de données n'est fournie.

Tu dois analyser uniquement la structure.

SCHÉMA :

{json.dumps(
    sanitized_schema,
    ensure_ascii=False,
    indent=2
)}

Analyse cette structure et retourne uniquement le JSON
correspondant au format demandé.
"""

    # ==========================================================
    # NETTOYAGE DU SCHÉMA
    # ==========================================================

    @staticmethod
    def _sanitize_schema(schema_info: dict) -> dict:
        """
        Garantit qu'on ne transmet que la structure du schéma.

        Cette étape constitue une sécurité supplémentaire :
        même si schema_info contient accidentellement d'autres
        informations, elles ne doivent pas être envoyées à l'IA.
        """

        if not isinstance(schema_info, dict):
            return {}

        sanitized = {}

        # Cas classique :
        #
        # {
        #     "tables": {
        #         "users": {
        #             "columns": {
        #                 "id": "INTEGER",
        #                 "name": "VARCHAR"
        #             }
        #         }
        #     }
        # }

        tables = schema_info.get("tables")

        if isinstance(tables, dict):

            sanitized_tables = {}

            for table_name, table_info in tables.items():

                if not isinstance(table_info, dict):
                    continue

                columns = table_info.get("columns", {})

                if isinstance(columns, dict):

                    sanitized_tables[str(table_name)] = {
                        "columns": {
                            str(column_name): str(column_type)
                            for column_name, column_type
                            in columns.items()
                        }
                    }

                elif isinstance(columns, list):

                    sanitized_tables[str(table_name)] = {
                        "columns": [
                            str(column)
                            for column in columns
                        ]
                    }

            sanitized["tables"] = sanitized_tables

        else:

            # Compatibilité avec certains formats de SchemaService.
            #
            # Exemple :
            #
            # {
            #     "users": {
            #         "id": "INTEGER",
            #         "email": "VARCHAR"
            #     }
            # }

            for table_name, table_info in schema_info.items():

                if not isinstance(table_info, dict):
                    continue

                columns = table_info.get("columns")

                if isinstance(columns, dict):

                    sanitized[str(table_name)] = {
                        "columns": {
                            str(column_name): str(column_type)
                            for column_name, column_type
                            in columns.items()
                        }
                    }

        return sanitized

    # ==========================================================
    # URL GEMINI
    # ==========================================================

    @staticmethod
    def _get_gemini_url() -> str:
        """
        Construit l'URL officielle Gemini.

        GEMINI_API_KEY = clé secrète
        GEMINI_MODEL   = nom du modèle
        """

        api_key = current_app.config.get("GEMINI_API_KEY")

        if not api_key:
            raise AIKPISelectorError(
                "GEMINI_API_KEY n'est pas configurée."
            )

        model = current_app.config.get(
            "GEMINI_MODEL",
            "gemini-3.6-flash"
        )

        return (
            "https://generativelanguage.googleapis.com/"
            f"v1beta/models/{model}:generateContent"
            f"?key={api_key}"
        )

    # ==========================================================
    # APPEL GEMINI
    # ==========================================================

    @staticmethod
    def call_ai(prompt: str) -> dict:
        """
        Appelle Google Gemini et retourne le JSON produit.
        """

        url = AIKPISelectorService._get_gemini_url()

        timeout = current_app.config.get(
            "AI_REQUEST_TIMEOUT_SECONDS",
            120
        )

        payload = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": SYSTEM_PROMPT
                    }
                ]
            },

            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],

            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        try:

            response = requests.post(
                url,
                json=payload,
                timeout=timeout
            )

        except requests.exceptions.Timeout as exc:

            raise AIKPISelectorError(
                "Timeout lors de l'appel à Gemini."
            ) from exc

        except requests.exceptions.ConnectionError as exc:

            raise AIKPISelectorError(
                "Impossible de contacter l'API Gemini."
            ) from exc

        except requests.exceptions.RequestException as exc:

            raise AIKPISelectorError(
                f"Erreur réseau Gemini : {exc}"
            ) from exc

        # ------------------------------------------------------
        # ERREURS HTTP
        # ------------------------------------------------------

        if not response.ok:

            try:
                error_data = response.json()
            except ValueError:
                error_data = response.text

            logger.error(
                "Erreur Gemini HTTP %s : %s",
                response.status_code,
                error_data
            )

            raise AIKPISelectorError(
                f"Gemini HTTP {response.status_code} : "
                f"{error_data}"
            )

        # ------------------------------------------------------
        # PARSING RÉPONSE
        # ------------------------------------------------------

        try:

            data = response.json()

        except ValueError as exc:

            raise AIKPISelectorError(
                "Gemini a retourné une réponse non JSON."
            ) from exc

        # ------------------------------------------------------
        # EXTRACTION DU TEXTE
        # ------------------------------------------------------

        try:

            candidates = data["candidates"]

            if not candidates:
                raise AIKPISelectorError(
                    "Gemini n'a retourné aucun candidat."
                )

            content = candidates[0]["content"]

            parts = content["parts"]

            if not parts:
                raise AIKPISelectorError(
                    "Gemini n'a retourné aucun contenu."
                )

            text = parts[0]["text"]

        except (
            KeyError,
            TypeError,
            IndexError
        ) as exc:

            logger.error(
                "Réponse Gemini inattendue : %s",
                data
            )

            raise AIKPISelectorError(
                f"Réponse Gemini invalide : {data}"
            ) from exc

        # ------------------------------------------------------
        # JSON
        # ------------------------------------------------------

        try:

            result = json.loads(text)

        except json.JSONDecodeError as exc:

            logger.error(
                "Gemini a retourné : %s",
                text
            )

            raise AIKPISelectorError(
                "Gemini n'a pas retourné un JSON valide."
            ) from exc

        if not isinstance(result, dict):

            raise AIKPISelectorError(
                "Le résultat Gemini doit être un objet JSON."
            )

        return result

    # ==========================================================
    # VALIDATION DU PLAN KPI
    # ==========================================================

    @staticmethod
    def validate_result(
        result: dict,
        schema_info: dict
    ) -> dict:
        """
        Vérifie que Gemini n'a pas inventé de tables ou colonnes.
        """

        if not isinstance(result, dict):

            raise AIKPISelectorError(
                "Le résultat IA n'est pas un objet JSON."
            )

        domaine = result.get(
            "domaine_detecte",
            ""
        )

        kpis = result.get(
            "kpi_recommandes",
            []
        )

        graphiques = result.get(
            "graphiques_recommandes",
            []
        )

        if not isinstance(kpis, list):
            kpis = []

        if not isinstance(graphiques, list):
            graphiques = []

        sanitized_schema = (
            AIKPISelectorService._sanitize_schema(
                schema_info
            )
        )

        # ------------------------------------------------------
        # EXTRACTION DES TABLES / COLONNES AUTORISÉES
        # ------------------------------------------------------

        allowed_tables = {}

        tables = sanitized_schema.get(
            "tables",
            {}
        )

        if isinstance(tables, dict):

            for table_name, table_info in tables.items():

                columns = set()

                if isinstance(table_info, dict):

                    raw_columns = table_info.get(
                        "columns",
                        {}
                    )

                    if isinstance(raw_columns, dict):

                        columns = {
                            str(column)
                            for column in raw_columns.keys()
                        }

                    elif isinstance(raw_columns, list):

                        columns = {
                            str(column)
                            for column in raw_columns
                        }

                allowed_tables[str(table_name)] = columns

        # ------------------------------------------------------
        # VALIDATION DES KPI
        # ------------------------------------------------------

        validated_kpis = []

        allowed_operations = {
            "count",
            "sum",
            "avg",
            "min",
            "max",
            "count_distinct"
        }

        for kpi in kpis:

            if not isinstance(kpi, dict):
                continue

            table = str(
                kpi.get("table", "")
            ).strip()

            column = str(
                kpi.get("column", "")
            ).strip()

            operation = str(
                kpi.get("operation", "")
            ).strip().lower()

            name = str(
                kpi.get("nom", "")
            ).strip()

            description = str(
                kpi.get("description", "")
            ).strip()

            # Table inexistante
            if table not in allowed_tables:
                logger.warning(
                    "KPI rejeté : table inexistante : %s",
                    table
                )
                continue

            # COUNT sur *
            if (
                operation == "count"
                and column == "*"
            ):
                column_valid = True
            else:
                column_valid = (
                    column in allowed_tables[table]
                )

            if not column_valid:

                logger.warning(
                    "KPI rejeté : colonne inexistante : %s.%s",
                    table,
                    column
                )

                continue

            if operation not in allowed_operations:

                logger.warning(
                    "KPI rejeté : opération interdite : %s",
                    operation
                )

                continue

            if not name:
                continue

            validated_kpis.append(
                {
                    "nom": name,
                    "table": table,
                    "column": column,
                    "operation": operation,
                    "description": description
                }
            )

        # ------------------------------------------------------
        # GRAPHIQUES
        # ------------------------------------------------------

        allowed_charts = {
            "bar",
            "line",
            "pie",
            "area",
            "scatter",
            "heatmap",
            "table"
        }

        validated_charts = []

        for chart in graphiques:

            if isinstance(chart, str):

                chart_type = chart.lower().strip()

                if chart_type in allowed_charts:
                    validated_charts.append(
                        chart_type
                    )

            elif isinstance(chart, dict):

                chart_type = str(
                    chart.get("type", "")
                ).lower().strip()

                if chart_type in allowed_charts:
                    validated_charts.append(
                        chart
                    )

        return {
            "domaine_detecte": str(domaine).strip(),
            "kpi_recommandes": validated_kpis,
            "graphiques_recommandes": validated_charts
        }

    # ==========================================================
    # SÉLECTION DES KPI
    # ==========================================================

    @staticmethod
    def select_kpis(
        schema_info: dict
    ) -> dict:

        empty_result = {
            "domaine_detecte": "",
            "kpi_recommandes": [],
            "graphiques_recommandes": []
        }

        if not schema_info:

            return {
                "success": False,
                "error": "Le schéma est vide.",
                "result": empty_result
            }

        try:

            # --------------------------------------------------
            # 1. Nettoyage
            # --------------------------------------------------

            sanitized_schema = (
                AIKPISelectorService._sanitize_schema(
                    schema_info
                )
            )

            if not sanitized_schema:

                return {
                    "success": False,
                    "error": (
                        "Impossible d'extraire les tables "
                        "et colonnes du schéma."
                    ),
                    "result": empty_result
                }

            # --------------------------------------------------
            # 2. Prompt
            # --------------------------------------------------

            prompt = (
                AIKPISelectorService.build_prompt(
                    sanitized_schema
                )
            )

            # --------------------------------------------------
            # 3. Gemini
            # --------------------------------------------------

            raw_result = (
                AIKPISelectorService.call_ai(
                    prompt
                )
            )

            # --------------------------------------------------
            # 4. Validation anti-hallucination
            # --------------------------------------------------

            validated_result = (
                AIKPISelectorService.validate_result(
                    raw_result,
                    sanitized_schema
                )
            )

            return {
                "success": True,
                "result": validated_result
            }

        except AIKPISelectorError as exc:

            logger.error(
                "AIKPISelectorError : %s",
                exc
            )

            return {
                "success": False,
                "error": str(exc),
                "result": empty_result
            }

        except Exception as exc:

            logger.exception(
                "Erreur inattendue AIKPISelectorService"
            )

            return {
                "success": False,
                "error": (
                    "Erreur interne lors de la sélection "
                    "des KPI."
                ),
                "result": empty_result
            }