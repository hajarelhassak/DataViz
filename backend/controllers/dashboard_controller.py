"""
DashboardController — gestion des dashboards.

Responsabilités :
- créer un dashboard ;
- générer un dashboard à partir de KPI ;
- récupérer un dashboard ;
- lister les dashboards d'un projet ;
- supprimer un dashboard ;
- supprimer un graphique ;
- exporter un dashboard.

IMPORTANT :
L'authentification JWT est temporairement désactivée
pour faciliter le développement du MVP.

Pour réactiver l'authentification plus tard :
    1. décommenter les @jwt_required()
    2. réactiver _get_current_user_id()
    3. réactiver les vérifications owner_id.
"""

import base64
import traceback

from flask import Blueprint, jsonify, request

# ==========================================================
# JWT — TEMPORAIREMENT DESACTIVE
# ==========================================================
#
# from flask_jwt_extended import jwt_required, get_jwt_identity
#
# Les imports restent commentés volontairement.
# L'authentification sera réactivée ultérieurement.
# ==========================================================

from app.extensions import db

from models.dashboard import Dashboard
from models.project import Project

from services.analytics_service import AnalyticsService
from services.dashboard_service import DashboardService
from services.audit_service import AuditService


# ==========================================================
# BLUEPRINT
# ==========================================================

dashboard_bp = Blueprint(
    "dashboards",
    __name__,
    url_prefix="/api/dashboards",
)


# ==========================================================
# OUTILS
# ==========================================================

def _get_current_user_id():
    """
    Récupère l'identifiant de l'utilisateur connecté.

    AUTHENTIFICATION TEMPORAIREMENT DESACTIVEE.

    Cette fonction retourne None volontairement.

    Elle pourra être réactivée plus tard avec :

        from flask_jwt_extended import get_jwt_identity

        user_id = get_jwt_identity()

    """

    # ======================================================
    # JWT TEMPORAIREMENT DESACTIVE
    # ======================================================

    return None

    # Ancienne logique JWT :

    # try:
    #     user_id = get_jwt_identity()

    #     if user_id is None:
    #         return None

    #     return str(user_id)

    # except Exception as exc:
    #     print(
    #         "[DashboardController] "
    #         "Erreur JWT :",
    #         exc,
    #     )
    #     traceback.print_exc()

    #     return None


def _safe_id(value):
    """
    Transforme un UUID / identifiant SQLAlchemy en string.
    """

    if value is None:
        return None

    return str(value)


def _json_response(
    success,
    error=None,
    status=200,
    **kwargs,
):
    """
    Construit une réponse JSON uniforme.
    """

    data = {
        "success": success,
    }

    if error is not None:
        data["error"] = error

    data.update(kwargs)

    return jsonify(data), status


def _serialize_dashboard(dashboard):
    """
    Sérialisation robuste d'un Dashboard.
    """

    if dashboard is None:
        return None

    try:

        data = dashboard.to_dict()

        if not isinstance(data, dict):
            data = {}

    except Exception as exc:

        print(
            "[DashboardController] "
            "Erreur Dashboard.to_dict() :",
            exc,
        )

        traceback.print_exc()

        data = {}

    # ------------------------------------------------------
    # GARANTIES MINIMALES
    # ------------------------------------------------------

    data["id"] = _safe_id(
        getattr(
            dashboard,
            "id",
            None,
        )
    )

    data["project_id"] = _safe_id(
        getattr(
            dashboard,
            "project_id",
            None,
        )
    )

    if hasattr(
        dashboard,
        "nom",
    ):
        data["nom"] = dashboard.nom

    if hasattr(
        dashboard,
        "name",
    ):
        data["name"] = dashboard.name

    if hasattr(
        dashboard,
        "created_at",
    ):

        created_at = dashboard.created_at

        data["created_at"] = (
            created_at.isoformat()
            if created_at is not None
            else None
        )

    if hasattr(
        dashboard,
        "updated_at",
    ):

        updated_at = dashboard.updated_at

        data["updated_at"] = (
            updated_at.isoformat()
            if updated_at is not None
            else None
        )

    return data


# ==========================================================
# PROJET
# ==========================================================

