"""
SchemaValidatorService — validation et nettoyage du schéma BDD.

Responsabilité :

Avant envoi vers l'IA :

BDD
 |
 ↓
SchemaValidatorService
 |
 ↓
Schema propre
 |
 ↓
AIKPISelectorService


Sécurité :
- Aucun enregistrement client.
- Aucun DataFrame.
- Seulement :
    * tables
    * colonnes
    * types
"""

from __future__ import annotations

import re



class SchemaValidationError(Exception):
    pass



class SchemaValidatorService:



    # Types acceptés provenant des connecteurs

    ALLOWED_TYPES = {

        "integer",
        "int",
        "bigint",

        "float",
        "double",
        "decimal",
        "numeric",

        "string",
        "varchar",
        "text",

        "boolean",
        "bool",

        "date",
        "datetime",
        "timestamp"

    }



    @staticmethod
    def validate(
        schema: dict
    ) -> dict:
        """
        Point d'entrée principal.

        Retourne un schéma nettoyé.
        """

        if not schema:

            raise SchemaValidationError(
                "Schéma vide."
            )


        if "tables" not in schema:

            raise SchemaValidationError(
                "Structure du schéma invalide."
            )



        clean_schema = {

            "tables": {}

        }



        for table_name, table_info in schema["tables"].items():


            clean_schema["tables"][
                table_name
            ] = SchemaValidatorService.validate_table(
                table_name,
                table_info
            )


        return clean_schema




    @staticmethod
    def validate_table(
        table_name: str,
        table_info: dict
    ) -> dict:


        if not SchemaValidatorService.is_safe_name(
            table_name
        ):

            raise SchemaValidationError(
                f"Nom de table invalide : {table_name}"
            )



        columns = table_info.get(
            "columns"
        )


        if not columns:

            raise SchemaValidationError(
                f"La table {table_name} ne contient aucune colonne."
            )



        clean_columns = {}



        for column_name, column_type in columns.items():


            if not SchemaValidatorService.is_safe_name(
                column_name
            ):

                continue



            clean_columns[column_name] = (
                SchemaValidatorService.normalize_type(
                    column_type
                )
            )



        return {

            "columns":
                clean_columns

        }




    @staticmethod
    def normalize_type(
        column_type: str
    ) -> str:

        """
        Transforme les types SQL différents
        vers des types compréhensibles par l'IA.
        """

        if not column_type:

            return "unknown"



        value = str(
            column_type
        ).lower()



        if "int" in value:

            return "integer"



        if any(
            x in value
            for x in [
                "float",
                "double",
                "decimal",
                "numeric"
            ]
        ):

            return "float"



        if any(
            x in value
            for x in [
                "date",
                "time"
            ]
        ):

            return "datetime"



        if any(
            x in value
            for x in [
                "bool"
            ]
        ):

            return "boolean"



        if any(
            x in value
            for x in [
                "char",
                "text",
                "varchar"
            ]
        ):

            return "string"



        return "unknown"




    @staticmethod
    def is_safe_name(
        name: str
    ) -> bool:

        """
        Evite les noms SQL suspects.
        """

        if not name:

            return False



        return bool(
            re.match(
                r"^[a-zA-Z0-9_]+$",
                name
            )
        )




    @staticmethod
    def summarize(
        schema: dict
    ) -> dict:

        """
        Génère un résumé léger pour l'IA.
        """

        tables = schema.get(
            "tables",
            {}
        )


        return {

            "nombre_tables":
                len(tables),


            "tables":

                {

                    name:
                    list(
                        info["columns"].keys()
                    )

                    for name, info
                    in tables.items()

                }

        }