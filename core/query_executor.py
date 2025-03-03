from common import QueryConfig
from typing import Dict, List, Any

import psycopg2


class QueryExecutor:
    """
    A class for executing SQL queries using a configured PostgreSQL database connection.
    """

    def __init__(self, config: QueryConfig):
        """
        Initializes the QueryExecutor with a database connection.

        :param config: QueryConfig object containing database settings.
        """
        self.config = config
        self.connection = psycopg2.connect(
            host=self.config.host,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password,
            port=self.config.port,
        )

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Executes an SQL query and returns the results as a list of dictionaries.

        :param query: The SQL query to execute.
        :param params: Optional tuple of query parameters.
        :return: Query result as a list of dictionaries.
        """
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        return results

    def close_connection(self):
        """Closes the database connection."""
        self.connection.close()
