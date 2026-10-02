# DB connection parameters, driver strings, env reader

#Objective:
# Create a central configuration module that dynamically determines which dialect to load 
# and constructs the correct connection URL without hardcoding credentials into your application code.

import os
import urllib.parse
from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Search current directory and root directory for .env
env_path = Path(__file__).resolve().parent.parent / ".env"
if not env_path.exists():
    env_path = Path.cwd() / ".env"
print(f"[DEBUG] Loading environment variables from: {env_path}")    
load_dotenv(dotenv_path=env_path)


class DatabaseConfig(ABC):
    def __init__(self) -> None:
        self.host: str = os.getenv("DB_HOST", "127.0.0.1")
        raw_port = os.getenv("DB_PORT")
        self.port: Optional[int] = int(raw_port) if raw_port else 1434
        self.username: Optional[str] = os.getenv("DB_USER")
        self.password: Optional[str] = os.getenv("DB_PASSWORD")
        self.database: str = os.getenv("DB_NAME", "radflow")

    @abstractmethod
    def build_connection_url(self) -> str:
        pass


class SqlServerConfig(DatabaseConfig):
    def __init__(self) -> None:
        super().__init__()
        self.driver: str = os.getenv("ODBC_DRIVER", "ODBC Driver 17 for SQL Server")
        self.trusted_connection: str = os.getenv("DB_TRUSTED_CONNECTION", "yes").lower()
    
    def build_connection_url(self) -> str:
        # Default to (local) which uses Shared Memory IPC
        server_target = self.host if self.host and self.host != "127.0.0.1" else "(local)"

        is_trusted = self.trusted_connection in ("yes", "true", "1")

        if is_trusted:
            odbc_str = (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={server_target};"
                f"DATABASE={self.database};"
                "Trusted_Connection=yes;"
                "TrustServerCertificate=yes;"
            )
        else:
            odbc_str = (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={server_target};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
                "TrustServerCertificate=yes;"
            )

        print(f"\n[DEBUG] Connecting via SQL Auth: DRIVER={{{self.driver}}};SERVER={server_target};DATABASE={self.database};UID={self.username};TrustServerCertificate=yes;\n")
        encoded_odbc = urllib.parse.quote_plus(odbc_str)
        return f"mssql+pyodbc:///?odbc_connect={encoded_odbc}"

class PostgresConfig(DatabaseConfig):
    def __init__(self) -> None:
        super().__init__()
        self.port = self.port or 5432

    def build_connection_url(self) -> str:
        user = urllib.parse.quote_plus(self.username) if self.username else ""
        pwd = f":{urllib.parse.quote_plus(self.password)}" if self.password else ""
        creds = f"{user}{pwd}@" if user else ""
        return f"postgresql+psycopg2://{creds}{self.host}:{self.port}/{self.database}"


class ConfigFactory:
    @staticmethod
    def get_config() -> DatabaseConfig:
        dialect = os.getenv("DB_DIALECT", "mssql").lower()
        if dialect in ("mssql", "sqlserver"):
            return SqlServerConfig()
        elif dialect in ("postgresql", "postgres"):
            return PostgresConfig()
        else:
            raise ValueError(
                f"Unsupported DB_DIALECT: '{dialect}'. "
                f"Supported dialects are 'mssql' and 'postgresql'."
            )