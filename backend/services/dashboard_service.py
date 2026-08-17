"""
DashboardService — génération des dashboards.

Responsabilités :

- créer le dashboard ;
- créer les cartes KPI ;
- créer les graphiques ;
- persister les configurations Plotly ;
- supprimer les graphiques ;
- exporter les dashboards.

Ce service ne calcule aucune statistique.
"""

from __future__ import annotations

import io
import json

import plotly.graph_objects as go

from app.extensions import db
from models.dashboard import Dashboard, Chart
from models.kpi import KPI


class DashboardService:

    # ==========================================================
    # KPI CARD
    # ==========================================================

    @staticmethod
    def build_kpi_card(
        kpi: KPI,
    ) -> tuple[str, dict]:

        value = kpi.valeur

        if value is None:
            value = 0

        try:
            value = float(value)
        except (
            TypeError,
            ValueError,
        ):
            value = 0

        fig = go.Figure(
            go.Indicator(
                mode="number",
                value=value,
                title={
                    "text": kpi.nom
                },
            )
        )

        fig.update_layout(
            height=250,
            margin=dict(
                l=20,
                r=20,
                t=50,
                b=20,
            ),
        )

        return (
            "kpi",
            json.loads(
                fig.to_json()
            ),
        )

    # ==========================================================
    # BAR CHART KPI
    # ==========================================================

    @staticmethod
    def build_bar_for_kpi(
        kpi: KPI,
    ) -> tuple[str, dict]:

        value = kpi.valeur

        if value is None:
            value = 0

        try:
            value = float(value)
        except (
            TypeError,
            ValueError,
        ):
            value = 0

        fig = go.Figure(
            data=[
                go.Bar(
                    x=[kpi.nom],
                    y=[value],
                )
            ]
        )

        fig.update_layout(
            height=300,
            margin=dict(
                l=20,
                r=20,
                t=40,
                b=20,
            ),
        )

        return (
            "bar",
            json.loads(
                fig.to_json()
            ),
        )

    # ==========================================================
    # FIGURE KPI
    # ==========================================================

    @staticmethod
    def build_figure_for_kpi(
        kpi: KPI,
    ) -> tuple[str, dict]:

        """
        Pour le moment, chaque KPI est affiché
        sous forme de carte KPI.

        Le choix automatique entre :
        - bar
        - line
        - pie
        - heatmap

        pourra être ajouté plus tard.
        """

        return (
            DashboardService
            .build_kpi_card(kpi)
        )

    # ==========================================================
    # CREATION DASHBOARD
    # ==========================================================

    @staticmethod
    def generate_dashboard(
        project_id: str,
        nom: str,
        kpis: list[KPI],
    ) -> Dashboard:

        if not project_id:
            raise ValueError(
                "project_id requis."
            )

        if not nom or not nom.strip():
            raise ValueError(
                "Le nom du dashboard est requis."
            )

        if not kpis:
            raise ValueError(
                "Impossible de créer un dashboard sans KPI."
            )

        dashboard = Dashboard(
            project_id=project_id,
            nom=nom.strip(),
        )

        db.session.add(dashboard)

        db.session.flush()

        for kpi in kpis:

            chart_type, figure = (
                DashboardService
                .build_figure_for_kpi(kpi)
            )

            chart = Chart(
                dashboard_id=dashboard.id,
                kpi_source_id=kpi.id,
                type_graphique=chart_type,
                titre=kpi.nom,
                config_json=json.dumps(
                    figure,
                    ensure_ascii=False,
                ),
            )

            db.session.add(chart)

        db.session.commit()

        return dashboard

    # ==========================================================
    # DASHBOARDS PROJET
    # ==========================================================

    @staticmethod
    def get_project_dashboards(
        project_id: str,
    ) -> list[Dashboard]:

        return (
            Dashboard.query
            .filter_by(
                project_id=project_id
            )
            .order_by(
                Dashboard.created_at.desc()
            )
            .all()
        )

    # ==========================================================
    # FIGURE
    # ==========================================================

    @staticmethod
    def get_chart_figure(
        chart: Chart,
    ) -> dict:

        if not chart.config_json:
            return {}

        try:

            return json.loads(
                chart.config_json
            )

        except (
            TypeError,
            json.JSONDecodeError,
        ):

            return {}

    # ==========================================================
    # SUPPRESSION GRAPHIQUE
    # ==========================================================

    @staticmethod
    def remove_chart(
        dashboard: Dashboard,
        chart_id: str,
    ) -> None:

        chart = (
            Chart.query
            .filter_by(
                id=chart_id,
                dashboard_id=dashboard.id,
            )
            .first()
        )

        if chart is None:
            raise ValueError(
                "Graphique introuvable."
            )

        db.session.delete(chart)

        db.session.commit()

    # ==========================================================
    # EXPORT PNG
    # ==========================================================

    @staticmethod
    def export_dashboard_as_png(
        dashboard: Dashboard,
        output_path: str,
    ) -> str:

        if not dashboard.charts:
            raise ValueError(
                "Dashboard vide."
            )

        chart = dashboard.charts[0]

        figure_config = (
            DashboardService
            .get_chart_figure(chart)
        )

        if not figure_config:
            raise ValueError(
                "Configuration du graphique vide."
            )

        fig = go.Figure(
            figure_config
        )

        fig.write_image(
            output_path
        )

        return output_path

    # ==========================================================
    # EXPORT MEMOIRE
    # ==========================================================

    @staticmethod
    def export_dashboard_as_bytesio(
        dashboard: Dashboard,
    ) -> io.BytesIO:

        if not dashboard.charts:
            raise ValueError(
                "Dashboard vide."
            )

        chart = dashboard.charts[0]

        figure_config = (
            DashboardService
            .get_chart_figure(chart)
        )

        if not figure_config:
            raise ValueError(
                "Configuration du graphique vide."
            )

        fig = go.Figure(
            figure_config
        )

        image_bytes = fig.to_image(
            format="png"
        )

        return io.BytesIO(
            image_bytes
        )