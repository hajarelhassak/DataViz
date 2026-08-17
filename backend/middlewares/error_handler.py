"""
Gestionnaire d'erreurs global — évite qu'une stack trace brute (pouvant
contenir des informations sensibles) ne remonte jusqu'au client. Chaque
type d'exception métier est traduit en réponse HTTP propre.
"""
import logging

from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError

from connectors.base_connector import UnauthorizedTableAccessError
from connectors.factory import UnsupportedEngineError
from services.auth_service import AuthenticationError
from utils.crypto import DecryptionError

logger = logging.getLogger("dataviz")


def register_error_handlers(app):
    @app.errorhandler(AuthenticationError)
    def handle_auth_error(exc):
        return jsonify({"error": str(exc)}), 401

    
    @app.errorhandler(UnauthorizedTableAccessError)
    def handle_unauthorized_table(exc):
        return jsonify({"error": str(exc)}), 403

    @app.errorhandler(UnsupportedEngineError)
    def handle_unsupported_engine(exc):
        return jsonify({"error": str(exc)}), 400

    @app.errorhandler(DecryptionError)
    def handle_decryption_error(exc):
        logger.error("Erreur de déchiffrement des credentials : %s", exc)
        return jsonify({"error": "Erreur de configuration interne. Contactez l'administrateur."}), 500

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(exc):
        logger.exception("Erreur base de données interne")
        return jsonify({"error": "Erreur interne de base de données."}), 500

    @app.errorhandler(404)
    def handle_not_found(exc):
        return jsonify({"error": "Ressource introuvable."}), 404

    @app.errorhandler(500)
    def handle_internal_error(exc):
        logger.exception("Erreur interne non gérée")
        return jsonify({"error": "Erreur interne du serveur."}), 500