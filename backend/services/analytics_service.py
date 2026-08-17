"""
AnalyticsService — calcul analytique local.

Responsabilités :

- calculer les KPI ;
- profiler les données ;
- détecter les anomalies ;
- persister les KPI.

IMPORTANT :

Aucun calcul n'est réalisé par Mistral.
Les données restent localement dans DataViz.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.extensions import db
from models.kpi import KPI


class CalculationService:

    NUMERIC_OPERATIONS = {
        "sum",
        "average",
        "mean",
        "median",
        "min",
        "max",
        "std",
        "variance",
        "quartile25",
        "quartile50",
        "quartile75",
    }

    GENERAL_OPERATIONS = {
        "count",
        "distinct_count",
        "mode",
    }

    DATE_OPERATIONS = {
        "date_min",
        "date_max",
        "date_range_days",
    }

    # ======================================================
    # EXECUTE
    # ======================================================

    @staticmethod
    def execute(
        series: pd.Series,
        operation: str,
    ) -> Any:

        if series is None:
            return None

        operation = str(
            operation or ""
        ).lower().strip()

        if not operation:
            return None

        clean = series.dropna()

        # --------------------------------------------------
        # COUNT
        # --------------------------------------------------

        if operation == "count":
            return int(clean.count())

        # --------------------------------------------------
        # DISTINCT
        # --------------------------------------------------

        if operation == "distinct_count":
            return int(clean.nunique())

        # --------------------------------------------------
        # MODE
        # --------------------------------------------------

        if operation == "mode":

            modes = clean.mode()

            if modes.empty:
                return None

            return modes.iloc[0]

        # --------------------------------------------------
        # DATES
        # --------------------------------------------------

        if operation in CalculationService.DATE_OPERATIONS:

            dates = pd.to_datetime(
                clean,
                errors="coerce",
            ).dropna()

            if dates.empty:
                return None

            if operation == "date_min":
                return str(dates.min())

            if operation == "date_max":
                return str(dates.max())

            if operation == "date_range_days":
                return int(
                    (
                        dates.max()
                        - dates.min()
                    ).days
                )

        # --------------------------------------------------
        # NUMERIQUE
        # --------------------------------------------------

        if operation in CalculationService.NUMERIC_OPERATIONS:

            numeric = pd.to_numeric(
                clean,
                errors="coerce",
            ).dropna()

            if numeric.empty:
                return None

            if operation == "sum":
                return float(numeric.sum())

            if operation in {
                "average",
                "mean",
            }:
                return float(numeric.mean())

            if operation in {
                "median",
                "quartile50",
            }:
                return float(numeric.median())

            if operation == "min":
                return float(numeric.min())

            if operation == "max":
                return float(numeric.max())

            if operation == "std":

                value = numeric.std()

                return (
                    0.0
                    if pd.isna(value)
                    else float(value)
                )

            if operation == "variance":

                value = numeric.var()

                return (
                    0.0
                    if pd.isna(value)
                    else float(value)
                )

            if operation == "quartile25":
                return float(
                    numeric.quantile(0.25)
                )

            if operation == "quartile75":
                return float(
                    numeric.quantile(0.75)
                )

        return None


class AnalyticsService:

    ALLOWED_OPERATIONS = {
        "sum",
        "average",
        "mean",
        "median",
        "min",
        "max",
        "std",
        "variance",
        "quartile25",
        "quartile50",
        "quartile75",
        "count",
        "distinct_count",
        "mode",
        "date_min",
        "date_max",
        "date_range_days",
    }

    # ======================================================
    # EXECUTE PLAN SUR UNE TABLE
    # ======================================================

    @staticmethod
    def execute_kpi_plan(
        df: pd.DataFrame,
        table_name: str,
        kpi_plan: list[dict],
    ) -> list[dict]:

        results = []

        if df is None or df.empty:
            return results

        if not isinstance(kpi_plan, list):
            return results

        for request in kpi_plan:

            if not isinstance(request, dict):
                continue

            column = request.get("column")

            operation = str(
                request.get("operation", "")
            ).lower().strip()

            if not column:
                continue

            if column not in df.columns:
                continue

            if operation not in (
                AnalyticsService.ALLOWED_OPERATIONS
            ):
                continue

            value = CalculationService.execute(
                df[column],
                operation,
            )

            if value is None:
                continue

            results.append(
                {
                    "table_name": table_name,
                    "column_name": column,
                    "column_type": str(
                        df[column].dtype
                    ),
                    "nom": (
                        request.get("nom")
                        or request.get("name")
                        or f"{column}_{operation}"
                    ),
                    "formule": operation,
                    "valeur": AnalyticsService.clean_value(
                        value
                    ),
                }
            )

        return results

    # ======================================================
    # EXECUTE PLAN IA SUR PLUSIEURS TABLES
    # ======================================================

    @staticmethod
    def execute_ai_plan(
        dataframes: dict[str, pd.DataFrame],
        kpi_plan: list[dict],
    ) -> list[dict]:
        """
        Exécute le plan KPI généré par Mistral.

        dataframes :

        {
            "products": dataframe_products,
            "sales": dataframe_sales
        }

        kpi_plan :

        [
            {
                "nom": "Chiffre d'affaires",
                "table": "sales",
                "column": "total",
                "operation": "sum"
            }
        ]
        """

        if not isinstance(dataframes, dict):
            return []

        if not isinstance(kpi_plan, list):
            return []

        results = []

        for kpi in kpi_plan:

            if not isinstance(kpi, dict):
                continue

            table = kpi.get("table")

            if not table:
                continue

            df = dataframes.get(table)

            if df is None:
                continue

            calculated = (
                AnalyticsService.execute_kpi_plan(
                    df=df,
                    table_name=table,
                    kpi_plan=[kpi],
                )
            )

            results.extend(calculated)

        return results

    # ======================================================
    # CALCUL SIMPLE
    # ======================================================

    @staticmethod
    def calculate_operation(
        series: pd.Series,
        operation: str,
    ) -> Any:

        return CalculationService.execute(
            series,
            operation,
        )

    # ======================================================
    # CLEAN
    # ======================================================

    @staticmethod
    def clean_value(
        value: Any,
    ) -> Any:

        if value is None:
            return None

        try:

            if pd.isna(value):
                return None

        except (
            TypeError,
            ValueError,
        ):
            pass

        if isinstance(
            value,
            np.generic,
        ):
            return value.item()

        if isinstance(
            value,
            (
                pd.Timestamp,
                pd.Timedelta,
            ),
        ):
            return str(value)

        return value

    # ======================================================
    # PROFIL
    # ======================================================

    @staticmethod
    def generate_data_profile(
        df: pd.DataFrame,
    ) -> dict:

        if df is None:

            return {
                "nombre_lignes": 0,
                "nombre_colonnes": 0,
                "colonnes": {},
            }

        profile = {
            "nombre_lignes": int(len(df)),
            "nombre_colonnes": int(len(df.columns)),
            "colonnes": {},
        }

        for column in df.columns:

            series = df[column]

            profile["colonnes"][column] = {
                "type": str(series.dtype),
                "valeurs_manquantes": int(
                    series.isna().sum()
                ),
                "pourcentage_manquant": round(
                    float(
                        series.isna().mean() * 100
                    ),
                    2,
                ),
                "valeurs_uniques": int(
                    series.nunique()
                ),
            }

        return profile

    # ======================================================
    # ANOMALIES
    # ======================================================

    @staticmethod
    def detect_anomalies(
        series: pd.Series,
    ) -> list[dict]:

        if series is None:
            return []

        numeric = pd.to_numeric(
            series,
            errors="coerce",
        ).dropna()

        if len(numeric) < 4:
            return []

        q1 = numeric.quantile(0.25)
        q3 = numeric.quantile(0.75)

        iqr = q3 - q1

        if iqr == 0:
            return []

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        mean = numeric.mean()
        std = numeric.std()

        if std == 0 or pd.isna(std):
            std = 1

        anomalies = numeric[
            (numeric < lower)
            | (numeric > upper)
        ]

        return [
            {
                "valeur": float(value),
                "ecart_moyenne": float(
                    (value - mean) / std
                ),
            }
            for value in anomalies.tolist()[:50]
        ]

    # ======================================================
    # PERSISTENCE KPI
    # ======================================================

    @staticmethod
    def persist_kpis(
        project_id: str,
        connection_id: str,
        kpi_dicts: list[dict],
    ) -> list[KPI]:

        if not kpi_dicts:
            return []

        saved = []

        allowed_fields = {
            "table_name",
            "column_name",
            "column_type",
            "nom",
            "formule",
            "valeur",
        }

        for data in kpi_dicts:

            if not isinstance(data, dict):
                continue

            clean_data = {
                key: value
                for key, value in data.items()
                if key in allowed_fields
            }

            clean_data["valeur"] = (
                AnalyticsService.clean_value(
                    clean_data.get("valeur")
                )
            )

            try:

                kpi = KPI(
                    project_id=project_id,
                    connection_id=connection_id,
                    **clean_data,
                )

            except TypeError:

                fallback = {
                    key: value
                    for key, value in clean_data.items()
                    if key != "table_name"
                }

                kpi = KPI(
                    project_id=project_id,
                    **fallback,
                )

            db.session.add(kpi)
            saved.append(kpi)

        if saved:
            db.session.commit()

        return saved

    # ======================================================
    # CREATE KPI
    # ======================================================

    @staticmethod
    def create_kpis(
        project_id: str,
        selected_kpis: list[dict],
        connection_id: str | None = None,
    ) -> list[KPI]:

        if not selected_kpis:
            return []

        calculated = []

        for data in selected_kpis:

            if not isinstance(data, dict):
                continue

            column = (
                data.get("column")
                or data.get("column_name")
            )

            if not column:
                continue

            operation = (
                data.get("operation")
                or data.get("formula")
                or data.get("formule")
                or "count"
            )

            operation = str(
                operation
            ).lower().strip()

            if operation not in (
                AnalyticsService.ALLOWED_OPERATIONS
            ):
                continue

            calculated.append(
                {
                    "table_name": data.get(
                        "table"
                    ),
                    "column_name": column,
                    "column_type": data.get(
                        "column_type"
                    ),
                    "nom": (
                        data.get("nom")
                        or data.get("name")
                        or data.get("label")
                        or "KPI"
                    ),
                    "formule": operation,
                    "valeur": data.get(
                        "valeur",
                        data.get("value"),
                    ),
                }
            )

        return AnalyticsService.persist_kpis(
            project_id=project_id,
            connection_id=connection_id,
            kpi_dicts=calculated,
        )