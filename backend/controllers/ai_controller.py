"""
AIController — gestion des interactions IA de DataViz.

Routes :

POST /api/ai/connections/<connection_id>/recommend
    Analyse le schéma et recommande KPI/graphiques/filtres.

POST /api/ai/dashboards/<dashboard_id>/analyze
    Analyse les KPI calculés d'un dashboard.



IMPORTANT :

- aucune ligne brute de la base cliente n'est envoyée à l'IA
  lors de l'analyse du schéma ;
- le contrôleur délègue la logique métier aux services ;
- les erreurs sont transformées en réponses JSON.
"""

from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
)

from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db

from repositories.connection_repository import (
    ConnectionRepository,
)

from services.ai_service import AIService
from services.audit_service import AuditService
from services.connection_service import ConnectionService


# ==========================================================
# BLUEPRINT
# ==========================================================

ai_bp = Blueprint(
    "ai",
    __name__,
    url_prefix="/api/ai",
)


# ==========================================================
# RECOMMANDATION KPI
# ==========================================================


@ai_bp.post(
    "/connections/<connection_id>/recommend"
)
@jwt_required()
def recommend_kpis(connection_id):
    """
    Analyse le schéma d'une connexion avec l'IA.

    Workflow :

        connexion
            ↓
        schéma en cache
            ↓
        contexte structurel
            ↓
        AIService
            ↓
        recommandations
    """

    # ======================================================
    # VALIDATION ID
    # ======================================================

    connection_id = str(
        connection_id or ""
    ).strip()

    if not connection_id:

        return jsonify({
            "success": False,
            "error": (
                "Identifiant de connexion obligatoire."
            ),
        }), 400

    # ======================================================
    # VERIFICATION CONNEXION
    # ======================================================

    try:

        connection = (
            ConnectionRepository.get_by_id(
                connection_id
            )
        )

    except Exception as exc:

        current_app.logger.exception(
            "[AIController] Erreur récupération connexion"
        )

        return jsonify({
            "success": False,
            "connection_id": connection_id,
            "error": (
                "Impossible de récupérer la connexion."
            ),
            "details": str(exc),
        }), 500

    if connection is None:

        return jsonify({
            "success": False,
            "connection_id": connection_id,
            "error": "Connexion introuvable.",
        }), 404

    # ======================================================
    # VERIFICATION SCHEMA
    # ======================================================

    try:

        schema = (
            ConnectionService.get_cached_schema(
                connection_id
            )
        )

    except ValueError as exc:

        return jsonify({
            "success": False,
            "connection_id": connection_id,
            "error": str(exc),
        }), 400

    except Exception as exc:

        current_app.logger.exception(
            "[AIController] Erreur récupération schéma"
        )

        return jsonify({
            "success": False,
            "connection_id": connection_id,
            "error": (
                "Impossible de récupérer le schéma."
            ),
            "details": str(exc),
        }), 500

    if not schema:

        return jsonify({
            "success": False,
            "connection_id": connection_id,
            "error": (
                "Aucun schéma disponible. "
                "Veuillez explorer la base avant "
                "de lancer l'analyse IA."
            ),
        }), 400

    # ======================================================
    # ANALYSE IA
    # ======================================================

    try:

        result = (
            ConnectionService
            .analyze_schema_with_ai(
                connection_id
            )
        )

    except ValueError as exc:

        return jsonify({
            "success": False,
            "connection_id": connection_id,
            "error": str(exc),
        }), 400

    except Exception as exc:

        current_app.logger.exception(
            "[AIController] Erreur analyse schéma"
        )

        return jsonify({
            "success": False,
            "connection_id": connection_id,
            "error": (
                "Une erreur est survenue "
                "pendant l'analyse IA."
            ),
            "details": str(exc),
        }), 500

    # ======================================================
    # VALIDATION REPONSE
    # ======================================================

    if not isinstance(
        result,
        dict,
    ):

        return jsonify({
            "success": False,
            "connection_id": connection_id,
            "error": (
                "Le service IA a retourné "
                "une réponse invalide."
            ),
        }), 502

    # ======================================================
    # ECHEC IA
    # ======================================================

    if result.get("success") is False:

        return jsonify({
            "success": False,
            "connection_id": connection_id,
            "error": (
                result.get("error")
                or result.get("erreur")
                or result.get("message")
                or "L'analyse IA a échoué."
            ),
            "statut": result.get("statut"),
        }), 502

    # ======================================================
    # AUDIT
    # ======================================================

    try:

        AuditService.log(
            get_jwt_identity(),
            "ai_kpi_recommendation",
            {
                "connection_id": connection_id,
            },
            request.remote_addr,
        )

    except Exception:

        # Une erreur d'audit ne doit jamais
        # faire échouer l'analyse IA.
        current_app.logger.warning(
            "[AIController] Échec journalisation audit",
            exc_info=True,
        )

    # ======================================================
    # REPONSE
    # ======================================================

    response = dict(result)

    response["success"] = True
    response["connection_id"] = connection_id

    return jsonify(
        response
    ), 200


