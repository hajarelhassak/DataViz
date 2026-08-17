"""
ConnectionController — gestion du workflow de connexion
aux bases de données externes.

Workflow :

1. Test de connexion
2. Sauvegarde des credentials
3. Import réel d'un fichier SQLite
4. Exploration du schéma
5. Mise en cache du schéma
6. Sélection des tables pour l'IA
7. Analyse IA du schéma
8. Retest d'une connexion existante

NOTE :
Les routes JWT sont temporairement désactivées pour faciliter
le développement et les tests du workflow principal.
"""

import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from connectors.factory import SUPPORTED_ENGINES
from repositories.connection_repository import ConnectionRepository
from services.audit_service import AuditService
from services.connection_service import ConnectionService


# ==========================================================
# BLUEPRINT
# ==========================================================

connection_bp = Blueprint(
    "connections",
    __name__,
    url_prefix="/api/connections",
)


# ==========================================================
# CONSTANTES
# ==========================================================

ALLOWED_SQLITE_EXTENSIONS = {
    ".db",
    ".sqlite",
    ".sqlite3",
}

SERVER_REQUIRED_FIELDS = {
    "engine_type",
    "host",
    "port",
    "database_name",
    "username",
    "password",
}


# ==========================================================
# UTILITAIRES GENERAUX
# ==========================================================

def _success(data=None, status_code=200, message=None):
    """
    Construit une réponse JSON de succès homogène.
    """

    response = {
        "success": True,
    }

    if message is not None:
        response["message"] = message

    if isinstance(data, dict):
        response.update(data)

    elif data is not None:
        response["data"] = data

    return jsonify(response), status_code


def _error(
    message,
    status_code=400,
    details=None,
):
    """
    Construit une réponse JSON d'erreur homogène.
    """

    response = {
        "success": False,
        "error": message,
    }

    if details is not None:
        response["details"] = details

    return jsonify(response), status_code


# ==========================================================
# IDENTITE UTILISATEUR
# ==========================================================

def _get_current_user_id():
    """
    Retourne l'identité JWT si disponible.

    Les routes n'étant pas encore protégées par JWT pendant
    le développement, toute erreur retourne simplement None.
    """

    try:
        from flask_jwt_extended import get_jwt_identity

        identity = get_jwt_identity()

        return identity

    except Exception:
        return None


# ==========================================================
# AUDIT
# ==========================================================

def _audit(action, data):
    """
    Effectue un audit sans bloquer la requête principale
    si l'audit échoue.
    """

    try:
        AuditService.log(
            _get_current_user_id(),
            action,
            data,
            request.remote_addr,
        )

    except Exception:
        current_app.logger.exception(
            "Erreur lors de l'audit : %s",
            action,
        )


# ==========================================================
# VALIDATION IDENTIFIANTS
# ==========================================================

def _validate_project_id(project_id):
    """
    Vérifie qu'un project_id a été fourni.
    """

    if not project_id:
        return _error(
            "Identifiant du projet obligatoire.",
            400,
        )

    return None


def _validate_connection_id(connection_id):
    """
    Vérifie qu'un connection_id a été fourni.
    """

    if not connection_id:
        return _error(
            "Identifiant de connexion obligatoire.",
            400,
        )

    return None


# ==========================================================
# DOSSIER SQLITE
# ==========================================================

def _get_sqlite_storage_dir():
    """
    Retourne le dossier utilisé pour stocker les fichiers
    SQLite importés définitivement.
    """

    configured_dir = current_app.config.get(
        "SQLITE_STORAGE_DIR"
    )

    if configured_dir:
        storage_dir = Path(configured_dir)

    else:
        storage_dir = (
            Path(current_app.instance_path)
            / "sqlite_databases"
        )

    storage_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return storage_dir.resolve()


# ==========================================================
# VALIDATION EXTENSION SQLITE
# ==========================================================

def _is_valid_sqlite_file(filename):
    """
    Vérifie l'extension du fichier SQLite.
    """

    if not filename:
        return False

    extension = Path(filename).suffix.lower()

    return extension in ALLOWED_SQLITE_EXTENSIONS


# ==========================================================
# SAUVEGARDE SQLITE
# ==========================================================

