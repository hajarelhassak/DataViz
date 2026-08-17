"""
Connecteur PostgreSQL
"""


from urllib.parse import quote_plus

from connectors.base_connector import BaseConnector





class PostgresConnector(BaseConnector):


    engine_type="postgresql"




    def build_uri(self):


        password=quote_plus(
            self.password
        )


        return (

            f"postgresql+psycopg2://"

            f"{self.username}:{password}"

            f"@{self.host}:{self.port}/"

            f"{self.database_name}"

        )





    def connect_args(self):

        return {

            "connect_timeout":
            self.connect_timeout

        }






    @staticmethod
    def _quote_identifier(identifier):


        if not identifier.replace("_","").isalnum():

            raise ValueError(
                f"Nom SQL invalide : {identifier}"
            )


        return f'"{identifier}"'