# ==========================================================
# ANALYSE DASHBOARD
# ==========================================================


@ai_bp.post(
    "/dashboards/<dashboard_id>/analyze"
)
@jwt_required()
def analyze_dashboard(dashboard_id):
    """
    Analyse les KPI d'un dashboard existant.
    """

    # Import local pour éviter certains cycles
    # entre modèles et contrôleurs.
    from models.dashboard import Dashboard

    # ======================================================
    # VALIDATION
    # ======================================================

    dashboard_id = str(
        dashboard_id or ""
    ).strip()

    if not dashboard_id:

        return jsonify({
            "success": False,
            "error": (
                "Identifiant du dashboard obligatoire."
            ),
        }), 400

    # ======================================================
    # RECHERCHE
    # ======================================================

    try:

        dashboard = db.session.get(
            Dashboard,
            dashboard_id,
        )

    except Exception as exc:

        current_app.logger.exception(
            "[AIController] Erreur récupération dashboard"
        )

        return jsonify({
            "success": False,
            "dashboard_id": dashboard_id,
            "error": (
                "Impossible de récupérer le dashboard."
            ),
            "details": str(exc),
        }), 500

    if dashboard is None:

        return jsonify({
            "success": False,
            "dashboard_id": dashboard_id,
            "error": "Dashboard introuvable.",
        }), 404

    # ======================================================
    # NOM DASHBOARD
    # ======================================================

    dashboard_name = (
        getattr(
            dashboard,
            "nom",
            None,
        )
        or getattr(
            dashboard,
            "name",
            None,
        )
        or "Dashboard"
    )

    # ======================================================
    # ANALYSE IA
    # ======================================================

    try:

        report = (
            AIService.analyze_dashboard(
                dashboard_id=dashboard.id,
                project_id=dashboard.project_id,
                project_name=dashboard_name,
            )
        )

    except ValueError as exc:

        return jsonify({
            "success": False,
            "dashboard_id": dashboard_id,
            "error": str(exc),
        }), 400

    except Exception as exc:

        current_app.logger.exception(
            "[AIController] Erreur analyse dashboard"
        )

        return jsonify({
            "success": False,
            "dashboard_id": dashboard_id,
            "error": (
                "Une erreur est survenue "
                "pendant l'analyse du dashboard."
            ),
            "details": str(exc),
        }), 500

    # ======================================================
    # VALIDATION REPONSE
    # ======================================================

    if not isinstance(
        report,
        dict,
    ):

        return jsonify({
            "success": False,
            "dashboard_id": dashboard_id,
            "error": (
                "Le service IA a retourné "
                "une réponse invalide."
            ),
        }), 502

    # ======================================================
    # ECHEC IA
    # ======================================================

    if report.get("success") is False:

        return jsonify({
            "success": False,
            "dashboard_id": dashboard_id,
            "error": (
                report.get("error")
                or report.get("erreur")
                or report.get("message")
                or "L'analyse IA a échoué."
            ),
        }), 502

    # ======================================================
    # AUDIT
    # ======================================================

    try:

        AuditService.log(
            get_jwt_identity(),
            "ai_dashboard_analysis",
            {
                "dashboard_id": dashboard_id,
            },
            request.remote_addr,
        )

    except Exception:

        current_app.logger.warning(
            "[AIController] Échec audit dashboard",
            exc_info=True,
        )

    # ======================================================
    # REPONSE
    # ======================================================

    return jsonify({
        "success": True,
        "dashboard_id": dashboard_id,
        **report,
    }), 200


# ==========================================================
# STATUS IA
# ==========================================================


@ai_bp.get(
    "/status"
)
@jwt_required()
def ai_status():
    """
    Vérifie la disponibilité dE GEMINI.
    """

    try:

        status = (
            AIService.check_status()
        )

    except Exception as exc:

        current_app.logger.exception(
            "[AIController] Erreur status IA"
        )

        return jsonify({
            "success": False,
            "available": False,
            "error": (
                "Le service IA est indisponible."
            ),
            "details": str(exc),
        }), 500

    # ======================================================
    # VALIDATION
    # ======================================================

    if not isinstance(
        status,
        dict,
    ):

        return jsonify({
            "success": False,
            "available": False,
            "error": (
                "Réponse invalide du service IA."
            ),
        }), 502

    # ======================================================
    # REPONSE
    # ======================================================

    return jsonify({
        "success": True,
        **status,
    }), 200