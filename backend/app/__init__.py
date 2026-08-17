"""
Initialisation de l'application Flask.

DataViz
"""

from __future__ import annotations

import logging
import os

from logging.handlers import RotatingFileHandler

from flask import Flask

from app.config import config
from app.extensions import init_extensions


def create_app(config_name=None):
    """
    Factory pattern pour créer l'application Flask.
    """

    # ==========================================================
    # DÉTERMINATION DE LA CONFIGURATION
    # ==========================================================

    if config_name is None:
        config_name = os.environ.get(
            "FLASK_ENV",
            "development",
        )

    # ==========================================================
    # VÉRIFICATION CONFIGURATION
    # ==========================================================

    if config_name not in config:
        raise ValueError(
            f"Configuration inconnue : {config_name}"
        )

    # ==========================================================
    # CRÉATION APPLICATION
    # ==========================================================

    app = Flask(__name__)

    # ==========================================================
    # CHARGEMENT CONFIGURATION
    # ==========================================================

    app.config.from_object(
        config[config_name]
    )

    # ==========================================================
    # INITIALISATION EXTENSIONS
    # ==========================================================

    init_extensions(app)

    # ==========================================================
    # CHARGEMENT DES MODÈLES
    #
    # Important :
    # SQLAlchemy doit connaître tous les modèles avant
    # db.create_all() ou avant certaines opérations ORM.
    # ==========================================================

    _import_models()

    # ==========================================================
    # LOGGING
    # ==========================================================

    setup_logging(app)

    # ==========================================================
    # BLUEPRINTS
    # ==========================================================

    register_blueprints(app)

    # ==========================================================
    # ERROR HANDLERS
    # ==========================================================

    register_error_handlers(app)

    # ==========================================================
    # CLI
    # ==========================================================

    register_cli_commands(app)

    # ==========================================================
    # DEBUG
    # ==========================================================

    if app.debug:
        print("======================================")
        print("DATAVIZ - APPLICATION FLASK")
        print("FICHIER APP INIT CHARGE")
        print("CONFIGURATION :", config_name)
        print("ROUTES FLASK :")
        print(app.url_map)
        print("======================================")

    return app


# ==========================================================
# IMPORT DES MODÈLES
# ==========================================================

def _import_models():
    """
    Importe explicitement tous les modèles SQLAlchemy.

    Cela garantit que les classes ORM sont enregistrées
    auprès de SQLAlchemy.
    """

    import models.user  # noqa: F401
    import models.project  # noqa: F401
    import models.connection  # noqa: F401
    import models.schema_metadata  # noqa: F401
    import models.kpi  # noqa: F401
    import models.dashboard  # noqa: F401
    import models.ai_report  # noqa: F401
    import models.audit_log  # noqa: F401
    import models.role  # noqa: F401


# ==========================================================
# LOGGING
# ==========================================================

def setup_logging(app):
    """
    Configure le système de logs de l'application.
    """

    log_level_name = app.config.get(
        "LOG_LEVEL",
        "INFO",
    )

    log_level = getattr(
        logging,
        str(log_level_name).upper(),
        logging.INFO,
    )

    app.logger.setLevel(log_level)

    # ======================================================
    # LOG FILE UNIQUEMENT EN PRODUCTION
    # ======================================================

    if not app.debug:

        log_directory = app.config.get(
            "LOG_DIRECTORY",
            "logs",
        )

        os.makedirs(
            log_directory,
            exist_ok=True,
        )

        log_file = os.path.join(
            log_directory,
            "app.log",
        )

        # Évite les doublons.
        already_configured = any(
            isinstance(
                handler,
                RotatingFileHandler,
            )
            for handler in app.logger.handlers
        )

        if not already_configured:

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=1024 * 1024,
                backupCount=10,
                encoding="utf-8",
            )

            file_handler.setLevel(
                log_level
            )

            formatter = logging.Formatter(
                "%(asctime)s - "
                "%(name)s - "
                "%(levelname)s - "
                "%(message)s"
            )

            file_handler.setFormatter(
                formatter
            )

            app.logger.addHandler(
                file_handler
            )


# ==========================================================
# BLUEPRINTS
# ==========================================================

def register_blueprints(app):
    """
    Enregistre tous les blueprints de l'application.
    """

    from controllers.auth_controller import auth_bp
    from controllers.user_controller import user_bp
    from controllers.project_controller import project_bp
    from controllers.connexion_controller import connection_bp
    from controllers.dashboard_controller import dashboard_bp
    from controllers.ai_controller import ai_bp

    blueprints = [
        auth_bp,
        user_bp,
        project_bp,
        connection_bp,
        dashboard_bp,
        ai_bp,
    ]

    for blueprint in blueprints:
        app.register_blueprint(
            blueprint
        )

    app.logger.info(
        "Blueprints enregistrés avec succès."
    )


# ==========================================================
# ERROR HANDLERS
# ==========================================================

def register_error_handlers(app):
    """
    Enregistre les gestionnaires d'erreurs HTTP.
    """

    @app.errorhandler(404)
    def not_found(error):
        return {
            "success": False,
            "error": "Ressource non trouvée.",
        }, 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return {
            "success": False,
            "error": "Méthode HTTP non autorisée.",
        }, 405

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return {
            "success": False,
            "error": "Requête invalide.",
        }, 422

    @app.errorhandler(500)
    def internal_error(error):

        app.logger.error(
            "Erreur interne : %s",
            error,
            exc_info=True,
        )

        return {
            "success": False,
            "error": "Erreur interne serveur.",
        }, 500


# ==========================================================
# CLI
# ==========================================================

def register_cli_commands(app):
    """
    Enregistre les commandes CLI personnalisées.
    """

    @app.cli.command("create-admin")
    def create_admin():
        """
        Crée un administrateur.

        Cette commande est volontairement conservée comme
        point d'entrée. La logique de création peut être
        ajoutée ensuite selon le modèle User/Role.
        """

        print(
            "Commande création admin."
        )