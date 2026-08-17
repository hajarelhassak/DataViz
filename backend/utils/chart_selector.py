"""
Chart selector — sélection automatique des visualisations.

Principe :
- Aucun calcul approximatif.
- Analyse complète des métadonnées pandas.
- Les règles déterministes remplacent un modèle ML pour garantir
  une génération stable des dashboards.
"""

from __future__ import annotations

import pandas as pd


CHART_BAR = "bar"
CHART_PIE = "pie"
CHART_LINE = "line"
CHART_SCATTER = "scatter"
CHART_KPI_CARD = "kpi_card"
CHART_TABLE = "table"


PIE_MAX_DISTINCT_VALUES = 6



def detect_column_type(series: pd.Series) -> str:
    """
    Détecte le type métier d'une colonne complète.
    """

    values = series.dropna()

    if values.empty:
        return "text"


    if pd.api.types.is_datetime64_any_dtype(values):
        return "temporal"


    if pd.api.types.is_numeric_dtype(values):

        distinct = values.nunique()

        ratio = distinct / len(values)


        # Exemple :
        # statut = 1,2,3
        # sexe = 0,1
        if distinct <= 10 and ratio < 0.05:
            return "categorical"


        return "numeric"



    # Tentative date complète
    try:

        parsed = pd.to_datetime(
            values,
            errors="coerce"
        )


        valid_ratio = parsed.notna().mean()


        if valid_ratio == 1:
            return "temporal"


    except Exception:
        pass



    distinct_ratio = values.nunique() / len(values)


    if values.nunique() <= 50 or distinct_ratio < 0.5:
        return "categorical"


    return "text"




def choose_chart_type(
    column_type: str,
    distinct_count: int = 0
) -> str:


    if column_type == "temporal":
        return CHART_LINE


    if column_type == "categorical":

        if distinct_count <= PIE_MAX_DISTINCT_VALUES:
            return CHART_PIE

        return CHART_BAR



    if column_type == "numeric":
        return CHART_KPI_CARD



    return CHART_TABLE




def choose_chart_for_two_columns(
    type_a: str,
    type_b: str
) -> str:


    if (
        "temporal" in {type_a, type_b}
        and
        "numeric" in {type_a, type_b}
    ):
        return CHART_LINE


    if type_a == "numeric" and type_b == "numeric":
        return CHART_SCATTER


    return CHART_BAR