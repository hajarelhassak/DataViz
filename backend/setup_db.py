"""
Initialisation de la base de données interne de DataViz.

Cette base contient uniquement les données internes de l'application :
- utilisateurs
- projets
- connexions
- dashboards
- KPI
- métadonnées
- logs
- etc.

Elle est différente des bases clientes connectées par DataViz.
"""

import os
import sys


# ==========================================================
# CHEMIN BACKEND
# ==========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ==========================================================
# APPLICATION FLASK
# ==========================================================

from app import create_app
from app.extensions import db


# ==========================================================
# MODELES
# ==========================================================
#
# IMPORTANT :
# Tous les modèles doivent être importés avant
# db.create_all() afin que SQLAlchemy connaisse
# toutes les tables et toutes les relations.
#

from models.ai_report import AIReport
from models.audit_log import AuditLog
from models.connection import Connection, SelectedTable
from models.dashboard import Dashboard
from models.kpi import KPI
from models.project import Project
from models.role import Role
from models.schema_metadata import SchemaMetadata
from models.user import User


# ==========================================================
# CREATION APPLICATION
# ==========================================================

app = create_app("development")


# ==========================================================
# INITIALISATION BASE DE DONNEES
# ==========================================================

with app.app_context():

    print()
    print("=" * 60)
    print("DATAVIZ - INITIALISATION DE LA BASE DE DONNEES")
    print("=" * 60)

    # ------------------------------------------------------
    # URI DE LA BASE
    # ------------------------------------------------------

    database_uri = app.config.get(
        "SQLALCHEMY_DATABASE_URI"
    )

    print()
    print("Base de données utilisée :")
    print(database_uri)

    # ------------------------------------------------------
    # CREATION DES TABLES
    # ------------------------------------------------------

    print()
    print("Création / vérification des tables...")

    db.create_all()

    print("OK - Tables créées / vérifiées.")

    # ------------------------------------------------------
    # LISTE DES TABLES
    # ------------------------------------------------------

    print()
    print("Tables présentes dans la base :")

    inspector = db.inspect(db.engine)

    tables = inspector.get_table_names()

    if tables:

        for table in tables:
            print(f"  - {table}")

    else:

        print("  Aucune table trouvée.")

    print()
    print("=" * 60)
    print("INITIALISATION TERMINEE")
    print("=" * 60)
    print()