def _save_sqlite_file(file_storage):
    """
    Sauvegarde un fichier SQLite avec un nom généré côté serveur.

    Retourne :
        str : chemin absolu du fichier sauvegardé.
    """

    if file_storage is None:
        raise ValueError(
            "Aucun fichier SQLite n'a été fourni."
        )

    original_filename = (
        file_storage.filename or ""
    ).strip()

    if not original_filename:
        raise ValueError(
            "Le nom du fichier SQLite est vide."
        )

    if not _is_valid_sqlite_file(
        original_filename
    ):
        raise ValueError(
            "Fichier SQLite invalide. "
            "Extensions autorisées : "
            ".db, .sqlite, .sqlite3."
        )

    storage_dir = _get_sqlite_storage_dir()

    extension = Path(
        original_filename
    ).suffix.lower()

    generated_filename = (
        f"{uuid.uuid4().hex}{extension}"
    )

    destination = (
        storage_dir
        / generated_filename
    )

    file_storage.save(
        str(destination)
    )

    if not destination.exists():
        raise RuntimeError(
            "Le fichier SQLite n'a pas pu être sauvegardé."
        )

    if destination.stat().st_size <= 0:

        try:
            destination.unlink()
        except OSError:
            pass

        raise ValueError(
            "Le fichier SQLite est vide."
        )

    return str(
        destination.resolve()
    )


# ==========================================================
# SUPPRESSION SQLITE
# ==========================================================

def _delete_sqlite_file(database_path):
    """
    Supprime proprement un fichier SQLite.
    """

    if not database_path:
        return

    try:

        path = Path(
            database_path
        )

        if path.exists():
            path.unlink()

            current_app.logger.info(
                "Fichier SQLite supprimé : %s",
                path,
            )

    except Exception:
        current_app.logger.exception(
            "Impossible de supprimer le fichier SQLite : %s",
            database_path,
        )


# ==========================================================
# VALIDATION MOTEUR
# ==========================================================

def _normalize_engine_type(engine_type):
    """
    Normalise le nom du moteur.
    """

    if engine_type is None:
        return ""

    return (
        str(engine_type)
        .strip()
        .lower()
    )


def _validate_engine_type(engine_type):
    """
    Vérifie que le moteur demandé est supporté.

    Retourne :
        None si valide
        tuple Flask si invalide
    """

    normalized_engine = _normalize_engine_type(
        engine_type
    )

    if not normalized_engine:
        return _error(
            "Le type de base de données est obligatoire.",
            400,
        )

    supported_engines = {
        str(engine).lower()
        for engine in SUPPORTED_ENGINES
    }

    if normalized_engine not in supported_engines:
        return _error(
            "Moteur de base de données non supporté.",
            400,
            {
                "supported_engines": sorted(
                    supported_engines
                )
            },
        )

    return None


# ==========================================================
# VALIDATION PAYLOAD SERVEUR
# ==========================================================

def _validate_server_payload(payload):
    """
    Valide les paramètres MySQL/PostgreSQL/SQL Server.
    """

    if not isinstance(payload, dict):
        return _error(
            "Le corps de la requête doit être un objet JSON.",
            400,
        )

    engine_type = _normalize_engine_type(
        payload.get("engine_type")
    )

    if engine_type == "sqlite":
        return _error(
            "SQLite utilise un fichier et non les paramètres "
            "host/port.",
            400,
        )

    missing_fields = []

    for field in SERVER_REQUIRED_FIELDS:

        value = payload.get(field)

        if value is None:
            missing_fields.append(field)
            continue

        if isinstance(value, str):
            if not value.strip():
                missing_fields.append(field)

    if missing_fields:
        return _error(
            "Champs requis manquants.",
            400,
            {
                "missing_fields": missing_fields
            },
        )

    # ------------------------------------------------------
    # VALIDATION PORT
    # ------------------------------------------------------

    try:

        port = int(
            payload["port"]
        )

    except (
        TypeError,
        ValueError,
    ):

        return _error(
            "Le port doit être un nombre.",
            400,
        )

    if port < 1 or port > 65535:
        return _error(
            "Le port doit être compris entre 1 et 65535.",
            400,
        )

    return None


# ==========================================================
# PAYLOAD SQLITE
# ==========================================================

def _get_sqlite_payload_from_request():
    """
    Transforme une requête multipart/form-data
    en payload utilisable par le service.
    """

    engine_type = _normalize_engine_type(
        request.form.get(
            "engine_type"
        )
    )

    nom = (
        request.form.get(
            "nom",
            "SQLite",
        )
        or "SQLite"
    ).strip()

    uploaded_file = request.files.get(
        "file"
    )

    if uploaded_file is None:
        raise ValueError(
            "Aucun fichier SQLite n'a été envoyé."
        )

    return {
        "engine_type": engine_type,
        "nom": nom or "SQLite",
        "file": uploaded_file,
    }