def _get_owned_project(
    project_id,
    user_id=None,
):
    """
    Recherche un projet.

    AUTHENTIFICATION TEMPORAIREMENT DESACTIVEE.

    Avant :
        le projet devait appartenir à user_id.

    Maintenant :
        on recherche simplement le projet par son ID.

    Retour :
        project, None

    ou :
        None, (json_response, status)
    """

    if not project_id:

        return None, _json_response(
            False,
            "project_id requis.",
            400,
        )

    try:

        # ==================================================
        # AUTHENTIFICATION DESACTIVEE
        # ==================================================
        #
        # Ancienne logique :
        #
        # if not user_id:
        #     return None, _json_response(
        #         False,
        #         "Utilisateur non authentifié.",
        #         401,
        #     )
        #
        # project = (
        #     Project.query
        #     .filter(
        #         Project.id == project_id,
        #         Project.owner_id == user_id,
        #     )
        #     .first()
        # )
        #
        # ==================================================

        project = (
            Project.query
            .filter(
                Project.id == project_id
            )
            .first()
        )

    except Exception as exc:

        db.session.rollback()

        print(
            "[DashboardController] "
            "Erreur recherche projet :",
            exc,
        )

        traceback.print_exc()

        return None, _json_response(
            False,
            "Erreur lors de la recherche du projet.",
            500,
            details=str(exc),
        )

    # ------------------------------------------------------
    # PROJET INTROUVABLE
    # ------------------------------------------------------

    if project is None:

        return None, _json_response(
            False,
            "Projet introuvable.",
            404,
        )

    # ------------------------------------------------------
    # IMPORTANT
    # ------------------------------------------------------
    #
    # C'est le return qui manquait dans ton ancien fichier.
    #
    # ------------------------------------------------------

    return project, None


# ==========================================================
# DASHBOARD
# ==========================================================

def _get_owned_dashboard(
    dashboard_id,
    user_id=None,
):
    """
    Recherche un dashboard.

    AUTHENTIFICATION TEMPORAIREMENT DESACTIVEE.

    Le dashboard est recherché uniquement avec son ID.

    Plus tard, on pourra réactiver la vérification :

        Project.owner_id == user_id
    """

    if not dashboard_id:

        return None, _json_response(
            False,
            "dashboard_id requis.",
            400,
        )

    try:

        # ==================================================
        # AUTHENTIFICATION DESACTIVEE
        # ==================================================
        #
        # Ancienne requête :
        #
        # dashboard = (
        #     Dashboard.query
        #     .join(
        #         Project,
        #         Dashboard.project_id == Project.id,
        #     )
        #     .filter(
        #         Dashboard.id == dashboard_id,
        #         Project.owner_id == user_id,
        #     )
        #     .first()
        # )
        #
        # ==================================================

        dashboard = (
            Dashboard.query
            .filter(
                Dashboard.id == dashboard_id
            )
            .first()
        )

    except Exception as exc:

        print(
            "[DashboardController] "
            "Erreur recherche dashboard :",
            exc,
        )

        traceback.print_exc()

        return None, _json_response(
            False,
            "Erreur lors de la recherche du dashboard.",
            500,
            details=str(exc),
        )

    if dashboard is None:

        return None, _json_response(
            False,
            "Dashboard introuvable.",
            404,
        )

    return dashboard, None


# ==========================================================
# AUDIT
# ==========================================================

def _audit(
    user_id,
    action,
    details,
):
    """
    Audit non bloquant.

    L'audit ne doit jamais empêcher
    l'opération principale.

    AUTHENTIFICATION DESACTIVEE :
    user_id peut être None.
    """

    try:

        AuditService.log(
            user_id,
            action,
            details,
            request.remote_addr,
        )

    except Exception as exc:

        print(
            "[DashboardController] "
            f"Erreur audit {action} :",
            exc,
        )

        traceback.print_exc()


# ==========================================================
# CREATION SIMPLE
# ==========================================================

