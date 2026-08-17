"""
BaseConnector — interface commune des connecteurs BDD.

Responsabilités :
- cacher SQLAlchemy aux services métier
- gérer création moteur
- tester connexion
- explorer schéma
- lecture sécurisée avec whitelist
"""


from __future__ import annotations

import abc

from typing import Optional

import pandas as pd

from sqlalchemy import (
    create_engine,
    inspect,
    text
)

from sqlalchemy.engine import Engine

from sqlalchemy.exc import (
    OperationalError,
    ProgrammingError,
    DBAPIError
)



class ConnectionTestResult:


    def __init__(
        self,
        success: bool,
        message: str
    ):

        self.success = success
        self.message = message



    def to_dict(self):

        return {
            "success": self.success,
            "message": self.message
        }





class UnauthorizedTableAccessError(Exception):
    pass





class BaseConnector(abc.ABC):


    engine_type = "base"



    def __init__(
        self,
        host=None,
        port=None,
        database_name=None,
        username=None,
        password=None,
        connect_timeout=5
    ):


        self.host = host

        self.port = port

        self.database_name = database_name

        self.username = username

        self.password = password

        self.connect_timeout = connect_timeout


        self._engine: Optional[Engine] = None







    @abc.abstractmethod
    def build_uri(self)->str:
        pass






    def connect_args(self)->dict:

        return {}







    def get_engine(self):


        if self._engine is None:


            self._engine = create_engine(

                self.build_uri(),

                connect_args=self.connect_args(),

                pool_pre_ping=True

            )


        return self._engine







    def test_connection(self):


        try:


            with self.get_engine().connect() as conn:

                conn.execute(
                    text("SELECT 1")
                )


            return ConnectionTestResult(
                True,
                "Connexion réussie."
            )



        except OperationalError:


            return ConnectionTestResult(
                False,
                "Serveur inaccessible."
            )



        except ProgrammingError:


            return ConnectionTestResult(
                False,
                "Erreur SQL ou identifiants invalides."
            )



        except DBAPIError:


            return ConnectionTestResult(
                False,
                "Erreur driver BDD."
            )



        except Exception as exc:


            return ConnectionTestResult(
                False,
                str(exc)
            )







    def get_schema(self):


        inspector = inspect(
            self.get_engine()
        )


        tables = []



        for table_name in inspector.get_table_names():

            columns=[]

            for column in inspector.get_columns(table_name):

                columns.append({
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column.get("nullable", True),
                "primary_key": column.get("primary_key", False)
            })

            tables.append({
                "name": table_name,
                "columns": columns
            })

        return {
        "engine": self.engine_type,
        "tables": tables
    }







    def read_table_safe(

        self,

        table_name:str,

        allowed_tables:set[str],

        limit:int|None=None,

        offset:int=0

    ):


        self._assert_table_allowed(

            table_name,

            allowed_tables

        )


        query = self.build_select_query(

            table_name,

            limit,

            offset

        )


        return pd.read_sql(

            text(query),

            self.get_engine()

        )









    def build_select_query(

        self,

        table_name,

        limit,

        offset

    ):


        table = self._quote_identifier(
            table_name
        )


        query=f"""

        SELECT *

        FROM {table}

        """



        if limit is not None:


            query += self.pagination_clause(

                limit,

                offset

            )


        return query







    def pagination_clause(

        self,

        limit,

        offset

    ):


        return f"""

        LIMIT {limit}

        OFFSET {offset}

        """








    def _assert_table_allowed(

        self,

        table_name,

        allowed_tables

    ):


        if table_name not in allowed_tables:


            raise UnauthorizedTableAccessError(

                f"Table non autorisée : {table_name}"

            )







    @staticmethod
    @abc.abstractmethod
    def _quote_identifier(identifier:str):

        pass






    def dispose(self):


        if self._engine:


            self._engine.dispose()

            self._engine=None