# ==========================================================
# TEST CONNEXION
# ==========================================================

@connection_bp.post("/test")
def test_connection():

    temporary_file = None

    try:

        is_multipart = (
            request.content_type
            and request.content_type.startswith(
                "multipart/form-data"
            )
        )

        # ==================================================
        # SQLITE
        # ==================================================

        if is_multipart:

            payload = (
                _get_sqlite_payload_from_request()
            )

            error = _validate_engine_type(
                payload.get("engine_type")
            )

            if error:
                return error

            engine_type = payload[
                "engine_type"
            ]

            if engine_type != "sqlite":
                return _error(
                    "Le formulaire multipart est réservé à SQLite.",
                    400,
                )

            temporary_file = _save_sqlite_file(
                payload["file"]
            )

            timeout = current_app.config.get(
                "DB_CONNECT_TIMEOUT_SECONDS",
                5,
            )

            result = (
                ConnectionService
                .test_connection_params(
                    engine_type="sqlite",
                    database_path=temporary_file,
                    connect_timeout=timeout,
                )
            )

        # ==================================================
        # MYSQL / POSTGRESQL / SQL SERVER
        # ==================================================

        else:

            payload = (
                request.get_json(
                    silent=True
                )
                or {}
            )

            error = _validate_engine_type(
                payload.get("engine_type")
            )

            if error:
                return error

            error = _validate_server_payload(
                payload
            )

            if error:
                return error

            engine_type = _normalize_engine_type(
                payload["engine_type"]
            )

            port = int(
                payload["port"]
            )

            timeout = current_app.config.get(
                "DB_CONNECT_TIMEOUT_SECONDS",
                5,
            )

            result = (
                ConnectionService
                .test_connection_params(
                    engine_type=engine_type,
                    host=str(
                        payload["host"]
                    ).strip(),
                    port=port,
                    database_name=str(
                        payload["database_name"]
                    ).strip(),
                    username=str(
                        payload["username"]
                    ).strip(),
                    password=payload["password"],
                    connect_timeout=timeout,
                )
            )

        # ==================================================
        # VERIFICATION RESULTAT
        # ==================================================

        if not isinstance(result, dict):
            result = {
                "success": bool(result)
            }

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        # ==================================================
        # AUDIT
        # ==================================================

        _audit(
            "connection_test",
            {
                "engine_type": engine_type,
                "success": success,
            },
        )

        # ==================================================
        # REPONSE
        # ==================================================

        if success:

            return _success(
                {
                    "result": result,
                },
                200,
                "Connexion réussie.",
            )

        return _error(
            result.get(
                "error",
                "La connexion à la base de données a échoué.",
            ),
            400,
            {
                "result": result,
            },
        )

    except ValueError as exc:

        return _error(
            str(exc),
            400,
        )

    except Exception as exc:

        current_app.logger.exception(
            "Erreur test connexion."
        )

        return _error(
            "Erreur lors du test de connexion.",
            500,
            {
                "message": str(exc)
            },
        )

    finally:

        if temporary_file:
            _delete_sqlite_file(
                temporary_file
            )


# ==========================================================
# CREATION CONNEXION
# ==========================================================

