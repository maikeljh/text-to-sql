from contextlib import closing

import psycopg2


class QueryExecutor:
    """
    A class for executing SQL queries using a configured PostgreSQL database connection.
    """

    def __init__(self, config):
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
        self.connection.autocommit = True

    def execute_query(self, query: str, params: tuple = (), timeout: int = 5000) -> list[dict]:
        """
        Executes an SQL query with an optional timeout and returns the results as a list of dictionaries.

        :param query: The SQL query to execute.
        :param params: Optional tuple of query parameters.
        :param timeout: Timeout in milliseconds for the SQL statement.
        :return: Query result as a list of dictionaries.
        """
        with closing(self.connection.cursor()) as cursor:
            try:
                cursor.execute(f"SET statement_timeout = {timeout}")
                cursor.execute(query, params) if params else cursor.execute(query)

                if cursor.description is None:
                    return []

                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            except psycopg2.Error as e:
                print(f"Error executing query: {e}")
                raise

    def close_connection(self):
        """Closes the database connection."""
        self.connection.close()
