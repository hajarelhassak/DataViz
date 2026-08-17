"""
AIService — intelligence artificielle décisionnelle de DataViz.

Architecture :

BDD cliente
    ↓
SchemaService / ConnectionService
    ↓
AIService.recommend_kpis()
    ↓
Gemini API
    ↓
Plan analytique
    ↓
Validation anti-hallucination
    ↓
AnalyticsService
    ↓
Calculs réels locaux
    ↓
KPI persistants
    ↓
AIService.request_analysis()
    ↓
Gemini API
    ↓
Rapport décisionnel

IMPORTANT :
- aucune ligne brute de la BDD cliente n'est envoyée à Gemini ;
- seuls le schéma et/ou des agrégats autorisés sont envoyés ;
- les calculs KPI sont réalisés localement ;
- les réponses Gemini sont validées avant utilisation.
"""

from __future__ import annotations

import json
import time
from typing import Any

import requests
from flask import current_app

from app.extensions import db
from models.ai_report import AIReport
from models.kpi import KPI
from services.ai_prompt_service import AIPromptService


# ==========================================================
# EXCEPTION
# ==========================================================


class AIServiceError(Exception):
    """Erreur contrôlée du service IA."""

    pass


# ==========================================================
# SERVICE
# ==========================================================


class AIService:

    # ======================================================
    # CONFIGURATION GEMINI
    # ======================================================

    @staticmethod
    def _get_gemini_config() -> tuple[str, str, int, int]:

        api_key = str(
            current_app.config.get(
                "GEMINI_API_KEY",
                "",
            )
        ).strip()

        model = str(
            current_app.config.get(
                "GEMINI_MODEL",
                "gemini-3.6-flash",
            )
        ).strip()

        timeout = current_app.config.get(
            "AI_REQUEST_TIMEOUT_SECONDS",
            120,
        )

        max_retries = current_app.config.get(
            "AI_MAX_RETRIES",
            1,
        )

        try:
            timeout = int(timeout)
        except (TypeError, ValueError):
            timeout = 120

        if timeout <= 0:
            timeout = 120

        try:
            max_retries = int(max_retries)
        except (TypeError, ValueError):
            max_retries = 1

        if max_retries < 0:
            max_retries = 0

        if not api_key:
            raise AIServiceError(
                "GEMINI_API_KEY n'est pas configurée."
            )

        if not model:
            raise AIServiceError(
                "GEMINI_MODEL n'est pas configuré."
            )

        return (
            api_key,
            model,
            timeout,
            max_retries,
        )

    # ======================================================
    # APPEL GEMINI
    # ======================================================

    @staticmethod
    def _call_gemini(
        prompt: str,
        system_prompt: str = "",
        debug_label: str = "Gemini",
    ) -> dict:
        """
        Appelle l'API Gemini generateContent.

        Gemini reçoit :
            - un system instruction ;
            - un prompt utilisateur.

        La réponse attendue est obligatoirement du JSON.
        """

        (
            api_key,
            model,
            timeout,
            max_retries,
        ) = AIService._get_gemini_config()

        if not isinstance(prompt, str):
            prompt = str(prompt)

        if not isinstance(system_prompt, str):
            system_prompt = str(system_prompt)

        prompt = prompt.strip()
        system_prompt = system_prompt.strip()

        if not prompt:
            raise AIServiceError(
                "Le prompt Gemini est vide."
            )

        # --------------------------------------------------
        # ENDPOINT OFFICIEL
        # --------------------------------------------------

        endpoint = (
            "https://generativelanguage.googleapis.com"
            f"/v1beta/models/{model}:generateContent"
        )

        # --------------------------------------------------
        # PAYLOAD
        # --------------------------------------------------

        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": prompt,
                        }
                    ],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
            },
        }

        if system_prompt:

            payload["systemInstruction"] = {
                "parts": [
                    {
                        "text": system_prompt,
                    }
                ]
            }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }

        # --------------------------------------------------
        # LOGS
        # --------------------------------------------------

        current_app.logger.info(
            "[Gemini] =========================================="
        )

        current_app.logger.info(
            "[Gemini] %s",
            debug_label,
        )

        current_app.logger.info(
            "[Gemini] Modèle : %s",
            model,
        )

        current_app.logger.info(
            "[Gemini] Timeout : %s secondes",
            timeout,
        )

        current_app.logger.info(
            "[Gemini] Taille prompt : %s caractères",
            len(prompt),
        )

        # NE PAS LOGGER LA CLE API
        #
        # On peut logger l'endpoint car il ne contient pas
        # la clé secrète.

        current_app.logger.info(
            "[Gemini] Endpoint : %s",
            endpoint,
        )

        # --------------------------------------------------
        # APPEL AVEC RETRIES
        # --------------------------------------------------

        last_exception: Exception | None = None

        response = None

        for attempt in range(max_retries + 1):

            started_at = time.perf_counter()

            try:

                current_app.logger.info(
                    "[Gemini] Tentative %s/%s",
                    attempt + 1,
                    max_retries + 1,
                )

                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=timeout,
                )

                elapsed = (
                    time.perf_counter()
                    - started_at
                )

                current_app.logger.info(
                    "[Gemini] HTTP %s en %.2fs",
                    response.status_code,
                    elapsed,
                )

                # --------------------------------------------------
                # SUCCÈS
                # --------------------------------------------------

                if response.ok:
                    break

                # --------------------------------------------------
                # ERREUR HTTP
                # --------------------------------------------------

                try:
                    error_body = response.json()
                except ValueError:
                    error_body = response.text[:5000]

                current_app.logger.error(
                    "[Gemini] Erreur HTTP %s : %s",
                    response.status_code,
                    error_body,
                )

                retryable = (
                    response.status_code == 429
                    or response.status_code >= 500
                )

                if retryable and attempt < max_retries:

                    time.sleep(2)

                    continue

                raise AIServiceError(
                    "Gemini HTTP "
                    f"{response.status_code}: "
                    f"{error_body}"
                )

            except requests.exceptions.Timeout as exc:

                last_exception = exc

                current_app.logger.error(
                    "[Gemini] Timeout après %s secondes.",
                    timeout,
                )

                if attempt >= max_retries:

                    raise AIServiceError(
                        "Timeout lors de l'appel Gemini "
                        f"après {timeout} secondes."
                    ) from exc

                time.sleep(2)

            except requests.exceptions.ConnectionError as exc:

                last_exception = exc

                current_app.logger.error(
                    "[Gemini] Erreur de connexion : %s",
                    exc,
                )

                if attempt >= max_retries:

                    raise AIServiceError(
                        "Impossible de contacter Gemini. "
                        "Vérifiez votre connexion Internet."
                    ) from exc

                time.sleep(2)

            except requests.exceptions.RequestException as exc:

                raise AIServiceError(
                    f"Erreur réseau Gemini : {exc}"
                ) from exc

        if response is None or not response.ok:

            raise AIServiceError(
                "Impossible de contacter Gemini."
            ) from last_exception

        # --------------------------------------------------
        # PARSING HTTP
        # --------------------------------------------------

        try:

            data = response.json()

        except ValueError as exc:

            raise AIServiceError(
                "Gemini a retourné une réponse HTTP "
                "non JSON."
            ) from exc

        # --------------------------------------------------
        # LOG RESPONSE
        # --------------------------------------------------

        current_app.logger.info(
            "[Gemini] Réponse reçue."
        )

        current_app.logger.debug(
            "[Gemini] Réponse brute : %s",
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            )[:10000],
        )

        # --------------------------------------------------
        # CANDIDATES
        # --------------------------------------------------

        candidates = data.get(
            "candidates",
            [],
        )

        if not candidates:

            feedback = data.get(
                "promptFeedback"
            )

            current_app.logger.error(
                "[Gemini] Aucun candidate."
            )

            if feedback:

                current_app.logger.error(
                    "[Gemini] Prompt feedback : %s",
                    feedback,
                )

            raise AIServiceError(
                "Gemini n'a retourné aucun résultat."
            )

        candidate = candidates[0]

        if not isinstance(candidate, dict):

            raise AIServiceError(
                "Réponse Gemini invalide."
            )

        # --------------------------------------------------
        # CONTENT
        # --------------------------------------------------

        content = candidate.get(
            "content"
        )

        if not isinstance(content, dict):

            raise AIServiceError(
                "Réponse Gemini invalide : "
                "content absent."
            )

        parts = content.get(
            "parts",
            [],
        )

        if not isinstance(parts, list):

            raise AIServiceError(
                "Réponse Gemini invalide : "
                "parts absent."
            )

        text_parts = []

        for part in parts:

            if not isinstance(part, dict):
                continue

            text = part.get("text")

            if text is not None:

                text_parts.append(
                    str(text)
                )

        text = "\n".join(
            text_parts
        ).strip()

        if not text:

            raise AIServiceError(
                "Gemini a retourné une réponse vide."
            )

        # --------------------------------------------------
        # JSON
        # --------------------------------------------------

        try:

            result = json.loads(text)

        except json.JSONDecodeError as exc:

            current_app.logger.error(
                "[Gemini] JSON invalide : %s",
                text[:10000],
            )

            raise AIServiceError(
                "Gemini n'a pas retourné "
                "un JSON valide."
            ) from exc

        if not isinstance(result, dict):

            raise AIServiceError(
                "La réponse Gemini doit être "
                "un objet JSON."
            )

        # --------------------------------------------------
        # USAGE
        # --------------------------------------------------

        usage = data.get(
            "usageMetadata",
            {},
        )

        if isinstance(usage, dict):

            current_app.logger.info(
                "[Gemini] Tokens prompt : %s",
                usage.get(
                    "promptTokenCount"
                ),
            )

            current_app.logger.info(
                "[Gemini] Tokens réponse : %s",
                usage.get(
                    "candidatesTokenCount"
                ),
            )

            current_app.logger.info(
                "[Gemini] Tokens total : %s",
                usage.get(
                    "totalTokenCount"
                ),
            )

        current_app.logger.info(
            "[Gemini] JSON valide."
        )

        current_app.logger.info(
            "[Gemini] =========================================="
        )

        return result

    # ======================================================
    # TEST GEMINI
    # ======================================================

    @staticmethod
    def test_gemini() -> dict:

        started_at = time.perf_counter()

        try:

            result = AIService._call_gemini(
                prompt=(
                    "Réponds uniquement avec cet objet JSON : "
                    '{"message":"hello"}'
                ),
                system_prompt=(
                    "Tu es un service de test. "
                    "Retourne uniquement du JSON valide."
                ),
                debug_label="TEST GEMINI",
            )

            elapsed = (
                time.perf_counter()
                - started_at
            )

            return {
                "success": True,
                "response": result,
                "response_time_ms": int(
                    elapsed * 1000
                ),
            }

        except Exception as exc:

            elapsed = (
                time.perf_counter()
                - started_at
            )

            current_app.logger.exception(
                "[Gemini TEST] Échec."
            )

            return {
                "success": False,
                "error": str(exc),
                "response_time_ms": int(
                    elapsed * 1000
                ),
            }

    # ======================================================
    # INDEXATION DU SCHEMA
    # ======================================================

    @staticmethod
    def _index_schema(schema: dict) -> dict:

        if not isinstance(schema, dict):
            return {}

        tables = schema.get(
            "tables",
            [],
        )

        if isinstance(tables, dict):

            normalized_tables = []

            for name, info in tables.items():

                item = {
                    "name": name,
                }

                if isinstance(info, dict):
                    item.update(info)

                normalized_tables.append(
                    item
                )

            tables = normalized_tables

        if not isinstance(tables, list):
            return {}

        index = {}

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

            table_name = str(
                table_name
            ).strip()

            if not table_name:
                continue

            columns = {}

            raw_columns = (
                table.get("columns")
                or table.get("colonnes")
                or []
            )

            if isinstance(
                raw_columns,
                list,
            ):

                for column in raw_columns:

                    if isinstance(
                        column,
                        str,
                    ):

                        column_name = (
                            column.strip()
                        )

                        if column_name:

                            columns[
                                column_name.lower()
                            ] = {
                                "name": column_name,
                                "type": None,
                            }

                    elif isinstance(
                        column,
                        dict,
                    ):

                        column_name = (
                            column.get("name")
                            or column.get("nom")
                            or column.get("column_name")
                        )

                        if not column_name:
                            continue

                        column_name = str(
                            column_name
                        ).strip()

                        if not column_name:
                            continue

                        columns[
                            column_name.lower()
                        ] = {
                            "name": column_name,
                            "type": column.get("type"),
                            "primary_key": bool(
                                column.get(
                                    "primary_key",
                                    False,
                                )
                            ),
                            "nullable": bool(
                                column.get(
                                    "nullable",
                                    True,
                                )
                            ),
                        }

            elif isinstance(
                raw_columns,
                dict,
            ):

                for column_name, info in raw_columns.items():

                    column_name = str(
                        column_name
                    ).strip()

                    if not column_name:
                        continue

                    if isinstance(
                        info,
                        dict,
                    ):

                        column_type = info.get(
                            "type"
                        )

                        primary_key = bool(
                            info.get(
                                "primary_key",
                                False,
                            )
                        )

                        nullable = bool(
                            info.get(
                                "nullable",
                                True,
                            )
                        )

                    else:

                        column_type = info
                        primary_key = False
                        nullable = True

                    columns[
                        column_name.lower()
                    ] = {
                        "name": column_name,
                        "type": column_type,
                        "primary_key": primary_key,
                        "nullable": nullable,
                    }

            index[
                table_name.lower()
            ] = {
                "name": table_name,
                "columns": columns,
                "foreign_keys": (
                    table.get("foreign_keys")
                    or table.get("foreignKeys")
                    or []
                ),
            }

        return index

    # ======================================================
    # VERIFICATION COLONNE
    # ======================================================

    @staticmethod
    def _column_exists(
        schema_index: dict,
        table: str,
        column: str,
    ) -> bool:

        if not table or not column:
            return False

        table_key = str(
            table
        ).strip().lower()

        column_key = str(
            column
        ).strip().lower()

        table_info = schema_index.get(
            table_key
        )

        if not table_info:
            return False

        return column_key in table_info.get(
            "columns",
            {},
        )

    # ======================================================
    # VALIDATION KPI
    # ======================================================

    @staticmethod
    def _filter_kpis_against_schema(
        schema: dict,
        kpis: list,
    ) -> list:

        schema_index = (
            AIService._index_schema(
                schema
            )
        )

        if not schema_index:
            return []

        allowed = set(
            AIPromptService.ALLOWED_OPERATIONS
        )

        if not isinstance(
            kpis,
            list,
        ):
            return []

        valid = []

        for item in kpis:

            if not isinstance(
                item,
                dict,
            ):
                continue

            table = item.get(
                "table"
            )

            column = item.get(
                "column"
            )

            operation = str(
                item.get(
                    "operation",
                    "",
                )
            ).strip().lower()

            if not table:
                continue

            if operation not in allowed:
                continue

            # --------------------------------------------------
            # COUNT(*)
            # --------------------------------------------------

            if (
                operation == "count"
                and str(column).strip() == "*"
            ):

                table_key = str(
                    table
                ).strip().lower()

                if table_key not in schema_index:
                    continue

                normalized = dict(
                    item
                )

                normalized["table"] = (
                    schema_index[
                        table_key
                    ]["name"]
                )

                normalized["column"] = "*"

                normalized["operation"] = (
                    operation
                )

                normalized.setdefault(
                    "id",
                    (
                        f"{table_key}_"
                        f"count"
                    ),
                )

                valid.append(
                    normalized
                )

                continue

            if not column:
                continue

            table_key = str(
                table
            ).strip().lower()

            if table_key not in schema_index:
                continue

            if not AIService._column_exists(
                schema_index,
                table,
                column,
            ):
                continue

            normalized = dict(
                item
            )

            normalized["table"] = (
                schema_index[
                    table_key
                ]["name"]
            )

            normalized["column"] = str(
                column
            ).strip()

            normalized["operation"] = (
                operation
            )

            normalized.setdefault(
                "id",
                (
                    f"{table_key}_"
                    f"{str(column).strip().lower()}_"
                    f"{operation}"
                ),
            )

            valid.append(
                normalized
            )

        return valid

    # ======================================================
    # VALIDATION GRAPHIQUES
    # ======================================================

    @staticmethod
    def _filter_charts_against_schema(
        schema: dict,
        charts: list,
    ) -> list:

        schema_index = (
            AIService._index_schema(
                schema
            )
        )

        if not schema_index:
            return []

        if not isinstance(
            charts,
            list,
        ):
            return []

        allowed_types = set(
            AIPromptService.ALLOWED_CHART_TYPES
        )

        allowed_operations = set(
            AIPromptService.ALLOWED_OPERATIONS
        )

        valid = []

        for chart in charts:

            if not isinstance(
                chart,
                dict,
            ):
                continue

            chart_type = str(
                chart.get(
                    "type",
                    "",
                )
            ).strip().lower()

            table = chart.get(
                "table"
            )

            if chart_type not in allowed_types:
                continue

            if not isinstance(
                table,
                str,
            ):
                continue

            table_key = table.strip().lower()

            if table_key not in schema_index:
                continue

            dimension = chart.get(
                "dimension"
            )

            value = chart.get(
                "value"
            )

            if dimension and not AIService._column_exists(
                schema_index,
                table,
                dimension,
            ):
                continue

            if value and not AIService._column_exists(
                schema_index,
                table,
                value,
            ):
                continue

            operation = str(
                chart.get(
                    "operation",
                    "",
                )
            ).strip().lower()

            if (
                operation
                and operation not in allowed_operations
            ):
                continue

            date_column = chart.get(
                "date_column"
            )

            if (
                date_column
                and not AIService._column_exists(
                    schema_index,
                    table,
                    date_column,
                )
            ):
                continue

            normalized = dict(
                chart
            )

            normalized["type"] = (
                chart_type
            )

            normalized["table"] = (
                schema_index[
                    table_key
                ]["name"]
            )

            if dimension:
                normalized["dimension"] = str(
                    dimension
                ).strip()

            if value:
                normalized["value"] = str(
                    value
                ).strip()

            if operation:
                normalized["operation"] = (
                    operation
                )

            if date_column:
                normalized["date_column"] = str(
                    date_column
                ).strip()

            valid.append(
                normalized
            )

        return valid

    # ======================================================
    # VALIDATION FILTRES
    # ======================================================

    @staticmethod
    def _filter_filters_against_schema(
        schema: dict,
        filters: list,
    ) -> list:

        schema_index = (
            AIService._index_schema(
                schema
            )
        )

        if not schema_index:
            return []

        if not isinstance(
            filters,
            list,
        ):
            return []

        allowed_types = set(
            AIPromptService.ALLOWED_FILTER_TYPES
        )

        valid = []

        for item in filters:

            if not isinstance(
                item,
                dict,
            ):
                continue

            table = item.get(
                "table"
            )

            column = item.get(
                "column"
            )

            filter_type = str(
                item.get(
                    "type",
                    "",
                )
            ).strip().lower()

            if not table or not column:
                continue

            if filter_type not in allowed_types:
                continue

            if not AIService._column_exists(
                schema_index,
                table,
                column,
            ):
                continue

            table_key = str(
                table
            ).strip().lower()

            normalized = dict(
                item
            )

            normalized["table"] = (
                schema_index[
                    table_key
                ]["name"]
            )

            normalized["column"] = str(
                column
            ).strip()

            normalized["type"] = (
                filter_type
            )

            valid.append(
                normalized
            )

        return valid

    # ======================================================
    # RECOMMANDATION KPI
    # ======================================================

    @staticmethod
    def recommend_kpis(
        schema: dict,
        connection_id: str | None = None,
    ) -> dict:

        if not isinstance(
            schema,
            dict,
        ) or not schema:

            raise ValueError(
                "Le schéma est vide."
            )

        current_app.logger.info(
            "[AIService] Analyse du schéma avec Gemini."
        )

        prompt = (
            AIPromptService
            .build_schema_analysis_prompt(
                schema
            )
        )

        try:

            result = AIService._call_gemini(
                prompt=prompt,
                system_prompt=(
                    AIPromptService
                    .SYSTEM_PROMPT_SCHEMA
                ),
                debug_label=(
                    "ANALYSE SCHEMA + KPI"
                ),
            )

            result.setdefault(
                "domaine_detecte",
                "Inconnu",
            )

            result.setdefault(
                "description_metier",
                "",
            )

            result.setdefault(
                "tables_metier",
                [],
            )

            result.setdefault(
                "kpi_recommandes",
                [],
            )

            result.setdefault(
                "graphiques_recommandes",
                [],
            )

            result.setdefault(
                "filtres_recommandes",
                [],
            )

            result.setdefault(
                "alertes_possibles",
                [],
            )

            result.setdefault(
                "questions_metier",
                [],
            )

            # --------------------------------------------------
            # VALIDATION KPI
            # --------------------------------------------------

            result["kpi_recommandes"] = (
                AIService
                ._filter_kpis_against_schema(
                    schema,
                    result["kpi_recommandes"],
                )
            )

            # --------------------------------------------------
            # VALIDATION GRAPHIQUES
            # --------------------------------------------------

            charts_input = (
                result.get(
                    "graphiques_recommandees"
                )
                or result.get(
                    "graphiques_recommandes",
                    [],
                )
            )

            result["graphiques_recommandes"] = (
                AIService
                ._filter_charts_against_schema(
                    schema,
                    charts_input,
                )
            )

            # --------------------------------------------------
            # VALIDATION FILTRES
            # --------------------------------------------------

            result["filtres_recommandes"] = (
                AIService
                ._filter_filters_against_schema(
                    schema,
                    result["filtres_recommandes"],
                )
            )

            result["connection_id"] = (
                connection_id
            )

            result["statut"] = "success"

            return result

        except Exception as exc:

            current_app.logger.exception(
                "[AIService] Erreur analyse schéma."
            )

            return {
                "statut": "degraded",
                "connection_id": connection_id,
                "erreur": str(exc),
                "domaine_detecte": None,
                "description_metier": "",
                "tables_metier": [],
                "kpi_recommandes": [],
                "graphiques_recommandes": [],
                "filtres_recommandes": [],
                "alertes_possibles": [],
                "questions_metier": [],
            }

    # ======================================================
    # ALIAS
    # ======================================================

    @staticmethod
    def recommend_kpis_from_schema(
        schema_info: dict,
    ) -> dict:

        return AIService.recommend_kpis(
            schema=schema_info
        )

    # ======================================================
    # CONTEXTE FINAL
    # ======================================================

    @staticmethod
    def build_context(
        project_nom: str,
        kpis: list[KPI],
        schema_info: dict | None = None,
        data_profile: dict | None = None,
        anomalies: list[dict] | None = None,
    ) -> dict:

        if not isinstance(
            kpis,
            list,
        ):
            kpis = []

        return {
            "projet": project_nom,

            # IMPORTANT :
            # schema_info doit être structurel uniquement.
            "schema": schema_info or {},

            # IMPORTANT :
            # data_profile doit contenir uniquement
            # des agrégats/statistiques autorisés.
            "profil": data_profile or {},

            "kpis": [
                {
                    "id": k.id,
                    "nom": k.nom,
                    "formule": k.formule,
                    "operation": k.operation,
                    "valeur": k.valeur,
                    "unite": k.unite,
                    "table": getattr(
                        k,
                        "table_name",
                        None,
                    ),
                    "colonne": getattr(
                        k,
                        "column_name",
                        None,
                    ),
                }
                for k in kpis
            ],

            "anomalies": anomalies or [],
        }

    # ======================================================
    # ANALYSE FINALE
    # ======================================================

    @staticmethod
    def request_analysis(
        project_id: str,
        project_nom: str,
        kpis: list[KPI],
        dashboard_id: str | None = None,
        schema_info: dict | None = None,
        data_profile: dict | None = None,
        anomalies: list[dict] | None = None,
    ) -> AIReport:

        context = AIService.build_context(
            project_nom=project_nom,
            kpis=kpis,
            schema_info=schema_info,
            data_profile=data_profile,
            anomalies=anomalies,
        )

        report = AIReport(
            project_id=project_id,
            dashboard_id=dashboard_id,
            prompt_context_json=json.dumps(
                context,
                ensure_ascii=False,
            ),
            statut="degraded",
        )

        started_at = time.perf_counter()

        try:

            current_app.logger.info(
                "[AIService] Analyse décisionnelle "
                "du projet %s.",
                project_nom,
            )

            prompt = (
                AIPromptService
                .build_dashboard_explanation_prompt(
                    context
                )
            )

            result = AIService._call_gemini(
                prompt=prompt,
                system_prompt=(
                    AIPromptService
                    .SYSTEM_PROMPT_ANALYSIS
                ),
                debug_label=(
                    "ANALYSE DECISIONNELLE"
                ),
            )

            result.setdefault(
                "resume",
                "",
            )

            result.setdefault(
                "tendances",
                [],
            )

            result.setdefault(
                "alertes",
                [],
            )

            result.setdefault(
                "actions_conseillees",
                [],
            )

            report.statut = "success"

            report.resultat_json = json.dumps(
                result,
                ensure_ascii=False,
            )

            report.erreur_message = None

        except Exception as exc:

            current_app.logger.exception(
                "[AIService] Erreur analyse "
                "décisionnelle Gemini."
            )

            report.statut = "degraded"

            report.erreur_message = str(
                exc
            )

            report.resultat_json = json.dumps(
                {
                    "resume": "",
                    "tendances": [],
                    "alertes": [],
                    "actions_conseillees": [],
                },
                ensure_ascii=False,
            )

        # --------------------------------------------------
        # PERFORMANCE
        # --------------------------------------------------

        elapsed = (
            time.perf_counter()
            - started_at
        )

        report.response_time_ms = int(
            elapsed * 1000
        )

        report.model_version = str(
            current_app.config.get(
                "GEMINI_MODEL",
                "gemini-3.6-flash",
            )
        )

        # --------------------------------------------------
        # PERSISTENCE
        # --------------------------------------------------

        try:

            db.session.add(
                report
            )

            db.session.commit()

        except Exception:

            db.session.rollback()

            current_app.logger.exception(
                "[AIService] Impossible de "
                "sauvegarder le rapport IA."
            )

            raise

        return report

    # ======================================================
    # ANALYSE DASHBOARD
    # ======================================================

    @staticmethod
    def analyze_dashboard(
        dashboard_id: str,
        project_id: str,
        project_name: str,
    ) -> dict:

        current_app.logger.info(
            "[AIService] Recherche KPI "
            "dashboard=%s",
            dashboard_id,
        )

        kpis = (
            KPI.query
            .filter_by(
                dashboard_id=dashboard_id
            )
            .all()
        )

        current_app.logger.info(
            "[AIService] %s KPI trouvés.",
            len(kpis),
        )

        report = AIService.request_analysis(
            project_id=project_id,
            project_nom=project_name,
            kpis=kpis,
            dashboard_id=dashboard_id,
        )

        return report.to_dict()

    # ======================================================
    # STATUS GEMINI
    # ======================================================

    @staticmethod
    def check_status() -> dict:

        try:

            (
                _api_key,
                model,
                _timeout,
                _max_retries,
            ) = AIService._get_gemini_config()

            result = AIService.test_gemini()

            if result.get("success"):

                return {
                    "available": True,
                    "configured": True,
                    "model": model,
                    "message": (
                        "Gemini est opérationnel."
                    ),
                    "response_time_ms": (
                        result.get(
                            "response_time_ms"
                        )
                    ),
                }

            return {
                "available": False,
                "configured": True,
                "model": model,
                "message": result.get(
                    "error",
                    "Gemini indisponible.",
                ),
            }

        except AIServiceError as exc:

            return {
                "available": False,
                "configured": False,
                "model": None,
                "message": str(exc),
            }

        except Exception as exc:

            current_app.logger.exception(
                "[AIService] Erreur check_status."
            )

            return {
                "available": False,
                "configured": False,
                "model": None,
                "message": str(exc),
            }