@connection_bp.post("/project/<project_id>")
def create_connection(project_id):

    database_path = None
    connection_created = False

    try:

        error = _validate_project_id(
            project_id
        )

        if error:
            return error

        is_multipart = (
            request.content_type
            and request.content_type.startswith(
                "multipart/form-data"
            )
        )

        # ==================================================
        # SQLITE
        # ==================================================

        if is_multipart:

            payload = (
                _get_sqlite_payload_from_request()
            )

            error = _validate_engine_type(
                payload.get("engine_type")
            )

            if error:
                return error

            if payload[
                "engine_type"
            ] != "sqlite":

                return _error(
                    "Le formulaire multipart est réservé à SQLite.",
                    400,
                )

            # ----------------------------------------------
            # IMPORT PERMANENT
            # ----------------------------------------------

            database_path = _save_sqlite_file(
                payload["file"]
            )

            # ----------------------------------------------
            # CREATION
            # ----------------------------------------------

            connection = (
                ConnectionService
                .create_connection(
                    project_id=project_id,
                    nom=payload.get(
                        "nom",
                        "SQLite",
                    ),
                    engine_type="sqlite",
                    database_path=database_path,
                )
            )

            connection_created = True

        # ==================================================
        # BASES SERVEUR
        # ==================================================

        else:

            payload = (
                request.get_json(
                    silent=True
                )
                or {}
            )

            error = _validate_engine_type(
                payload.get("engine_type")
            )

            if error:
                return error

            error = _validate_server_payload(
                payload
            )

            if error:
                return error

            engine_type = _normalize_engine_type(
                payload["engine_type"]
            )

            port = int(
                payload["port"]
            )

            database_name = str(
                payload["database_name"]
            ).strip()

            connection = (
                ConnectionService
                .create_connection(
                    project_id=project_id,
                    nom=(
                        payload.get("nom")
                        or database_name
                    ),
                    engine_type=engine_type,
                    host=str(
                        payload["host"]
                    ).strip(),
                    port=port,
                    database_name=database_name,
                    username=str(
                        payload["username"]
                    ).strip(),
                    password=payload["password"],
                )
            )

            connection_created = True

        # ==================================================
        # AUDIT
        # ==================================================

        _audit(
            "connection_created",
            {
                "connection_id": str(
                    connection.id
                ),
                "engine_type": connection.engine_type,
                "project_id": str(
                    project_id
                ),
            },
        )

        # ==================================================
        # REPONSE
        # ==================================================

        return _success(
            {
                "connection": connection.to_dict()
            },
            201,
            "Connexion créée avec succès.",
        )

    except ValueError as exc:

        if database_path and not connection_created:
            _delete_sqlite_file(
                database_path
            )

        return _error(
            str(exc),
            400,
        )

    except Exception as exc:

        if database_path and not connection_created:
            _delete_sqlite_file(
                database_path
            )

        current_app.logger.exception(
            "Erreur création connexion."
        )

        return _error(
            "Impossible de créer la connexion.",
            500,
            {
                "message": str(exc)
            },
        )


# ==========================================================
# LISTE CONNEXIONS D'UN PROJET
# ==========================================================

@connection_bp.get("/project/<project_id>")
def list_connections(project_id):

    try:

        error = _validate_project_id(
            project_id
        )

        if error:
            return error

        connections = (
            ConnectionRepository
            .list_for_project(
                project_id
            )
        )

        serialized_connections = []

        for connection in connections:

            serialized_connections.append(
                connection.to_dict()
            )

        return _success(
            {
                "connections": serialized_connections,
                "count": len(
                    serialized_connections
                ),
            },
            200,
        )

    except Exception as exc:

        current_app.logger.exception(
            "Erreur récupération connexions "
            "du projet %s.",
            project_id,
        )

        return _error(
            "Impossible de récupérer les connexions.",
            500,
            {
                "message": str(exc)
            },
        )


# ==========================================================
# SUPPRESSION CONNEXION
# ==========================================================

@connection_bp.delete("/<connection_id>")
def delete_connection(connection_id):

    try:

        error = _validate_connection_id(
            connection_id
        )

        if error:
            return error

        # ==================================================
        # RECUPERER LA CONNEXION
        # ==================================================

        connection = (
            ConnectionRepository
            .get_by_id(
                connection_id
            )
        )

        if connection is None:
            return _error(
                "Connexion introuvable.",
                404,
            )

        # ==================================================
        # INFORMATIONS AVANT SUPPRESSION
        # ==================================================

        project_id = connection.project_id
        engine_type = connection.engine_type
        database_path = connection.database_path

        # ==================================================
        # SUPPRESSION BDD INTERNE
        # ==================================================

        ConnectionRepository.delete(
            connection
        )

        # ==================================================
        # SUPPRESSION FICHIER SQLITE
        # ==================================================

        if (
            engine_type == "sqlite"
            and database_path
        ):
            _delete_sqlite_file(
                database_path
            )

        # ==================================================
        # AUDIT
        # ==================================================

        _audit(
            "connection_deleted",
            {
                "connection_id": str(
                    connection_id
                ),
                "project_id": str(
                    project_id
                ),
                "engine_type": engine_type,
            },
        )

        # ==================================================
        # REPONSE
        # ==================================================

        return _success(
            {
                "connection_id": connection_id,
            },
            200,
            "Connexion supprimée avec succès.",
        )

    except Exception as exc:

        current_app.logger.exception(
            "Erreur suppression connexion %s.",
            connection_id,
        )

        return _error(
            "Impossible de supprimer la connexion.",
            500,
            {
                "message": str(exc)
            },
        )


# ==========================================================
# EXPLORATION SCHEMA
# ==========================================================

