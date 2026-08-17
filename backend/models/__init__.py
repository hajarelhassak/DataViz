"""
Chargement centralisé des modèles SQLAlchemy.

Tous les modèles sont importés ici afin que SQLAlchemy
connaisse toutes les classes et puisse résoudre les
relations entre elles avant l'exécution des requêtes.
"""

from models.user import User
from models.role import Role
from models.project import Project
from models.connection import Connection, SelectedTable
from models.schema_metadata import SchemaMetadata
from models.kpi import KPI
from models.dashboard import Dashboard
from models.ai_report import AIReport
from models.audit_log import AuditLog


__all__ = [
    "User",
    "Role",
    "Project",
    "Connection",
    "SelectedTable",
    "SchemaMetadata",
    "KPI",
    "Dashboard",
    "AIReport",
    "AuditLog",
]