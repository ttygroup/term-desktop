"databases.py - Service to manage database connections and operations."

# python standard library imports
from __future__ import annotations
from typing import TYPE_CHECKING, Sequence, Any, TypedDict  # , Callable
if TYPE_CHECKING:
    from term_desktop.services.servicesmanager import ServicesManager

from contextlib import contextmanager
from pathlib import Path
import sqlite3
# from importlib import resources

# python 3rd party
import platformdirs

# Textual imports
from textual.worker import WorkerError

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
        try:
            self.connection.close()
        except sqlite3.DatabaseError as e:
            self.log.error(f"Error closing database connection: {e}")
            raise e
            
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


    class DatabaseMeta(TypedDict):
        """
        Required keys:
        - db_name: str
        - owner: Any
        """

        db_name: str
        owner: Any
        

    #####################
    # ~ Initialzation ~ #
    #####################

    SERVICE_ID = "database_service"
    
    

    def __init__(self, services_manager: ServicesManager) -> None:
        """
        Initialize the database service
        """
        super().__init__(services_manager)
        
        self.storage_dir = Path(
            platformdirs.user_data_dir(appname="term-desktop", ensure_exists=True)
        )
        self.database_owners: dict[Any, list[str]] = {}
        """Mapping of database owners to a list of their databases."""
        

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
        """Start the Database service."""
        self.log("Starting Database service")

        if True:
            return True
        else:
            return False

    async def stop(self) -> bool:
        self.log("Stopping Database service")
    
        try:    
            for database in self.databases.values():
                database.close()
        except Exception:
            return False
        else:
            return True

    @property
    def databases(self) -> dict[str, DatabaseProcess]:
        """Alias for processes in the Database service."""
        return self.processes

    async def request_database(self, database_meta: DatabaseMeta) -> DatabaseProcess:

        db_name = database_meta["db_name"]
        owner = database_meta["owner"]
        
        db_process = self.databases.get(db_name)
        if db_process is not None:
            # Check owner matches
            if db_name not in self.database_owners[owner]:
                raise RuntimeError(
                    f"Database '{db_name}' is already owned by another owner."
                )
            self.log.debug(f"Database '{db_name}' already loaded. Returning existing instance.")
            return db_process

        # Database not yet loaded in memory, make new connection
        assert self.SERVICE_ID is not None
        worker_meta: ServicesManager.WorkerMeta = {
            "work": self._retrieve_database,
            "name": f"RetrieveDBWorker-{db_name}",
            "service_id": self.SERVICE_ID,
            "group": self.SERVICE_ID,
            "description": f"Retreive {db_name} database.",
            "exit_on_error": False,
            "start": True,
            "exclusive": False,  # numerous DB retrievals can happen simultaneously.
            "thread": False,
        }

        worker = self.run_worker(database_meta, worker_meta=worker_meta)
        try:
            db_process = await worker.wait()
        except WorkerError as e:
            self.log.error(f"Failed to retrieve database {database_meta['db_name']}")
            raise e
        else:
            return db_process


    ################
    # ~ Internal ~ #
    ################
    # Methods that are only used inside this service.
    # These should be marked with a leading underscore.


    async def _retrieve_database(self, database_meta: DatabaseMeta) -> DatabaseProcess:

        db_name = database_meta["db_name"]
        owner = database_meta["owner"]

        self.log.debug(f"Retreiving database '{db_name}' owned by '{owner}'.")
        
        # Stage 1: Create database process
        # If the file already exists, this will connect to it.
        database_process = DatabaseProcess(self.storage_dir, db_name)

        # Stage 2: Add the database process to the process dictionary
        try:
            self._add_process_to_dict(database_process, db_name)
        except RuntimeError as e:
            raise RuntimeError(
                f"Failed to add process {database_process} for database {db_name}. "
                "This might be due to a duplicate process ID."
            ) from e
        else:
            # Stage 3: Register the owner of the database
            if owner not in self.database_owners:
                self.database_owners[owner] = []

            if db_name in self.database_owners[owner]:
                raise RuntimeError(
                    f"Database '{db_name}' is already owned by '{owner}'."
                )

            self.database_owners[owner].append(db_name)
            self.log.info(f"Database '{db_name}' successfully created and ready for use.")
            return database_process


    ################