@connection_bp.post("/<connection_id>/explore")
def explore_schema(connection_id):

    try:

        error = _validate_connection_id(
            connection_id
        )

        if error:
            return error

        connection = (
            ConnectionRepository
            .get_by_id(
                connection_id
            )
        )

        if connection is None:
            return _error(
                "Connexion introuvable.",
                404,
            )

        timeout = current_app.config.get(
            "DB_CONNECT_TIMEOUT_SECONDS",
            5,
        )

        schema = (
            ConnectionService
            .explore_schema(
                connection,
                connect_timeout=timeout,
            )
        )

        # ==================================================
        # CALCUL NOMBRE TABLES
        # ==================================================

        table_count = 0

        if isinstance(
            schema,
            dict,
        ):

            tables = schema.get(
                "tables",
                []
            )

            if isinstance(
                tables,
                list,
            ):
                table_count = len(
                    tables
                )

        # ==================================================
        # AUDIT
        # ==================================================

        _audit(
            "schema_explored",
            {
                "connection_id": str(
                    connection_id
                ),
                "table_count": table_count,
            },
        )

        # ==================================================
        # REPONSE
        # ==================================================

        return _success(
            {
                "connection_id": connection_id,
                "schema": schema,
                "table_count": table_count,
            },
            200,
            "Schéma analysé avec succès.",
        )

    except ValueError as exc:

        return _error(
            str(exc),
            400,
        )

    except Exception as exc:

        current_app.logger.exception(
            "Erreur exploration schéma "
            "connexion %s.",
            connection_id,
        )

        return _error(
            "Impossible d'explorer le schéma.",
            500,
            {
                "message": str(exc)
            },
        )


# ==========================================================
# RECUPERATION SCHEMA CACHE
# ==========================================================

@connection_bp.get("/<connection_id>/schema")
def get_schema(connection_id):

    try:

        error = _validate_connection_id(
            connection_id
        )

        if error:
            return error

        connection = (
            ConnectionRepository
            .get_by_id(
                connection_id
            )
        )

        if connection is None:
            return _error(
                "Connexion introuvable.",
                404,
            )

        schema = (
            ConnectionRepository
            .get_cached_schema(
                connection_id
            )
        )

        if not schema:
            return _error(
                "Aucun schéma disponible. "
                "Veuillez d'abord explorer la base.",
                404,
            )

        return _success(
            {
                "connection_id": connection_id,
                "schema": schema,
            },
            200,
        )

    except Exception as exc:

        current_app.logger.exception(
            "Erreur récupération schéma "
            "connexion %s.",
            connection_id,
        )

        return _error(
            "Impossible de récupérer le schéma.",
            500,
            {
                "message": str(exc)
            },
        )


# ==========================================================
# SAUVEGARDE TABLES SELECTIONNEES
# ==========================================================

@connection_bp.post("/<connection_id>/tables")
def save_selected_tables(connection_id):

    try:

        # ==================================================
        # VERIFICATION CONNEXION
        # ==================================================

        error = _validate_connection_id(
            connection_id
        )

        if error:
            return error

        connection = (
            ConnectionRepository
            .get_by_id(
                connection_id
            )
        )

        if connection is None:
            return _error(
                "Connexion introuvable.",
                404,
            )

        # ==================================================
        # PAYLOAD
        # ==================================================

        payload = (
            request.get_json(
                silent=True
            )
            or {}
        )

        tables = payload.get(
            "tables"
        )

        if not isinstance(
            tables,
            list,
        ):
            return _error(
                "Le champ 'tables' doit être une liste.",
                400,
            )

        # ==================================================
        # NETTOYAGE
        # ==================================================

        cleaned_tables = []

        for table in tables:

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
            return _error(
                "Veuillez sélectionner au moins une table.",
                400,
            )

        # ==================================================
        # RECUPERATION SCHEMA
        # ==================================================

        cached_schema = (
            ConnectionRepository
            .get_cached_schema(
                connection_id
            )
        )

        if not cached_schema:
            return _error(
                "Le schéma de la base n'a pas encore été exploré.",
                400,
            )

        # ==================================================
        # TABLES DISPONIBLES
        # ==================================================

        available_tables = set()

        schema_tables = (
            cached_schema.get(
                "tables",
                []
            )
            if isinstance(
                cached_schema,
                dict,
            )
            else []
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
                    str(table_name)
                )

        # ==================================================
        # VALIDATION
        # ==================================================

        invalid_tables = [
            table
            for table in cleaned_tables
            if table not in available_tables
        ]

        if invalid_tables:
            return _error(
                "Certaines tables sélectionnées "
                "n'existent pas dans le schéma.",
                400,
                {
                    "invalid_tables": invalid_tables,
                    "available_tables": sorted(
                        available_tables
                    ),
                },
            )

        # ==================================================
        # SAUVEGARDE
        # ==================================================

        selected_rows = (
            ConnectionRepository
            .set_selected_tables(
                connection_id=connection_id,
                table_names=cleaned_tables,
            )
        )

        # ==================================================
        # AUDIT
        # ==================================================

        _audit(
            "tables_selected",
            {
                "connection_id": str(
                    connection_id
                ),
                "project_id": str(
                    connection.project_id
                ),
                "table_count": len(
                    cleaned_tables
                ),
            },
        )

        # ==================================================
        # REPONSE
        # ==================================================

        return _success(
            {
                "connection_id": connection_id,
                "tables": cleaned_tables,
                "table_count": len(
                    cleaned_tables
                ),
                "saved_count": len(
                    selected_rows
                ),
            },
            200,
            "Tables sélectionnées enregistrées avec succès.",
        )

    except ValueError as exc:

        return _error(
            str(exc),
            400,
        )

    except Exception as exc:

        current_app.logger.exception(
            "Erreur sauvegarde tables sélectionnées."
        )

        return _error(
            "Impossible d'enregistrer les tables sélectionnées.",
            500,
            {
                "message": str(exc)
            },
        )


