# DB connection parameters, driver strings, env reader

#Objective:
# Create a central configuration module that dynamically determines which dialect to load 
# and constructs the correct connection URL without hardcoding credentials into your application code.

# Enviroment Variables:``
# DB_DIALECT = "mysql"  # Example dialect, can be changed to 'mysql', 'sqlite', etc.
# DB_HOST = "localhost"
# DB_PORT = 1443 # 5432 : PostgreSQL, 1433 : SQL Server
# DB_NAME = "mydatabase"
# DB_USER = "myuser"
# DB_PASSWORD = "mypassword"
# ODBC_DRIVER = "ODBC Driver 17 for SQL Server"  # Example ODBC driver, can be changed based on the database


from abc import abstractmethod
import os

class DatabaseConfig:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")   
        self.port = os.getenv("DB_PORT", None)  # Port can be None for sqlite
        self.username = os.getenv("DB_USER", None)  # Username can be None for sqlite
        self.password = os.getenv("DB_PASSWORD", None)  # Password can be None for
        self.database = os.getenv("DB_NAME", None)  # Database name can be None for sqlite

    @abstractmethod
    def build_connection_url(self) -> str: pass

class SqlServerConfig(DatabaseConfig):
    def __init__(self):
        super().__init__()
        self.driver = os.getenv("ODBC_DRIVER", "ODBC Driver 17 for SQL Server")
        self.port = self.port or 1433  # Default SQL Server port
    def build_connection_url(self) -> str:
        return f"mssql+pyodbc://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?driver={self.driver}&TrustServerCertificate=yes"

class PostgresConfig(DatabaseConfig):
    def __init__(self):
        super().__init__()
        self.port = self.port or 5432  # Default PostgreSQL port
    def build_connection_url(self) -> str:
        return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


#Factory function to get the appropriate database configuration based on the dialect

class ConfigFactory:
    def __init__(self):
        pass

    @staticmethod
    def get_config() -> DatabaseConfig:
        dialect = os.getenv("DB_DIALECT", "sqlite").lower()
        if dialect == "mssql":
            return SqlServerConfig()
        elif dialect == "postgresql":
            return PostgresConfig()
        else:
            raise ValueError(f"Unsupported DB_DIALECT: {dialect}. Supported dialects are 'mssql' and 'postgresql'.")

