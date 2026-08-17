"""
ProjectController — CRUD des projets (espaces de travail).

NOTE :
JWT temporairement désactivé pour le développement.
Un owner_id de développement est utilisé temporairement.
"""

from flask import Blueprint, jsonify, request

from repositories.project_repository import ProjectRepository


# ==========================================================
# BLUEPRINT
# ==========================================================

project_bp = Blueprint(
    "projects",
    __name__,
    url_prefix="/api/projects",
)


# ==========================================================
# UTILISATEUR TEMPORAIRE DE DEVELOPPEMENT
# ==========================================================

DEV_OWNER_ID = "dev-user"


# ==========================================================
# LISTE DES PROJETS
# ==========================================================

@project_bp.get("")
def list_projects():

    try:

        projects = ProjectRepository.list_for_owner(
            DEV_OWNER_ID
        )

        return jsonify([
            project.to_dict()
            for project in projects
        ]), 200

    except Exception as exc:

        print(
            "Erreur liste projets :",
            exc
        )

        return jsonify({
            "success": False,
            "error": "Impossible de récupérer les projets.",
            "message": str(exc),
        }), 500


# ==========================================================
# CREATION D'UN PROJET
# ==========================================================

@project_bp.post("")
def create_project():

    try:

        payload = (
            request.get_json(silent=True)
            or {}
        )

        nom = payload.get("nom", "")

        if not isinstance(nom, str):

            return jsonify({
                "success": False,
                "error":
                    "Le nom du projet doit être une chaîne.",
            }), 400

        nom = nom.strip()

        if not nom:

            return jsonify({
                "success": False,
                "error":
                    "Le nom du projet est requis.",
            }), 400

        entreprise = payload.get("entreprise")

        project = ProjectRepository.create(
            nom=nom,
            owner_id=DEV_OWNER_ID,
            entreprise=entreprise,
        )

        return jsonify(
            project.to_dict()
        ), 201

    except Exception as exc:

        print(
            "Erreur création projet :",
            exc
        )

        return jsonify({
            "success": False,
            "error":
                "Impossible de créer le projet.",
            "message":
                str(exc),
        }), 500


# ==========================================================
# RECUPERER UN PROJET
# ==========================================================

@project_bp.get("/<project_id>")
def get_project(project_id):

    try:

        project = ProjectRepository.get_by_id(
            project_id
        )

        if project is None:

            return jsonify({
                "success": False,
                "error":
                    "Projet introuvable.",
            }), 404

        return jsonify(
            project.to_dict()
        ), 200

    except Exception as exc:

        print(
            "Erreur récupération projet :",
            exc
        )

        return jsonify({
            "success": False,
            "error":
                "Impossible de récupérer le projet.",
            "message":
                str(exc),
        }), 500


# ==========================================================
# SUPPRIMER UN PROJET
# ==========================================================

@project_bp.delete("/<project_id>")
def delete_project(project_id):

    try:

        project = ProjectRepository.get_by_id(
            project_id
        )

        if project is None:

            return jsonify({
                "success": False,
                "error":
                    "Projet introuvable.",
            }), 404

        ProjectRepository.delete(
            project
        )

        return jsonify({
            "success": True,
            "message":
                "Projet supprimé.",
        }), 200

    except Exception as exc:

        print(
            "Erreur suppression projet :",
            exc
        )

        return jsonify({
            "success": False,
            "error":
                "Impossible de supprimer le projet.",
            "message":
                str(exc),
        }), 500