@dashboard_bp.post("")
# @jwt_required()  # AUTHENTIFICATION TEMPORAIREMENT DESACTIVEE
def create_dashboard():
    """
    POST /api/dashboards

    Exemple :

    {
        "project_id": "...",
        "name": "Dashboard commercial",
        "connection_id": "...",
        "tables": [
            "customers",
            "orders"
        ]
    }
    """

    print("\n==========================================")
    print("[DashboardController] POST /api/dashboards")
    print("==========================================")

    # ======================================================
    # JWT DESACTIVE
    # ======================================================

    # user_id = _get_current_user_id()

    user_id = None

    print(
        "[DashboardController] "
        "AUTHENTIFICATION : DESACTIVEE"
    )

    # ------------------------------------------------------
    # JSON
    # ------------------------------------------------------

    payload = request.get_json(
        silent=True
    )

    if payload is None:
        payload = {}

    if not isinstance(
        payload,
        dict,
    ):

        return _json_response(
            False,
            "Le payload doit être un objet JSON.",
            400,
        )

    print(
        "[DashboardController] PAYLOAD :",
        payload,
    )

    # ------------------------------------------------------
    # PARAMETRES
    # ------------------------------------------------------

    project_id = payload.get(
        "project_id"
    )

    connection_id = payload.get(
        "connection_id"
    )

    name = (
        payload.get("name")
        or payload.get("nom")
        or ""
    )

    if not isinstance(
        name,
        str,
    ):

        name = str(name)

    name = name.strip()

    tables = payload.get(
        "tables",
        [],
    )

    # ------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------

    if not project_id:

        return _json_response(
            False,
            "project_id requis.",
            400,
        )

    if not name:

        return _json_response(
            False,
            "Le nom du dashboard est requis.",
            400,
        )

    if len(name) > 255:

        return _json_response(
            False,
            "Le nom du dashboard ne peut pas dépasser 255 caractères.",
            400,
        )

    if not connection_id:

        return _json_response(
            False,
            "connection_id requis.",
            400,
        )

    if not isinstance(
        tables,
        list,
    ):

        return _json_response(
            False,
            "Le champ tables doit être un tableau.",
            400,
        )

    # ------------------------------------------------------
    # NORMALISATION TABLES
    # ------------------------------------------------------

    normalized_tables = []

    for table in tables:

        if table is None:
            continue

        if isinstance(
            table,
            str,
        ):

            table_name = table.strip()

            if table_name:

                normalized_tables.append(
                    table_name
                )

        elif isinstance(
            table,
            dict,
        ):

            table_name = (
                table.get("table_name")
                or table.get("table")
                or table.get("name")
            )

            if table_name:

                table_name = str(
                    table_name
                ).strip()

                if table_name:

                    normalized_tables.append(
                        table_name
                    )

    print(
        "[DashboardController] PROJECT ID :",
        project_id,
    )

    print(
        "[DashboardController] NAME :",
        name,
    )

    print(
        "[DashboardController] CONNECTION ID :",
        connection_id,
    )

    print(
        "[DashboardController] TABLES :",
        normalized_tables,
    )

    # ------------------------------------------------------
    # VERIFICATION PROJET
    # ------------------------------------------------------

    project, error_response = _get_owned_project(
        project_id,
        user_id,
    )

    if error_response:

        return error_response

    # ------------------------------------------------------
    # CREATION
    # ------------------------------------------------------

    try:

        dashboard = Dashboard(
            project_id=project.id,
            nom=name,
        )

        db.session.add(
            dashboard
        )

        db.session.commit()

        db.session.refresh(
            dashboard
        )

        print(
            "[DashboardController] "
            "DASHBOARD CREE :",
            dashboard.id,
        )

    except Exception as exc:

        db.session.rollback()

        print(
            "[DashboardController] "
            "ERREUR CREATION DASHBOARD :",
            exc,
        )

        traceback.print_exc()

        return _json_response(
            False,
            "Impossible de créer le dashboard.",
            500,
            details=str(exc),
        )

    # ------------------------------------------------------
    # SERIALISATION
    # ------------------------------------------------------

    dashboard_id = _safe_id(
        dashboard.id
    )

    dashboard_data = _serialize_dashboard(
        dashboard
    )

    # ------------------------------------------------------
    # AUDIT
    # ------------------------------------------------------

    _audit(
        user_id,
        "dashboard_created",
        {
            "dashboard_id": dashboard_id,
            "project_id": _safe_id(
                project.id
            ),
            "connection_id": _safe_id(
                connection_id
            ),
            "tables": normalized_tables,
        },
    )

    # ------------------------------------------------------
    # REPONSE
    # ------------------------------------------------------

    print(
        "[DashboardController] "
        "RESPONSE 201 :",
        dashboard_id,
    )

    return _json_response(
        True,
        status=201,
        message="Dashboard créé avec succès.",
        id=dashboard_id,
        dashboard_id=dashboard_id,
        dashboard=dashboard_data,
    )


# ==========================================================
# GENERATION COMPLETE
# ==========================================================

