"""
Connecteur SQL Server — utilise pyodbc. Nécessite le driver ODBC
Microsoft installé sur la machine (à documenter dans le manuel
d'installation On-Premise — voir Partie 12 du guide, difficultés connues).

SQL Server ne supporte pas la syntaxe LIMIT/OFFSET de MySQL/PostgreSQL :
on utilise donc OFFSET ... FETCH NEXT ... ROWS ONLY (SQL Server 2012+),
qui nécessite un ORDER BY explicite.
"""
"""
Connecteur SQL Server avec pyodbc.
"""


from urllib.parse import quote_plus

import pandas as pd

from sqlalchemy import text

from connectors.base_connector import BaseConnector





class MSSQLConnector(BaseConnector):


    engine_type="mssql"




    def build_uri(self):


        driver = quote_plus(
            "ODBC Driver 18 for SQL Server"
        )


        password = quote_plus(
            self.password
        )


        return (

            f"mssql+pyodbc://"

            f"{self.username}:{password}"

            f"@{self.host}:{self.port}/"

            f"{self.database_name}"

            f"?driver={driver}"

            f"&TrustServerCertificate=yes"

        )






    def connect_args(self):


        return {

            "timeout":
            self.connect_timeout,

            "login_timeout":
            self.connect_timeout

        }






    @staticmethod
    def _quote_identifier(identifier):


        if not identifier.replace("_","").isalnum():

            raise ValueError(
                f"Nom SQL invalide : {identifier}"
            )


        return f"[{identifier}]"







    def pagination_clause(

        self,

        limit,

        offset

    ):


        return f"""

        ORDER BY (SELECT NULL)

        OFFSET {offset} ROWS

        FETCH NEXT {limit} ROWS ONLY

        """