# ==========================================================
# ANALYSE IA
# ==========================================================

@connection_bp.post("/<connection_id>/analyze")
def analyze_schema(connection_id):

    try:

        error = _validate_connection_id(
            connection_id
        )

        if error:
            return error

        connection = (
            ConnectionRepository
            .get_by_id(
                connection_id
            )
        )

        if connection is None:
            return _error(
                "Connexion introuvable.",
                404,
            )

        # ==================================================
        # ANALYSE
        # ==================================================

        result = (
            ConnectionService
            .analyze_schema_with_ai(
                connection_id
            )
        )

        # ==================================================
        # AUDIT
        # ==================================================

        _audit(
            "schema_ai_analysis",
            {
                "connection_id": str(
                    connection_id
                ),
            },
        )

        # ==================================================
        # REPONSE
        # ==================================================

        if isinstance(
            result,
            dict,
        ):

            return _success(
                {
                    "connection_id": connection_id,
                    "analysis": result,
                },
                200,
                "Analyse IA terminée avec succès.",
            )

        return _success(
            {
                "connection_id": connection_id,
                "analysis": result,
            },
            200,
            "Analyse IA terminée avec succès.",
        )

    except ValueError as exc:

        return _error(
            str(exc),
            400,
        )

    except Exception as exc:

        current_app.logger.exception(
            "Erreur analyse IA connexion %s.",
            connection_id,
        )

        return _error(
            "Erreur lors de l'analyse IA.",
            500,
            {
                "message": str(exc)
            },
        )


# ==========================================================
# RETEST CONNEXION
# ==========================================================

@connection_bp.post("/<connection_id>/retest")
def retest_connection(connection_id):

    try:

        error = _validate_connection_id(
            connection_id
        )

        if error:
            return error

        connection = (
            ConnectionRepository
            .get_by_id(
                connection_id
            )
        )

        if connection is None:
            return _error(
                "Connexion introuvable.",
                404,
            )

        timeout = current_app.config.get(
            "DB_CONNECT_TIMEOUT_SECONDS",
            5,
        )

        result = (
            ConnectionService
            .retest_connection(
                connection,
                connect_timeout=timeout,
            )
        )

        if not isinstance(
            result,
            dict,
        ):
            result = {
                "success": bool(result)
            }

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        # ==================================================
        # AUDIT
        # ==================================================

        _audit(
            "connection_retest",
            {
                "connection_id": str(
                    connection_id
                ),
                "success": success,
            },
        )

        # ==================================================
        # REPONSE
        # ==================================================

        if success:

            return _success(
                {
                    "connection_id": connection_id,
                    "result": result,
                },
                200,
                "Connexion valide.",
            )

        return _error(
            result.get(
                "error",
                "La connexion a échoué.",
            ),
            400,
            {
                "result": result,
            },
        )

    except ValueError as exc:

        return _error(
            str(exc),
            400,
        )

    except Exception as exc:

        current_app.logger.exception(
            "Erreur retest connexion %s.",
            connection_id,
        )

        return _error(
            "Impossible de tester la connexion.",
            500,
            {
                "message": str(exc)
            },
        )