@dashboard_bp.post("/generate")
# @jwt_required()  # AUTHENTIFICATION TEMPORAIREMENT DESACTIVEE
def generate_dashboard():
    """
    POST /api/dashboards/generate

    Exemple :

    {
        "project_id": "...",
        "connection_id": "...",
        "table_name": "orders",
        "nom": "Dashboard ventes",
        "kpis": [
            {
                "column": "price",
                "operation": "sum"
            }
        ]
    }
    """

    print("\n==========================================")
    print("[DashboardController] POST /api/dashboards/generate")
    print("==========================================")

    # ======================================================
    # JWT DESACTIVE
    # ======================================================

    # user_id = _get_current_user_id()

    user_id = None

    print(
        "[DashboardController] "
        "AUTHENTIFICATION : DESACTIVEE"
    )

    # ------------------------------------------------------
    # JSON
    # ------------------------------------------------------

    payload = request.get_json(
        silent=True
    ) or {}

    if not isinstance(
        payload,
        dict,
    ):

        return _json_response(
            False,
            "Le payload doit être un objet JSON.",
            400,
        )

    project_id = payload.get(
        "project_id"
    )

    connection_id = payload.get(
        "connection_id"
    )

    table_name = payload.get(
        "table_name"
    )

    dashboard_name = (
        payload.get("nom")
        or payload.get("name")
        or "Nouveau Dashboard"
    )

    if not isinstance(
        dashboard_name,
        str,
    ):

        dashboard_name = str(
            dashboard_name
        )

    dashboard_name = dashboard_name.strip()

    selected_kpis = payload.get(
        "kpis",
        [],
    )

    # ------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------

    if not project_id:

        return _json_response(
            False,
            "project_id requis.",
            400,
        )

    if not connection_id:

        return _json_response(
            False,
            "connection_id requis.",
            400,
        )

    if not table_name:

        return _json_response(
            False,
            "table_name requis.",
            400,
        )

    if (
        not isinstance(
            selected_kpis,
            list,
        )
        or not selected_kpis
    ):

        return _json_response(
            False,
            "Aucun KPI sélectionné.",
            400,
        )

    # ------------------------------------------------------
    # PROJET
    # ------------------------------------------------------

    project, error_response = _get_owned_project(
        project_id,
        user_id,
    )

    if error_response:

        return error_response

    # ------------------------------------------------------
    # CONNECTION SERVICE
    # ------------------------------------------------------

    try:

        from services.connection_service import (
            ConnectionService
        )

        load_method = getattr(
            ConnectionService,
            "load_table_dataframe",
            None,
        )

        if not callable(
            load_method
        ):

            return _json_response(
                False,
                "ConnectionService.load_table_dataframe n'est pas disponible.",
                500,
            )

        df = load_method(
            connection_id=connection_id,
            table_name=table_name,
            project_id=project_id,
        )

    except Exception as exc:

        print(
            "[DashboardController] "
            "ERREUR CHARGEMENT DONNEES :",
            exc,
        )

        traceback.print_exc()

        return _json_response(
            False,
            "Impossible de charger les données de la connexion.",
            500,
            details=str(exc),
        )

    if df is None:

        return _json_response(
            False,
            "Aucune donnée n'a été retournée par la connexion.",
            422,
        )

    # ------------------------------------------------------
    # CALCUL KPI
    # ------------------------------------------------------

    try:

        execute_method = getattr(
            AnalyticsService,
            "execute_kpi_plan",
            None,
        )

        if not callable(
            execute_method
        ):

            return _json_response(
                False,
                "AnalyticsService.execute_kpi_plan n'est pas disponible.",
                500,
            )

        kpi_results = execute_method(
            df=df,
            table_name=table_name,
            kpi_plan=selected_kpis,
        )

    except Exception as exc:

        print(
            "[DashboardController] "
            "ERREUR CALCUL KPI :",
            exc,
        )

        traceback.print_exc()

        return _json_response(
            False,
            "Erreur pendant le calcul des KPI.",
            500,
            details=str(exc),
        )

    if not kpi_results:

        return _json_response(
            False,
            "Aucun KPI valide n'a pu être calculé.",
            422,
        )

    # ------------------------------------------------------
    # PERSISTENCE KPI
    # ------------------------------------------------------

    try:

        persist_method = getattr(
            AnalyticsService,
            "persist_kpis",
            None,
        )

        if not callable(
            persist_method
        ):

            return _json_response(
                False,
                "AnalyticsService.persist_kpis n'est pas disponible.",
                500,
            )

        kpis = persist_method(
            project_id=project_id,
            connection_id=connection_id,
            kpi_dicts=kpi_results,
        )

    except Exception as exc:

        db.session.rollback()

        print(
            "[DashboardController] "
            "ERREUR SAUVEGARDE KPI :",
            exc,
        )

        traceback.print_exc()

        return _json_response(
            False,
            "Impossible de sauvegarder les KPI.",
            500,
            details=str(exc),
        )

    if not kpis:

        return _json_response(
            False,
            "Aucun KPI n'a été sauvegardé.",
            422,
        )

    # ------------------------------------------------------
    # GENERATION DASHBOARD
    # ------------------------------------------------------

    try:

        generate_method = getattr(
            DashboardService,
            "generate_dashboard",
            None,
        )

        if not callable(
            generate_method
        ):

            return _json_response(
                False,
                "DashboardService.generate_dashboard n'est pas disponible.",
                500,
            )

        dashboard = generate_method(
            project_id=project_id,
            nom=dashboard_name,
            kpis=kpis,
        )

        if dashboard is None:

            return _json_response(
                False,
                "La génération du dashboard n'a retourné aucun résultat.",
                422,
            )

        db.session.commit()

    except ValueError as exc:

        db.session.rollback()

        return _json_response(
            False,
            str(exc),
            422,
        )

    except Exception as exc:

        db.session.rollback()

        print(
            "[DashboardController] "
            "ERREUR GENERATION DASHBOARD :",
            exc,
        )

        traceback.print_exc()

        return _json_response(
            False,
            "Impossible de générer le dashboard.",
            500,
            details=str(exc),
        )

    # ------------------------------------------------------
    # REPONSE
    # ------------------------------------------------------

    dashboard_id = _safe_id(
        dashboard.id
    )

    dashboard_data = _serialize_dashboard(
        dashboard
    )

    _audit(
        user_id,
        "dashboard_generated",
        {
            "dashboard_id": dashboard_id,
            "project_id": _safe_id(
                project_id
            ),
        },
    )

    return _json_response(
        True,
        status=201,
        dashboard=dashboard_data,
        id=dashboard_id,
        dashboard_id=dashboard_id,
    )


