"databases.py - Service to manage database connections and operations."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING, Sequence, Any
if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager

from contextlib import contextmanager
from pathlib import Path
import sqlite3
# from importlib import resources

# python 3rd party
import platformdirs

# Textual imports
# from textual.widget import Widget

# Textual 3rd party
# None

# Local imports
from term_desktop.services.servicebase import TDEServiceBase
from term_desktop.aceofbase import AceOfBase  # , ProcessType




class DatabaseProcess(AceOfBase):

    def __init__(self, storage_dir: Path, db_name: str) -> None:
        super().__init__()
        self.storage_dir = storage_dir
        self.db_name: str = db_name
        self.db_path: Path = self.storage_dir / self.db_name
        self.connection = sqlite3.connect(self.db_path)

    def close(self) -> None:
        """Close the database connection."""
        self.connection.close()
            
    @contextmanager
    def transaction(self):
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except sqlite3.DatabaseError as e:
            self.log.error(f"Database error: {e}")
            self.connection.rollback()
            raise e
        except Exception as e:
            self.log.error(f"Unexpected error: {e}")
            self.connection.rollback()
            raise e
       
    def execute_script(self, script: str) -> None:
        """Usage:
        ```
        script = "create_table.sql"
        db.execute_script(script)
        ``` """
        
        with self.transaction() as cursor:
            cursor.executescript(script)

    def create_table(self, table: str, columns: dict[str, str]) -> None:
        """Usage:
        ```
        table = "users"
        columns = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT",
            "age": "INTEGER",
            "email": "TEXT"
        }
        db.create_table(table, columns)
        ```
        """

        columns_str = ', '.join([f"{k} {v}" for k, v in columns.items()])
        query = f"CREATE TABLE IF NOT EXISTS {table} ({columns_str});"

        with self.transaction() as cursor:
            cursor.execute(query) 
        
    def insert_one(
        self,
        table: str,
        columns: list[str],
        values: Sequence[Any],
    ) -> None:
        """Usage:
        ```    
        table = "users"
        columns = ["name", "age", "email"]
        values = ["Alice", 30, "alice@example.com"]
        db.insert_one(table, columns, values)
        ```
        In Raw SQL it would look like this:   
        `INSERT INTO users (name, age, email) VALUES (?, ?, ?);`
        """

        placeholders = ", ".join(["?"] * len(values))
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

        with self.transaction() as cursor:
            cursor.execute(query, values)     

    def delete_one(self, table_name: str, column_name: str, value: Any) -> None:
        """Delete a row from a database table.

        EXAMPLE:
        ```
        delete_one('employees', 'id', 3)
        ```
        Raw SQL:   
        `DELETE FROM {table_name} WHERE {column_name} = ?;` 
        """
         
        sql_delete_query = f"DELETE FROM {table_name} WHERE {column_name} = ?;"

        with self.transaction() as cursor:
            cursor.execute(sql_delete_query, (value,))

    def update_column(
            self,
            table_name: str,
            column_name: str,
            new_value: Any,
            condition_column: str,
            condition_value: Any
        ) -> None:
        """Update a column in a database table.
        
        Usage:
        ```
        update_column('employees', 'salary', 75000, 'id', 3)
        ``` 
        Raw SQL:   
        `UPDATE {table_name} SET {column_name} = ? WHERE {condition_column} = ?; `
        """
        
        sql_update_query = f"UPDATE {table_name} SET {column_name} = ? WHERE {condition_column} = ?;"

        with self.transaction() as cursor:
            cursor.execute(sql_update_query, (new_value, condition_value))


    def fetchall(self, query: str, params: Sequence[str] | None = None) -> list[Any]:
        """This method runs a SQL query and retrieves all rows that match the query criteria.
        
        EXAMPLE:
        ```
        users = db.fetchall("SELECT * FROM users WHERE name = ?", ["Alice"])
        ``` 
        Args:
            query (str): The SQL query to run.
            params (Sequence, optional): The query parameters. Defaults to None.

        Returns:
            list[tuple[str]]: A list of rows that match the query criteria.
        """
        
        with self.transaction() as cursor:
            cursor.execute(query, params or [])
            return cursor.fetchall()

    
    def fetchone(self, query: str, params: Sequence[str] | None = None) -> Any:
        """This method is similar to fetchall, but it only retrieves a single row
        from the database, even if multiple rows meet the query criteria.
        
        Example:
        ```
        row = db.fetchone("SELECT * FROM users WHERE name = ?", ["Alice"])
        ``` 
        Args:
            query (str): The SQL query to run.
            params (Sequence, optional): The query parameters. Defaults to None.

        Returns:
            tuple: A single row that matches the query criteria.
        """
        
        with self.transaction() as cursor:
            cursor.execute(query, params or [])
            return cursor.fetchone()


class DatabaseService(TDEServiceBase[DatabaseProcess]):

    #####################
    # ~ Initialzation ~ #
    #####################

    SERVICE_ID = "database_service"

    def __init__(self, services_manager: ServicesManager) -> None:
        """
        Initialize the database service
        """
        super().__init__(services_manager)
        
        self.storage_dir = Path(platformdirs.user_data_dir(appname="term-desktop", ensure_exists=True))
        

    ################
    # ~ Messages ~ #
    ################
    # None yet

    ####################
    # ~ External API ~ #
    ####################
    # Methods that might need to be accessed by
    # anything else in TDE, including other services.

    async def start(self) -> bool:
        """Start the [INSERT SERVICE NAME HERE] service."""
        self.log("Starting Foo service")

        if True:
            return True
        else:
            return False

    async def stop(self) -> bool:
        self.log("Stopping Window service")
        if True:
            return True
        else:
            return False

    ################
    # ~ Internal ~ #
    ################
    # Methods that are only used inside this service.
    # These should be marked with a leading underscore.

    async def request_database(self, db_name: str) -> None:
        pass

        

    ################