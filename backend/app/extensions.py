"""
Instances uniques des extensions Flask.

Les extensions sont créées ici puis initialisées
dans app/__init__.py avec l'application Flask.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# ==========================================================
# EXTENSIONS
# ==========================================================

db = SQLAlchemy()

migrate = Migrate()

jwt = JWTManager()

cors = CORS()

limiter = Limiter(
    key_func=get_remote_address
)


# ==========================================================
# INITIALISATION
# ==========================================================

def init_extensions(app):
    """
    Initialise toutes les extensions Flask
    avec l'application.
    """

    # SQLAlchemy
    db.init_app(app)

    # Flask-Migrate
    migrate.init_app(
        app,
        db
    )

    # JWT
    jwt.init_app(app)

    # CORS
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": app.config.get(
                    "CORS_ORIGINS",
                    ["http://localhost:5173", "http://localhost:5174"]
                ),
                "methods": [
                    "GET",
                    "POST",
                    "PUT",
                    "DELETE",
                    "OPTIONS"
                ],
                "allow_headers": [
                    "Content-Type",
                    "Authorization"
                ]
            }
        }
    )

    # Rate limiting
    limiter.init_app(app)