"""
Factory des connecteurs.
"""

from connectors.base_connector import BaseConnector

from connectors.mysql_connector import MySQLConnector
from connectors.postgres_connector import PostgresConnector
from connectors.mssql_connector import MSSQLConnector
from connectors.sqlite_connector import SQLiteConnector


_CONNECTOR_REGISTRY = {
    "mysql": MySQLConnector,
    "mariadb": MySQLConnector,

    "postgresql": PostgresConnector,
    "postgres": PostgresConnector,

    "sqlserver": MSSQLConnector,
    "mssql": MSSQLConnector,

    "sqlite": SQLiteConnector,
}


SUPPORTED_ENGINES = [
    "mysql",
    "postgresql",
    "sqlserver",
    "sqlite",
]


class UnsupportedEngineError(Exception):
    pass


def create_connector(
    engine_type: str,
    host=None,
    port=None,
    database_name=None,
    username=None,
    password=None,
    database_path=None,
    connect_timeout=5
) -> BaseConnector:

    if not engine_type:
        raise ValueError(
            "Type de base de données obligatoire."
        )

    engine = engine_type.lower().strip()

    connector = _CONNECTOR_REGISTRY.get(engine)

    if connector is None:
        raise UnsupportedEngineError(
            f"{engine_type} non supporté. "
            f"Disponible : {SUPPORTED_ENGINES}"
        )

    # ======================================================
    # SQLITE
    # ======================================================

    if engine == "sqlite":

        if not database_path:
            raise ValueError(
                "database_path obligatoire pour SQLite"
            )

        return connector(
            database_path=database_path,
            connect_timeout=connect_timeout
        )

    # ======================================================
    # BASES SERVEUR
    # ======================================================

    return connector(
        host=host,
        port=port,
        database_name=database_name,
        username=username,
        password=password,
        connect_timeout=connect_timeout
    )