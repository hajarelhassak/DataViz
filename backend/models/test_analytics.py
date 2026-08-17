"""
Tests du calcul de statistiques et de la détection de type de colonne
(Partie 11 du guide : cœur de la logique métier de génération de dashboard).
"""
import pandas as pd

from services.analytics_service import AnalyticsService
from utils.chart_selector import choose_chart_type, detect_column_type


def test_detect_numeric_column():
    series = pd.Series([10.5, 20.1, 30.7, 40.2, 50.9])
    assert detect_column_type(series) == "numeric"


def test_detect_categorical_column():
    series = pd.Series(["Rabat", "Casablanca", "Rabat", "Fès", "Casablanca"] * 10)
    assert detect_column_type(series) == "categorical"


def test_detect_temporal_column():
    series = pd.Series(pd.date_range("2024-01-01", periods=12, freq="ME"))
    assert detect_column_type(series) == "temporal"


def test_numeric_stats_are_computed_correctly():
    df = pd.DataFrame({"chiffre_affaires": [100, 200, 300, 400, 500]})
    results = AnalyticsService.compute_statistics_for_dataframe(df, "ventes")

    stats_by_formule = {r["formule"]: r["valeur"] for r in results}
    assert stats_by_formule["moyenne"] == 300
    assert stats_by_formule["somme"] == 1500
    assert stats_by_formule["min"] == 100
    assert stats_by_formule["max"] == 500


def test_identifier_columns_are_excluded_from_statistics():
    """Une clé primaire (id) ou étrangère (produit_id) n'est pas une mesure métier."""
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "produit_id": [10, 20, 30, 40, 50],
        "montant": [100, 200, 300, 400, 500],
    })
    results = AnalyticsService.compute_statistics_for_dataframe(df, "ventes")
    columns_with_kpis = {r["column_name"] for r in results}
    assert "id" not in columns_with_kpis
    assert "produit_id" not in columns_with_kpis
    assert "montant" in columns_with_kpis


def test_chart_type_selection_heuristic():
    assert choose_chart_type("temporal") == "line"
    assert choose_chart_type("categorical", distinct_count=3) == "pie"
    assert choose_chart_type("categorical", distinct_count=20) == "bar"
    assert choose_chart_type("numeric") == "kpi_card"


def test_anomaly_detection_finds_outlier():
    series = pd.Series([10, 11, 9, 10, 12, 11, 500])  # 500 est une anomalie évidente
    anomalies = AnalyticsService.detect_anomalies(series)
    assert len(anomalies) >= 1
    assert any(a["valeur"] == 500 for a in anomalies)