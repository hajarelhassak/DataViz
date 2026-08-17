"""
ConnectionService — gestion métier des connexions BDD.

Responsabilités :

- tester une connexion avant sauvegarde ;
- chiffrer les credentials ;
- construire les connecteurs ;
- explorer le schéma ;
- mettre en cache le schéma ;
- gérer les tables autorisées ;
- charger les données des tables autorisées ;
- analyser le schéma avec l'IA ;
- retester une connexion existante ;
- supporter SQLite, MySQL, PostgreSQL et SQL Server.

IMPORTANT :

- les credentials sont chiffrés avant stockage ;
- les mots de passe ne sont jamais retournés au frontend ;
- les lignes brutes ne sont pas envoyées à l'IA ;
- une table doit être explicitement autorisée avant lecture.
"""

from __future__ import annotations

from typing import Any


from connectors.base_connector import (
    UnauthorizedTableAccessError,
)

from connectors.factory import (
    SUPPORTED_ENGINES,
    UnsupportedEngineError,
    create_connector,
)

from models.connection import Connection

from repositories.connection_repository import (
    ConnectionRepository,
)

from services.schema_service import SchemaService
from services.ai_service import AIService

from utils.crypto import (
    decrypt_value,
    encrypt_value,
)


class ConnectionService:
    """
    Service métier central pour les connexions BDD externes.
    """

    # ==========================================================
    # CONSTANTES
    # ==========================================================

    DEFAULT_CONNECT_TIMEOUT = 5
    DEFAULT_DATA_TIMEOUT = 30

    SERVER_ENGINES = {
        "mysql",
        "postgresql",
        "mssql",
    }

    # ==========================================================
    # NORMALISATION MOTEUR
    # ==========================================================

    @staticmethod
    def _normalize_engine_type(
        engine_type: str,
    ) -> str:

        if engine_type is None:
            raise ValueError(
                "Type de base de données obligatoire."
            )

        normalized = str(
            engine_type
        ).strip().lower()

        if not normalized:
            raise ValueError(
                "Type de base de données obligatoire."
            )

        if normalized not in SUPPORTED_ENGINES:

            raise UnsupportedEngineError(
                f"Moteur non supporté : {normalized}. "
                f"Moteurs disponibles : "
                f"{', '.join(sorted(SUPPORTED_ENGINES))}"
            )

        return normalized

    # ==========================================================
    # NORMALISATION PORT
    # ==========================================================

    @staticmethod
    def _normalize_port(
        port: int | str | None,
    ) -> int:

        if port is None:
            raise ValueError(
                "Port obligatoire."
            )

        try:

            normalized_port = int(
                port
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "Le port doit être un nombre."
            ) from exc

        if not 1 <= normalized_port <= 65535:

            raise ValueError(
                "Le port doit être compris "
                "entre 1 et 65535."
            )

        return normalized_port

    # ==========================================================
    # VALIDATION PARAMETRES
    # ==========================================================

    @staticmethod
    def _validate_parameters(
        engine_type: str,
        host: str | None = None,
        port: int | str | None = None,
        database_name: str | None = None,
        username: str | None = None,
        password: str | None = None,
        database_path: str | None = None,
        require_password: bool = False,
    ) -> str:

        engine_type = (
            ConnectionService
            ._normalize_engine_type(
                engine_type
            )
        )

        # ------------------------------------------------------
        # SQLITE
        # ------------------------------------------------------

        if engine_type == "sqlite":

            if not database_path:

                raise ValueError(
                    "Chemin de la base SQLite obligatoire."
                )

            if not str(
                database_path
            ).strip():

                raise ValueError(
                    "Chemin de la base SQLite invalide."
                )

            return engine_type

        # ------------------------------------------------------
        # BASE SERVEUR
        # ------------------------------------------------------

        if not host:

            raise ValueError(
                "Host obligatoire."
            )

        if not str(host).strip():

            raise ValueError(
                "Host invalide."
            )

        if not database_name:

            raise ValueError(
                "Nom de base obligatoire."
            )

        if not str(database_name).strip():

            raise ValueError(
                "Nom de base invalide."
            )

        if not username:

            raise ValueError(
                "Utilisateur obligatoire."
            )

        if not str(username).strip():

            raise ValueError(
                "Utilisateur invalide."
            )

        ConnectionService._normalize_port(
            port
        )

        if require_password:

            if password is None:

                raise ValueError(
                    "Mot de passe obligatoire."
                )

            if not str(password):

                raise ValueError(
                    "Mot de passe obligatoire."
                )

        return engine_type

    # ==========================================================
    # TIMEOUT
    # ==========================================================

    @staticmethod
    def _normalize_timeout(
        timeout: int | str | None,
        default: int,
    ) -> int:

        try:

            normalized_timeout = int(
                timeout
            )

        except (
            TypeError,
            ValueError,
        ):

            normalized_timeout = default

        if normalized_timeout <= 0:
            normalized_timeout = default

        return normalized_timeout

    # ==========================================================
    # CREATION CONNECTEUR DEPUIS PARAMETRES
    # ==========================================================

    @staticmethod
    def _create_connector_from_parameters(
        engine_type: str,
        host: str | None = None,
        port: int | str | None = None,
        database_name: str | None = None,
        username: str | None = None,
        password: str | None = None,
        database_path: str | None = None,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
    ):

        engine_type = (
            ConnectionService
            ._normalize_engine_type(
                engine_type
            )
        )

        timeout = (
            ConnectionService
            ._normalize_timeout(
                connect_timeout,
                ConnectionService.DEFAULT_CONNECT_TIMEOUT,
            )
        )

        # ------------------------------------------------------
        # SQLITE
        # ------------------------------------------------------

        if engine_type == "sqlite":

            if not database_path:

                raise ValueError(
                    "Chemin de la base SQLite obligatoire."
                )

            return create_connector(
                engine_type="sqlite",
                database_path=str(
                    database_path
                ).strip(),
                connect_timeout=timeout,
            )

        # ------------------------------------------------------
        # SERVEUR
        # ------------------------------------------------------

        normalized_port = (
            ConnectionService
            ._normalize_port(
                port
            )
        )

        if not host:
            raise ValueError(
                "Host obligatoire."
            )

        if not database_name:
            raise ValueError(
                "Nom de base obligatoire."
            )

        if not username:
            raise ValueError(
                "Utilisateur obligatoire."
            )

        return create_connector(
            engine_type=engine_type,
            host=str(host).strip(),
            port=normalized_port,
            database_name=str(
                database_name
            ).strip(),
            username=str(
                username
            ).strip(),
            password=password or "",
            connect_timeout=timeout,
        )

    # ==========================================================
    # CONNECTEUR DEPUIS CONNEXION
    # ==========================================================

    @staticmethod
    def _build_connector(
        connection: Connection,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
    ):

        if connection is None:

            raise ValueError(
                "Connexion invalide."
            )

        engine_type = (
            ConnectionService
            ._normalize_engine_type(
                connection.engine_type
            )
        )

        timeout = (
            ConnectionService
            ._normalize_timeout(
                connect_timeout,
                ConnectionService.DEFAULT_CONNECT_TIMEOUT,
            )
        )

        # ------------------------------------------------------
        # SQLITE
        # ------------------------------------------------------

        if engine_type == "sqlite":

            if not connection.database_path:

                raise ValueError(
                    "Le chemin de la base SQLite "
                    "est manquant."
                )

            return (
                ConnectionService
                ._create_connector_from_parameters(
                    engine_type="sqlite",
                    database_path=connection.database_path,
                    connect_timeout=timeout,
                )
            )

        # ------------------------------------------------------
        # SERVEUR
        # ------------------------------------------------------

        if not connection.host:

            raise ValueError(
                "Le host de la connexion est manquant."
            )

        if connection.port is None:

            raise ValueError(
                "Le port de la connexion est manquant."
            )

        if not connection.database_name:

            raise ValueError(
                "Le nom de la base est manquant."
            )

        if not connection.username:

            raise ValueError(
                "L'utilisateur de la connexion est manquant."
            )

        if connection.encrypted_password is None:

            raise ValueError(
                "Le mot de passe chiffré "
                "de la connexion est manquant."
            )

        # ------------------------------------------------------
        # DECHIFFREMENT
        # ------------------------------------------------------

        try:

            password = decrypt_value(
                connection.encrypted_password
            )

        except Exception as exc:

            raise ValueError(
                "Impossible de déchiffrer "
                "le mot de passe de la connexion."
            ) from exc

        # ------------------------------------------------------
        # CONNECTEUR
        # ------------------------------------------------------

        return (
            ConnectionService
            ._create_connector_from_parameters(
                engine_type=engine_type,
                host=connection.host,
                port=connection.port,
                database_name=connection.database_name,
                username=connection.username,
                password=password,
                connect_timeout=timeout,
            )
        )

    # ==========================================================
    # NORMALISATION TEST
    # ==========================================================

    @staticmethod
    def _normalize_test_result(
        result: Any,
    ) -> dict[str, Any]:

        if hasattr(
            result,
            "to_dict",
        ):

            response = result.to_dict()

        elif isinstance(
            result,
            dict,
        ):

            response = dict(
                result
            )

        else:

            response = {
                "success": bool(
                    getattr(
                        result,
                        "success",
                        False,
                    )
                ),
                "message": str(
                    result
                ),
            }

        response["success"] = bool(
            response.get(
                "success",
                False,
            )
        )

        if not response.get(
            "message"
        ):

            response["message"] = (
                "Connexion réussie."
                if response["success"]
                else "Échec de la connexion."
            )

        if "error" not in response:

            response["error"] = (
                None
                if response["success"]
                else response["message"]
            )

        return response

    # ==========================================================
    # TEST CONNEXION PARAMETRES
    # ==========================================================

    @staticmethod
    def test_connection_params(
        engine_type: str,
        host: str | None = None,
        port: int | str | None = None,
        database_name: str | None = None,
        username: str | None = None,
        password: str | None = None,
        database_path: str | None = None,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
    ) -> dict[str, Any]:

        connector = None

        try:

            engine_type = (
                ConnectionService
                ._validate_parameters(
                    engine_type=engine_type,
                    host=host,
                    port=port,
                    database_name=database_name,
                    username=username,
                    password=password,
                    database_path=database_path,
                    require_password=False,
                )
            )

            connector = (
                ConnectionService
                ._create_connector_from_parameters(
                    engine_type=engine_type,
                    host=host,
                    port=port,
                    database_name=database_name,
                    username=username,
                    password=password,
                    database_path=database_path,
                    connect_timeout=connect_timeout,
                )
            )

            result = (
                connector.test_connection()
            )

            return (
                ConnectionService
                ._normalize_test_result(
                    result
                )
            )

        except (
            UnsupportedEngineError,
            ValueError,
        ) as exc:

            return {
                "success": False,
                "message": str(exc),
                "error": str(exc),
            }

        except Exception as exc:

            return {
                "success": False,
                "message": (
                    "Impossible de tester "
                    "la connexion."
                ),
                "error": str(exc),
            }

        finally:

            if connector is not None:

                try:
                    connector.dispose()

                except Exception:
                    pass

    # ==========================================================
    # CREATION CONNEXION
    # ==========================================================

    @staticmethod
    def create_connection(
        project_id: str,
        nom: str,
        engine_type: str,
        host: str | None = None,
        port: int | str | None = None,
        database_name: str | None = None,
        username: str | None = None,
        password: str | None = None,
        database_path: str | None = None,
    ) -> Connection:

        if not project_id:
            raise ValueError(
                "Projet obligatoire."
            )

        project_id = str(
            project_id
        ).strip()

        if not project_id:
            raise ValueError(
                "Identifiant de projet invalide."
            )

        if not nom:
            raise ValueError(
                "Nom de connexion obligatoire."
            )

        nom = str(
            nom
        ).strip()

        if not nom:
            raise ValueError(
                "Nom de connexion invalide."
            )

        engine_type = (
            ConnectionService
            ._validate_parameters(
                engine_type=engine_type,
                host=host,
                port=port,
                database_name=database_name,
                username=username,
                password=password,
                database_path=database_path,
                require_password=False,
            )
        )

        # ------------------------------------------------------
        # SQLITE
        # ------------------------------------------------------

        if engine_type == "sqlite":

            return (
                ConnectionRepository.create(
                    project_id=project_id,
                    nom=nom,
                    engine_type="sqlite",
                    database_path=str(
                        database_path
                    ).strip(),
                )
            )

        # ------------------------------------------------------
        # SERVEUR
        # ------------------------------------------------------

        normalized_port = (
            ConnectionService
            ._normalize_port(
                port
            )
        )

        # ------------------------------------------------------
        # CHIFFREMENT
        # ------------------------------------------------------

        try:

            encrypted_password = (
                encrypt_value(
                    password or ""
                )
            )

        except Exception as exc:

            raise ValueError(
                "Impossible de chiffrer "
                "le mot de passe de la connexion."
            ) from exc

        # ------------------------------------------------------
        # CREATION
        # ------------------------------------------------------

        return (
            ConnectionRepository.create(
                project_id=project_id,
                nom=nom,
                engine_type=engine_type,
                host=str(host).strip(),
                port=normalized_port,
                database_name=str(
                    database_name
                ).strip(),
                username=str(
                    username
                ).strip(),
                encrypted_password=encrypted_password,
            )
        )

    # ==========================================================
    # RETEST
    # ==========================================================

    @staticmethod
    def retest_connection(
        connection: Connection,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
    ) -> dict[str, Any]:

        if connection is None:

            return {
                "success": False,
                "message": "Connexion invalide.",
                "error": "Connexion invalide.",
            }

        connector = None

        try:

            connector = (
                ConnectionService
                ._build_connector(
                    connection,
                    connect_timeout,
                )
            )

            result = (
                connector.test_connection()
            )

            response = (
                ConnectionService
                ._normalize_test_result(
                    result
                )
            )

            success = bool(
                response.get(
                    "success",
                    False,
                )
            )

            try:

                ConnectionRepository.record_test_result(
                    connection,
                    success,
                )

            except Exception:

                # Le résultat réel du test reste valide.
                pass

            return response

        except Exception as exc:

            try:

                ConnectionRepository.record_test_result(
                    connection,
                    False,
                )

            except Exception:
                pass

            return {
                "success": False,
                "message": (
                    "Impossible de tester "
                    "la connexion."
                ),
                "error": str(exc),
            }

        finally:

            if connector is not None:

                try:
                    connector.dispose()

                except Exception:
                    pass

    # ==========================================================
    # EXPLORATION SCHEMA
    # ==========================================================

    @staticmethod
    def explore_schema(
        connection: Connection,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
    ) -> dict[str, Any]:

        if connection is None:

            raise ValueError(
                "Connexion obligatoire."
            )

        connector = None

        try:

            connector = (
                ConnectionService
                ._build_connector(
                    connection,
                    connect_timeout,
                )
            )

            schema = (
                connector.get_schema()
            )

            if schema is None:

                raise ValueError(
                    "Le connecteur n'a retourné "
                    "aucun schéma."
                )

            if not isinstance(
                schema,
                dict,
            ):

                raise ValueError(
                    "Le schéma retourné est invalide."
                )

            schema.setdefault(
                "tables",
                [],
            )

            if not isinstance(
                schema["tables"],
                list,
            ):

                raise ValueError(
                    "Le champ 'tables' du schéma "
                    "doit être une liste."
                )

            # --------------------------------------------------
            # CACHE
            # --------------------------------------------------

            ConnectionRepository.cache_schema(
                connection.id,
                schema,
            )

            return schema

        finally:

            if connector is not None:

                try:
                    connector.dispose()

                except Exception:
                    pass

    # ==========================================================
    # SCHEMA CACHE
    # ==========================================================

    @staticmethod
    def get_cached_schema(
        connection_id: str,
    ) -> dict[str, Any] | None:

        if not connection_id:

            raise ValueError(
                "Identifiant de connexion obligatoire."
            )

        connection_id = str(
            connection_id
        ).strip()

        if not connection_id:

            raise ValueError(
                "Identifiant de connexion invalide."
            )

        schema = (
            ConnectionRepository
            .get_cached_schema(
                connection_id
            )
        )

        if not schema:
            return None

        if not isinstance(
            schema,
            dict,
        ):

            raise ValueError(
                "Le schéma en cache est invalide."
            )

        return schema

    # ==========================================================
    # TABLES SELECTIONNEES
    # ==========================================================

    @staticmethod
    def set_selected_tables(
        connection_id: str,
        table_names: list[str],
    ) -> list[str]:

        if not connection_id:

            raise ValueError(
                "Identifiant de connexion obligatoire."
            )

        connection_id = str(
            connection_id
        ).strip()

        if not connection_id:

            raise ValueError(
                "Identifiant de connexion invalide."
            )

        if not isinstance(
            table_names,
            list,
        ):

            raise ValueError(
                "Les tables doivent être fournies "
                "sous forme de liste."
            )

        # ------------------------------------------------------
        # NETTOYAGE
        # ------------------------------------------------------

        cleaned_tables = []

        for table in table_names:

            if not isinstance(
                table,
                str,
            ):
                continue

            table = table.strip()

            if (
                table
                and table not in cleaned_tables
            ):

                cleaned_tables.append(
                    table
                )

        if not cleaned_tables:

            raise ValueError(
                "Au moins une table doit être sélectionnée."
            )

        # ------------------------------------------------------
        # CONNEXION
        # ------------------------------------------------------

        connection = (
            ConnectionRepository.get_by_id(
                connection_id
            )
        )

        if connection is None:

            raise ValueError(
                "Connexion introuvable."
            )

        # ------------------------------------------------------
        # SCHEMA
        # ------------------------------------------------------

        schema = (
            ConnectionRepository
            .get_cached_schema(
                connection_id
            )
        )

        if not schema:

            raise ValueError(
                "Le schéma de la base n'a pas encore "
                "été exploré."
            )

        # ------------------------------------------------------
        # TABLES DISPONIBLES
        # ------------------------------------------------------

        available_tables = set()

        schema_tables = schema.get(
            "tables",
            [],
        )

        for table in schema_tables:

            if not isinstance(
                table,
                dict,
            ):
                continue

            table_name = (
                table.get("name")
                or table.get("nom")
                or table.get("table_name")
            )

            if table_name:

                available_tables.add(
                    str(
                        table_name
                    ).strip()
                )

        # ------------------------------------------------------
        # TABLES INVALIDES
        # ------------------------------------------------------

        invalid_tables = [
            table
            for table in cleaned_tables
            if table not in available_tables
        ]

        if invalid_tables:

            raise ValueError(
                "Certaines tables sélectionnées "
                "n'existent pas dans le schéma : "
                + ", ".join(
                    invalid_tables
                )
            )

        # ------------------------------------------------------
        # SAUVEGARDE
        # ------------------------------------------------------

        rows = (
            ConnectionRepository
            .set_selected_tables(
                connection_id,
                cleaned_tables,
            )
        )

        result = []

        for row in rows or []:

            table_name = getattr(
                row,
                "table_name",
                None,
            )

            if table_name:

                result.append(
                    str(table_name)
                )

        return result or cleaned_tables

    # ==========================================================
    # TABLES AUTORISEES
    # ==========================================================

    @staticmethod
    def get_selected_tables(
        connection_id: str,
    ) -> set[str]:

        if not connection_id:

            raise ValueError(
                "Identifiant de connexion obligatoire."
            )

        connection_id = str(
            connection_id
        ).strip()

        if not connection_id:

            raise ValueError(
                "Identifiant de connexion invalide."
            )

        return (
            ConnectionRepository
            .get_allowed_tables(
                connection_id
            )
        )

    # ==========================================================
    # DATAFRAME
    # ==========================================================

    @staticmethod
    def load_table_dataframe(
        connection: Connection,
        table_name: str,
        connect_timeout: int = DEFAULT_DATA_TIMEOUT,
    ):

        if connection is None:

            raise ValueError(
                "Connexion obligatoire."
            )

        if not table_name:

            raise ValueError(
                "Nom de table obligatoire."
            )

        table_name = str(
            table_name
        ).strip()

        if not table_name:

            raise ValueError(
                "Nom de table invalide."
            )

        # ------------------------------------------------------
        # WHITELIST
        # ------------------------------------------------------

        allowed_tables = (
            ConnectionService
            .get_selected_tables(
                connection.id
            )
        )

        if not allowed_tables:

            raise UnauthorizedTableAccessError(
                "Aucune table n'est autorisée "
                "pour cette connexion."
            )

        if table_name not in allowed_tables:

            raise UnauthorizedTableAccessError(
                f"La table '{table_name}' "
                "n'est pas autorisée."
            )

        connector = None

        try:

            connector = (
                ConnectionService
                ._build_connector(
                    connection,
                    connect_timeout,
                )
            )

            return (
                connector.read_table_safe(
                    table_name=table_name,
                    allowed_tables=allowed_tables,
                    limit=None,
                    offset=0,
                )
            )

        finally:

            if connector is not None:

                try:
                    connector.dispose()

                except Exception:
                    pass

    # ==========================================================
    # ANALYSE IA DU SCHEMA
    # ==========================================================

    @staticmethod
    def analyze_schema_with_ai(
        connection_id: str,
    ) -> dict[str, Any]:

        # ------------------------------------------------------
        # VALIDATION
        # ------------------------------------------------------

        if not connection_id:

            raise ValueError(
                "Identifiant de connexion obligatoire."
            )

        connection_id = str(
            connection_id
        ).strip()

        if not connection_id:

            raise ValueError(
                "Identifiant de connexion invalide."
            )

        # ------------------------------------------------------
        # CONNEXION
        # ------------------------------------------------------

        connection = (
            ConnectionRepository.get_by_id(
                connection_id
            )
        )

        if connection is None:

            raise ValueError(
                "Connexion introuvable."
            )

        # ------------------------------------------------------
        # SCHEMA
        # ------------------------------------------------------

        schema = (
            ConnectionRepository
            .get_cached_schema(
                connection_id
            )
        )

        if not schema:

            raise ValueError(
                "Aucun schéma disponible pour cette connexion. "
                "Veuillez explorer le schéma avant "
                "l'analyse IA."
            )

        if not isinstance(
            schema,
            dict,
        ):

            raise ValueError(
                "Le schéma disponible est invalide."
            )

        # ------------------------------------------------------
        # CONTEXTE IA
        # ------------------------------------------------------

        try:

            ai_schema_context = (
                SchemaService
                .build_ai_schema_context(
                    schema
                )
            )

        except Exception as exc:

            raise ValueError(
                "Impossible de construire le contexte "
                "du schéma pour l'IA."
            ) from exc

        if not ai_schema_context:

            raise ValueError(
                "Le contexte du schéma généré "
                "pour l'IA est vide."
            )

        # ------------------------------------------------------
        # IA
        # ------------------------------------------------------

        try:

            result = (
                AIService.recommend_kpis(
                    schema=ai_schema_context,
                    connection_id=connection_id,
                )
            )

        except Exception as exc:

            return {
                "success": False,
                "connection_id": connection_id,
                "message": (
                    "L'analyse IA n'a pas pu "
                    "être exécutée."
                ),
                "error": str(exc),
                "statut": "error",
                "schema": schema,
                "domaine_detecte": None,
                "kpi_recommandes": [],
                "graphiques_recommandes": [],
            }

        # ------------------------------------------------------
        # VALIDATION
        # ------------------------------------------------------

        if not isinstance(
            result,
            dict,
        ):

            return {
                "success": False,
                "connection_id": connection_id,
                "message": (
                    "La réponse du service IA "
                    "est invalide."
                ),
                "error": (
                    "Réponse IA non dictionnaire."
                ),
                "statut": "error",
                "schema": schema,
                "domaine_detecte": None,
                "kpi_recommandes": [],
                "graphiques_recommandes": [],
            }

        # ------------------------------------------------------
        # STATUT
        # ------------------------------------------------------

        status = result.get(
            "statut"
        )

        success_value = result.get(
            "success"
        )

        if status is not None:

            ai_success = (
                str(status).lower()
                in {
                    "success",
                    "ok",
                    "completed",
                }
            )

        else:

            ai_success = bool(
                success_value
            )

        # ------------------------------------------------------
        # ECHEC
        # ------------------------------------------------------

        if not ai_success:

            error_message = (
                result.get("erreur")
                or result.get("error")
                or result.get("message")
                or "Erreur inconnue du service IA."
            )

            return {
                "success": False,
                "connection_id": connection_id,
                "message": (
                    "L'analyse IA n'a pas pu "
                    "être exécutée."
                ),
                "error": error_message,
                "statut": status or "error",
                "schema": schema,
                "domaine_detecte": None,
                "kpi_recommandes": [],
                "graphiques_recommandes": [],
            }

        # ------------------------------------------------------
        # RESULTATS
        # ------------------------------------------------------

        domaine = result.get(
            "domaine_detecte"
        )

        kpis = result.get(
            "kpi_recommandes",
            [],
        )

        graphiques = result.get(
            "graphiques_recommandes",
            [],
        )

        if not isinstance(
            kpis,
            list,
        ):

            kpis = []

        if not isinstance(
            graphiques,
            list,
        ):

            graphiques = []

        # ------------------------------------------------------
        # METADATA
        # ------------------------------------------------------

        metadata = (
            ConnectionRepository
            .get_schema_metadata(
                connection_id
            )
        )

        if metadata is None:

            # Normalement impossible après explore_schema(),
            # mais on évite un crash incompréhensible.
            raise ValueError(
                "Les métadonnées du schéma "
                "sont introuvables."
            )

        # ------------------------------------------------------
        # RECOMMANDATION
        # ------------------------------------------------------

        recommendation = {
            "domaine_detecte": domaine,
            "kpi_recommandes": kpis,
            "graphiques_recommandes": graphiques,
        }

        # ------------------------------------------------------
        # SAUVEGARDE
        # ------------------------------------------------------

        if not hasattr(
            metadata,
            "set_ai_recommendation",
        ):

            raise ValueError(
                "Le modèle SchemaMetadata ne possède pas "
                "la méthode set_ai_recommendation()."
            )

        metadata.set_ai_recommendation(
            recommendation
        )

        ConnectionRepository.commit()

        # ------------------------------------------------------
        # REPONSE
        # ------------------------------------------------------

        return {
            "success": True,
            "connection_id": connection_id,
            "message": (
                "Schéma analysé avec succès par l'IA."
            ),
            "statut": "success",
            "domaine_detecte": domaine,
            "kpi_recommandes": kpis,
            "graphiques_recommandes": graphiques,
            "schema": schema,
        }