# ==========================================================
# LISTE DES DASHBOARDS D'UN PROJET
# IMPORTANT :
# Cette route est placée AVANT /<dashboard_id>
# ==========================================================

@dashboard_bp.get(
    "/project/<project_id>"
)
# @jwt_required()  # AUTHENTIFICATION TEMPORAIREMENT DESACTIVEE
def list_project_dashboards(
    project_id,
):

    # ======================================================
    # JWT DESACTIVE
    # ======================================================

    # user_id = _get_current_user_id()

    user_id = None

    project, error_response = _get_owned_project(
        project_id,
        user_id,
    )

    if error_response:

        return error_response

    try:

        query = (
            Dashboard.query
            .filter(
                Dashboard.project_id == project.id
            )
        )

        if hasattr(
            Dashboard,
            "created_at",
        ):

            query = query.order_by(
                Dashboard.created_at.desc()
            )

        dashboards = query.all()

    except Exception as exc:

        print(
            "[DashboardController] "
            "ERREUR LISTE DASHBOARDS :",
            exc,
        )

        traceback.print_exc()

        return _json_response(
            False,
            "Impossible de récupérer les dashboards.",
            500,
            details=str(exc),
        )

    return jsonify([
        _serialize_dashboard(
            dashboard
        )
        for dashboard in dashboards
    ]), 200


# ==========================================================
# RECUPERATION DASHBOARD
# ==========================================================

@dashboard_bp.get(
    "/<dashboard_id>"
)
# @jwt_required()  # AUTHENTIFICATION TEMPORAIREMENT DESACTIVEE
def get_dashboard(
    dashboard_id,
):

    # ======================================================
    # JWT DESACTIVE
    # ======================================================

    # user_id = _get_current_user_id()

    user_id = None

    dashboard, error_response = _get_owned_dashboard(
        dashboard_id,
        user_id,
    )

    if error_response:

        return error_response

    return jsonify(
        _serialize_dashboard(
            dashboard
        )
    ), 200


# ==========================================================
# SUPPRESSION DASHBOARD
# ==========================================================

