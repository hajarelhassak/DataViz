"""
ExportService — gestion des exports DataViz.

Responsabilités :
- Exporter les dashboards générés.
- Exporter les KPI calculés.
- Exporter les rapports analytiques.

Sécurité :
- Aucun accès aux bases clientes.
- Utilise uniquement les résultats déjà calculés.
"""

from __future__ import annotations

import io
import json

import pandas as pd

from flask import send_file

from models.dashboard import Dashboard
from models.kpi import KPI



class ExportService:


    # =====================================================
    # Export Dashboard PNG
    # =====================================================

    @staticmethod
    def export_dashboard_png(
        dashboard: Dashboard
    ) -> io.BytesIO:

        """
        Génère une image PNG du premier graphique.
        """

        import plotly.graph_objects as go


        if not dashboard.charts:

            raise ValueError(
                "Le dashboard ne contient aucun graphique."
            )


        chart = dashboard.charts[0]


        figure = json.loads(
            chart.config_json
        )


        fig = go.Figure(
            figure
        )


        image = fig.to_image(
            format="png"
        )


        return io.BytesIO(
            image
        )



    # =====================================================
    # Export KPI Excel
    # =====================================================

    @staticmethod
    def export_kpis_excel(
        kpis: list[KPI]
    ) -> io.BytesIO:

        """
        Exporte les KPI calculés en Excel.
        """

        rows = []


        for kpi in kpis:

            rows.append({

                "nom": kpi.nom,

                "table": kpi.table_name,

                "colonne": getattr(
                    kpi,
                    "column_name",
                    None
                ),

                "formule": kpi.formule,

                "valeur": kpi.valeur,

                "unite": kpi.unite,

                "type": getattr(
                    kpi,
                    "column_type",
                    None
                )

            })


        df = pd.DataFrame(
            rows
        )


        output = io.BytesIO()


        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                index=False,
                sheet_name="KPI"
            )


        output.seek(0)


        return output



    # =====================================================
    # Export JSON
    # =====================================================

    @staticmethod
    def export_dashboard_json(
        dashboard: Dashboard
    ) -> io.BytesIO:

        """
        Export de la structure complète du dashboard.
        """

        data = {


            "id":
                dashboard.id,


            "nom":
                dashboard.nom,


            "charts":[]

        }


        for chart in dashboard.charts:

            data["charts"].append({

                "titre":
                    chart.titre,


                "type":
                    chart.type_graphique,


                "configuration":
                    json.loads(
                        chart.config_json
                    )

            })


        file = io.BytesIO(

            json.dumps(
                data,
                ensure_ascii=False,
                indent=4
            ).encode(
                "utf-8"
            )

        )


        return file



    # =====================================================
    # Export rapport IA
    # =====================================================

    @staticmethod
    def export_ai_report_json(
        report
    ) -> io.BytesIO:

        """
        Exporte l'analyse IA générée.
        """

        data = {

            "statut":
                report.statut,


            "analyse":
                json.loads(
                    report.resultat_json
                )
                if report.resultat_json
                else None,


            "erreur":
                report.erreur_message

        }


        return io.BytesIO(

            json.dumps(
                data,
                ensure_ascii=False,
                indent=4
            ).encode(
                "utf-8"
            )

        )