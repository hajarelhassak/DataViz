"""
Connecteur SQLite.

Utilisation :

- développement
- tests
- démonstration locale
- connexion à une base SQLite existante

Le connecteur utilise SQLAlchemy via BaseConnector.
Les données de la base cliente ne sont pas copiées
dans la base interne de DataViz.
"""

from pathlib import Path

from connectors.base_connector import BaseConnector


class SQLiteConnector(BaseConnector):

    engine_type = "sqlite"

    def __init__(self, database_path: str,connect_timeout: int = 5):

        super().__init__(connect_timeout=connect_timeout)

        if not database_path:
         raise ValueError(
            "Le chemin de la base SQLite est obligatoire."
        )

        self.database_path = str(
          Path(database_path).expanduser()
    )

    # ==========================================================
    # VERIFICATION DU FICHIER
    # ==========================================================

    def _validate_database_path(self):

        path = Path(self.database_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Base SQLite introuvable : {self.database_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Le chemin SQLite n'est pas un fichier : "
                f"{self.database_path}"
            )

    # ==========================================================
    # URI SQLALCHEMY
    # ==========================================================

    def build_uri(self) -> str:

        self._validate_database_path()

        path = Path(
            self.database_path
        ).resolve()

        # SQLAlchemy accepte les chemins absolus
        # sous la forme sqlite:///C:/...
        return f"sqlite:///{path.as_posix()}"

    # ==========================================================
    # ARGUMENTS DE CONNEXION
    # ==========================================================

    def connect_args(self) -> dict:

        return {
            "check_same_thread": False
        }

    # ==========================================================
    # IDENTIFIANT SQL
    # ==========================================================

    @staticmethod
    def _quote_identifier(identifier: str):

        if not identifier:
            raise ValueError(
                "Identifiant SQL vide."
            )

        # Protection contre les injections SQL.
        #
        # On accepte :
        # lettres
        # chiffres
        # underscore
        #
        # Exemple :
        # ventes
        # ventes_2026
        # table1

        if not identifier.replace("_", "").isalnum():

            raise ValueError(
                f"Nom SQL invalide : {identifier}"
            )

        return f'"{identifier}"'