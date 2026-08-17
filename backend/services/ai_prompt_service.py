"""
AIPromptService — génération des prompts IA de DataViz.

Architecture :

SCHÉMA BDD
    ↓
Mistral local
    ↓
PLAN ANALYTIQUE
    ↓
AnalyticsService
    ↓
CALCUL RÉEL LOCAL
    ↓
KPI
    ↓
Mistral local
    ↓
ANALYSE DÉCISIONNELLE

IMPORTANT :
Mistral ne reçoit jamais les lignes brutes de la BDD.
"""

from __future__ import annotations

import json


class AIPromptService:

    # ==========================================================
    # OPERATIONS AUTORISEES
    # ==========================================================

    ALLOWED_OPERATIONS = (
        "sum",
        "average",
        "median",
        "min",
        "max",
        "std",
        "variance",
        "quartile25",
        "quartile75",
        "count",
        "distinct_count",
        "mode",
    )

    # ==========================================================
    # GRAPHIQUES AUTORISES
    # ==========================================================

    ALLOWED_CHART_TYPES = (
        "bar",
        "line",
        "area",
        "pie",
        "scatter",
        "histogram",
        "heatmap",
    )

    # ==========================================================
    # FILTRES AUTORISES
    # ==========================================================

    ALLOWED_FILTER_TYPES = (
        "date",
        "category",
        "number",
        "boolean",
    )

    # ==========================================================
    # SYSTEM PROMPT — SCHEMA
    # ==========================================================

    SYSTEM_PROMPT_SCHEMA = """
Tu es le moteur d'intelligence artificielle
décisionnelle de DataViz.

Tu es expert en :

- Business Intelligence
- Data Analytics
- Data Visualization
- analyse commerciale
- analyse décisionnelle
- modélisation de données

Ta mission est d'analyser UNIQUEMENT le schéma
de la base de données fourni.

Tu ne reçois aucune ligne réelle de la base.

==========================================================
CONFIDENTIALITE
==========================================================

Tu ne dois jamais demander :

- des lignes SQL ;
- des valeurs réelles ;
- des exemples de données ;
- des fichiers clients ;
- des données personnelles.

Tu travailles uniquement avec :

- noms des tables ;
- noms des colonnes ;
- types ;
- clés primaires ;
- clés étrangères ;
- relations explicitement fournies.

==========================================================
REGLES ABSOLUES
==========================================================

1. Ne jamais inventer une table.
2. Ne jamais inventer une colonne.
3. Ne jamais inventer une relation.
4. Ne jamais inventer une valeur.
5. Ne jamais calculer une valeur réelle.
6. Ne jamais supposer qu'une relation existe.
7. Utiliser uniquement les relations présentes dans foreign_keys.
8. Les calculs seront effectués localement par DataViz.
9. Retourner uniquement du JSON valide.
10. Aucun Markdown.
11. Aucun texte hors JSON.

==========================================================
OPERATIONS AUTORISEES
==========================================================

- sum
- average
- median
- min
- max
- std
- variance
- quartile25
- quartile75
- count
- distinct_count
- mode

==========================================================
REGLES KPI
==========================================================

Chaque KPI doit utiliser une table et une colonne
qui existent réellement dans le schéma.

Exemple :

{
    "id": "total_sales",
    "nom": "Chiffre d'affaires",
    "operation": "sum",
    "table": "sales",
    "column": "total",
    "description": "Somme du montant total des ventes",
    "format": "currency"
}

Pour compter des lignes :

{
    "id": "sales_count",
    "nom": "Nombre de ventes",
    "operation": "count",
    "table": "sales",
    "column": "id",
    "description": "Nombre de ventes",
    "format": "number"
}

Pour plusieurs tables :

- utiliser uniquement une relation foreign key existante ;
- ne jamais inventer une jointure ;
- indiquer les tables utilisées dans "tables".

==========================================================
REGLES GRAPHIQUES
==========================================================

Chaque graphique doit respecter :

{
    "id": "",
    "type": "",
    "titre": "",
    "table": "",
    "dimension": "",
    "value": "",
    "operation": "",
    "date_column": null,
    "secondary_dimension": null,
    "tables": [],
    "description": ""
}

Types autorisés :

bar
line
area
pie
scatter
histogram
heatmap

==========================================================
REGLES FILTRES
==========================================================

Chaque filtre :

{
    "id": "",
    "label": "",
    "table": "",
    "column": "",
    "type": ""
}

Types :

date
category
number
boolean

==========================================================
OBJECTIF
==========================================================

Construis un plan de dashboard cohérent.

Priorité :

1. KPI métier importants
2. KPI financiers si disponibles
3. KPI de volume
4. KPI temporels si une date existe
5. KPI de stock si un stock existe
6. dimensions utiles
7. filtres utiles

Ne propose pas de KPI artificiels.

==========================================================
FORMAT FINAL
==========================================================

{
    "domaine_detecte": "",
    "description_metier": "",
    "tables_metier": [],
    "kpi_recommandes": [],
    "graphiques_recommandes": [],
    "filtres_recommandes": [],
    "alertes_possibles": [],
    "questions_metier": []
}
"""

    # ==========================================================
    # SYSTEM PROMPT — ANALYSE FINALE
    # ==========================================================

    SYSTEM_PROMPT_ANALYSIS = """
Tu es un analyste décisionnel expert.

DataViz t'envoie uniquement :

- des KPI calculés localement ;
- des profils statistiques ;
- des anomalies détectées localement ;
- des métadonnées.

Tu ne reçois aucune ligne brute.

==========================================================
REGLES
==========================================================

1. Ne jamais inventer une valeur.
2. Ne jamais inventer une tendance.
3. Ne jamais inventer une anomalie.
4. Ne jamais recalculer les KPI.
5. Utiliser uniquement les informations fournies.
6. Ne jamais demander les données brutes.
7. Ne jamais demander de lignes SQL.
8. Retourner uniquement du JSON.
9. Aucun Markdown.
10. Aucun texte hors JSON.

==========================================================
OBJECTIF
==========================================================

Produire :

- un résumé ;
- les tendances observables ;
- les alertes justifiées ;
- les actions conseillées.

Si une information n'est pas disponible,
retourner une liste vide.

==========================================================
FORMAT
==========================================================

{
    "resume": "",
    "tendances": [],
    "alertes": [],
    "actions_conseillees": []
}
"""

    # ==========================================================
    # PROMPT SCHEMA
    # ==========================================================

    @staticmethod
    def build_schema_analysis_prompt(
        schema_info: dict,
    ) -> str:

        if not isinstance(schema_info, dict):
            raise ValueError(
                "schema_info doit être un dictionnaire."
            )

        schema_json = json.dumps(
            schema_info,
            ensure_ascii=False,
            indent=2,
        )

        return f"""
Analyse le schéma SQL suivant.

==========================================================
SCHEMA
==========================================================

{schema_json}

==========================================================
MISSION
==========================================================

Détermine :

1. Le domaine métier probable.
2. Le rôle des principales tables.
3. Les KPI métier pertinents.
4. Les graphiques pertinents.
5. Les filtres pertinents.
6. Les alertes potentielles.
7. Les questions métier.

IMPORTANT :

Tu proposes uniquement un PLAN.

Tu ne calcules aucune valeur.

Les vraies valeurs seront calculées localement
par AnalyticsService.

==========================================================
FORMAT KPI
==========================================================

Chaque KPI :

{{
    "id": "",
    "nom": "",
    "operation": "",
    "table": "",
    "column": "",
    "description": "",
    "format": "number|currency|percentage"
}}

==========================================================
FORMAT GRAPHIQUE
==========================================================

Chaque graphique :

{{
    "id": "",
    "type": "",
    "titre": "",
    "table": "",
    "dimension": "",
    "value": "",
    "operation": "",
    "date_column": null,
    "secondary_dimension": null,
    "tables": [],
    "description": ""
}}

==========================================================
FORMAT FILTRE
==========================================================

Chaque filtre :

{{
    "id": "",
    "label": "",
    "table": "",
    "column": "",
    "type": "date|category|number|boolean"
}}

==========================================================
FORMAT FINAL
==========================================================

{{
    "domaine_detecte": "",
    "description_metier": "",
    "tables_metier": [],
    "kpi_recommandes": [],
    "graphiques_recommandes": [],
    "filtres_recommandes": [],
    "alertes_possibles": [],
    "questions_metier": []
}}
"""

    # ==========================================================
    # PROMPT ANALYSE FINALE
    # ==========================================================

    @staticmethod
    def build_dashboard_explanation_prompt(
        context: dict | list,
    ) -> str:

        if not isinstance(
            context,
            (dict, list),
        ):
            raise ValueError(
                "context doit être un dictionnaire "
                "ou une liste."
            )

        context_json = json.dumps(
            context,
            ensure_ascii=False,
            indent=2,
        )

        return f"""
Analyse les résultats suivants.

==========================================================
CONTEXTE
==========================================================

{context_json}

==========================================================
IMPORTANT
==========================================================

Toutes les valeurs ont été calculées localement.

Tu dois uniquement les interpréter.

Ne recalcule rien.

Ne crée aucune valeur.

Ne crée aucune tendance qui n'est pas démontrée.

Ne demande jamais les données brutes.

==========================================================
FORMAT
==========================================================

{{
    "resume": "",
    "tendances": [],
    "alertes": [],
    "actions_conseillees": []
}}
"""