@dashboard_bp.delete(
    "/<dashboard_id>"
)
# @jwt_required()  # AUTHENTIFICATION TEMPORAIREMENT DESACTIVEE
def delete_dashboard(
    dashboard_id,
):

    # ======================================================
    # JWT DESACTIVE
    # ======================================================

    # user_id = _get_current_user_id()

    user_id = None

    dashboard, error_response = _get_owned_dashboard(
        dashboard_id,
        user_id,
    )

    if error_response:

        return error_response

    try:

        db.session.delete(
            dashboard
        )

        db.session.commit()

    except Exception as exc:

        db.session.rollback()

        print(
            "[DashboardController] "
            "ERREUR SUPPRESSION DASHBOARD :",
            exc,
        )

        traceback.print_exc()

        return _json_response(
            False,
            "Impossible de supprimer le dashboard.",
            500,
            details=str(exc),
        )

    _audit(
        user_id,
        "dashboard_deleted",
        {
            "dashboard_id": _safe_id(
                dashboard_id
            )
        },
    )

    return _json_response(
        True,
        status=200,
        message="Dashboard supprimé.",
    )


# ==========================================================
# SUPPRESSION GRAPHIQUE
# ==========================================================

@dashboard_bp.delete(
    "/<dashboard_id>/charts/<chart_id>"
)
# @jwt_required()  # AUTHENTIFICATION TEMPORAIREMENT DESACTIVEE
def remove_chart(
    dashboard_id,
    chart_id,
):

    # ======================================================
    # JWT DESACTIVE
    # ======================================================

    # user_id = _get_current_user_id()

    user_id = None

    dashboard, error_response = _get_owned_dashboard(
        dashboard_id,
        user_id,
    )

    if error_response:

        return error_response

    try:

        remove_method = getattr(
            DashboardService,
            "remove_chart",
            None,
        )

        if not callable(
            remove_method
        ):

            return _json_response(
                False,
                "DashboardService.remove_chart n'est pas disponible.",
                500,
            )

        result = remove_method(
            dashboard,
            chart_id,
        )

        if result is not False:

            db.session.commit()

    except Exception as exc:

        db.session.rollback()

        print(
            "[DashboardController] "
            "ERREUR SUPPRESSION GRAPHIQUE :",
            exc,
        )

        traceback.print_exc()

        return _json_response(
            False,
            "Impossible de supprimer le graphique.",
            500,
            details=str(exc),
        )

    _audit(
        user_id,
        "chart_removed",
        {
            "dashboard_id": _safe_id(
                dashboard_id
            ),
            "chart_id": _safe_id(
                chart_id
            ),
        },
    )

    return _json_response(
        True,
        status=200,
        message="Graphique supprimé.",
    )


# ==========================================================
# EXPORT IMAGE
# ==========================================================

@dashboard_bp.get(
    "/<dashboard_id>/image-data"
)
# @jwt_required()  # AUTHENTIFICATION TEMPORAIREMENT DESACTIVEE
def export_dashboard_image(
    dashboard_id,
):

    # ======================================================
    # JWT DESACTIVE
    # ======================================================

    # user_id = _get_current_user_id()

    user_id = None

    dashboard, error_response = _get_owned_dashboard(
        dashboard_id,
        user_id,
    )

    if error_response:

        return error_response

    try:

        export_method = getattr(
            DashboardService,
            "export_dashboard_as_bytesio",
            None,
        )

        if not callable(
            export_method
        ):

            return _json_response(
                False,
                "DashboardService.export_dashboard_as_bytesio n'est pas disponible.",
                500,
            )

        image_stream = export_method(
            dashboard
        )

        if image_stream is None:

            return _json_response(
                False,
                "L'export n'a retourné aucune donnée.",
                422,
            )

        image_bytes = image_stream.getvalue()

        image_base64 = (
            base64.b64encode(
                image_bytes
            )
            .decode("utf-8")
        )

    except ValueError as exc:

        return _json_response(
            False,
            str(exc),
            422,
        )

    except Exception as exc:

        print(
            "[DashboardController] "
            "ERREUR EXPORT IMAGE :",
            exc,
        )

        traceback.print_exc()

        return _json_response(
            False,
            "Impossible d'exporter le dashboard.",
            500,
            details=str(exc),
        )

    _audit(
        user_id,
        "dashboard_exported",
        {
            "dashboard_id": _safe_id(
                dashboard_id
            )
        },
    )

    return _json_response(
        True,
        status=200,
        image_base64=image_base64,
    )