"""
ConnectionRepository — accès aux données des connexions BDD.

Responsabilités :

- récupérer une connexion ;
- lister les connexions d'un projet ;
- créer une connexion ;
- supprimer une connexion ;
- enregistrer les résultats de tests ;
- gérer le cache SchemaMetadata ;
- gérer les tables sélectionnées ;
- vérifier les tables autorisées.

Le repository ne contient PAS de logique métier complexe.

Architecture :

Controller
    ↓
Service
    ↓
Repository
    ↓
SQLAlchemy
    ↓
Base interne DataViz
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

from models.connection import (
    Connection,
    SelectedTable,
)

from models.schema_metadata import SchemaMetadata


class ConnectionRepository:
    """
    Repository centralisant les opérations SQLAlchemy
    relatives aux connexions BDD externes.
    """

    # ==========================================================
    # GET BY ID
    # ==========================================================

    @staticmethod
    def get_by_id(connection_id):

        if not connection_id:
            return None

        try:
            return db.session.get(
                Connection,
                connection_id,
            )

        except SQLAlchemyError:
            db.session.rollback()
            raise

    # ==========================================================
    # LIST PROJECT CONNECTIONS
    # ==========================================================

    @staticmethod
    def list_for_project(project_id):

        if not project_id:
            return []

        try:
            query = (
                db.session
                .query(Connection)
                .filter(
                    Connection.project_id == project_id
                )
            )

            if hasattr(
                Connection,
                "created_at",
            ):
                query = query.order_by(
                    Connection.created_at.desc()
                )

            return query.all()

        except SQLAlchemyError:
            db.session.rollback()
            raise

    # ==========================================================
    # CREATE
    # ==========================================================

    @staticmethod
    def create(
        project_id,
        nom,
        engine_type,
        host=None,
        port=None,
        database_name=None,
        username=None,
        encrypted_password=None,
        database_path=None,
    ):

        if not project_id:
            raise ValueError(
                "Identifiant du projet obligatoire."
            )

        if not nom:
            raise ValueError(
                "Nom de connexion obligatoire."
            )

        if not engine_type:
            raise ValueError(
                "Type de moteur obligatoire."
            )

        connection = Connection(
            project_id=project_id,
            nom=nom,
            engine_type=engine_type,
            host=host,
            port=port,
            database_name=database_name,
            username=username,
            encrypted_password=encrypted_password,
            database_path=database_path,
        )

        try:
            db.session.add(connection)
            db.session.commit()
            db.session.refresh(connection)

            return connection

        except SQLAlchemyError:
            db.session.rollback()
            raise

    # ==========================================================
    # DELETE
    # ==========================================================

    @staticmethod
    def delete(connection):

        if connection is None:
            return False

        try:
            db.session.delete(connection)
            db.session.commit()

            return True

        except SQLAlchemyError:
            db.session.rollback()
            raise

    # ==========================================================
    # TEST RESULT
    # ==========================================================

    @staticmethod
    def record_test_result(
        connection,
        success,
    ):

        if connection is None:
            raise ValueError(
                "Connexion introuvable."
            )

        connection.last_test_success = bool(
            success
        )

        connection.last_tested_at = (
            datetime.now(timezone.utc)
        )

        try:
            db.session.commit()

            return connection

        except SQLAlchemyError:
            db.session.rollback()
            raise

    # ==========================================================
    # CACHE SCHEMA
    # ==========================================================

    @staticmethod
    def cache_schema(
        connection_id,
        schema,
    ):

        if not connection_id:
            raise ValueError(
                "Identifiant de connexion obligatoire."
            )

        if not isinstance(schema, dict):
            raise ValueError(
                "Le schéma doit être un dictionnaire."
            )

        connection = (
            ConnectionRepository.get_by_id(
                connection_id
            )
        )

        if connection is None:
            raise ValueError(
                "Connexion introuvable."
            )

        try:
            metadata = (
                db.session
                .query(SchemaMetadata)
                .filter(
                    SchemaMetadata.connection_id
                    == connection_id
                )
                .first()
            )

            if metadata is None:
                metadata = SchemaMetadata(
                    connection_id=connection_id,
                    schema_json="{}",
                )

                db.session.add(metadata)

            metadata.set_schema(schema)

            db.session.commit()

            db.session.refresh(metadata)

            return metadata

        except SQLAlchemyError:
            db.session.rollback()
            raise

    # ==========================================================
    # COMPATIBILITY
    # ==========================================================

    @staticmethod
    def save_schema(
        connection_id,
        schema,
    ):

        return ConnectionRepository.cache_schema(
            connection_id,
            schema,
        )

    # ==========================================================
    # GET CACHED SCHEMA
    # ==========================================================

    @staticmethod
    def get_cached_schema(
        connection_id,
    ):

        if not connection_id:
            return {}

        try:
            metadata = (
                db.session
                .query(SchemaMetadata)
                .filter(
                    SchemaMetadata.connection_id
                    == connection_id
                )
                .first()
            )

            if metadata is None:
                return {}

            return metadata.get_schema()

        except SQLAlchemyError:
            db.session.rollback()
            raise

    # ==========================================================
    # GET SCHEMA METADATA
    # ==========================================================

    @staticmethod
    def get_schema_metadata(
        connection_id,
    ):

        if not connection_id:
            return None

        try:
            return (
                db.session
                .query(SchemaMetadata)
                .filter(
                    SchemaMetadata.connection_id
                    == connection_id
                )
                .first()
            )

        except SQLAlchemyError:
            db.session.rollback()
            raise

    # ==========================================================
    # SELECTED TABLES
    # ==========================================================

    @staticmethod
    def set_selected_tables(
        connection_id,
        table_names,
    ):

        if not connection_id:
            raise ValueError(
                "Identifiant de connexion obligatoire."
            )

        if not isinstance(
            table_names,
            list,
        ):
            raise ValueError(
                "Les tables doivent être fournies sous forme de liste."
            )

        connection = (
            ConnectionRepository.get_by_id(
                connection_id
            )
        )

        if connection is None:
            raise ValueError(
                "Connexion introuvable."
            )

        cleaned_tables = []

        for table_name in table_names:

            if not isinstance(
                table_name,
                str,
            ):
                continue

            table_name = table_name.strip()

            if (
                table_name
                and table_name not in cleaned_tables
            ):
                cleaned_tables.append(
                    table_name
                )

        try:

            (
                db.session
                .query(SelectedTable)
                .filter(
                    SelectedTable.connection_id
                    == connection_id
                )
                .delete(
                    synchronize_session=False
                )
            )

            rows = []

            for table_name in cleaned_tables:

                row = SelectedTable(
                    connection_id=connection_id,
                    table_name=table_name,
                )

                db.session.add(row)

                rows.append(row)

            db.session.commit()

            return rows

        except SQLAlchemyError:
            db.session.rollback()
            raise

    # ==========================================================
    # GET SELECTED TABLES
    # ==========================================================

    @staticmethod
    def get_selected_tables(
        connection_id,
    ):

        if not connection_id:
            return []

        try:
            return (
                db.session
                .query(SelectedTable)
                .filter(
                    SelectedTable.connection_id
                    == connection_id
                )
                .order_by(
                    SelectedTable.table_name.asc()
                )
                .all()
            )

        except SQLAlchemyError:
            db.session.rollback()
            raise

    # ==========================================================
    # ALLOWED TABLES
    # ==========================================================

    @staticmethod
    def get_allowed_tables(
        connection_id,
    ):

        rows = (
            ConnectionRepository
            .get_selected_tables(
                connection_id
            )
        )

        return {
            row.table_name
            for row in rows
            if row.table_name
        }

    # ==========================================================
    # CHECK TABLE
    # ==========================================================

    @staticmethod
    def is_table_allowed(
        connection_id,
        table_name,
    ):

        if not connection_id:
            return False

        if not isinstance(
            table_name,
            str,
        ):
            return False

        normalized_name = table_name.strip()

        if not normalized_name:
            return False

        return (
            normalized_name
            in ConnectionRepository.get_allowed_tables(
                connection_id
            )
        )

    # ==========================================================
    # COMMIT
    # ==========================================================

    @staticmethod
    def commit():

        try:
            db.session.commit()

        except SQLAlchemyError:
            db.session.rollback()
            raise

    # ==========================================================
    # ROLLBACK
    # ==========================================================

    @staticmethod
    def rollback():
        db.session.rollback()

    # ==========================================================
    # REFRESH
    # ==========================================================

    @staticmethod
    def refresh(instance):

        if instance is None:
            return None

        try:
            db.session.refresh(instance)

            return instance

        except SQLAlchemyError:
            db.session.rollback()
            raise