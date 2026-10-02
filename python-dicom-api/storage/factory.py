"""+--------------------------------------+
               |      storage.config.ConfigFactory    |
               +--------------------------------------+
                                  │
                                  ▼
               +--------------------------------------+
               |       storage.factory.DBFactory      |
               +--------------------------------------+
                                  │
                   ┌──────────────┴──────────────┐
                   │                             │
                   ▼                             ▼
       [ SqlServerAuditAdapter ]      [ PostgresAuditAdapter ]
                   │                             │
                   ▼                             ▼
         SQL Server (Localhost)       PostgreSQL (Container)"""

from logging import config
from typing import Optional

from storage.config import ConfigFactory, SqlServerConfig, PostgresConfig
from storage.base import AuditRepository
from sqlalchemy import create_engine, Engine

from storage.adapters.sqlserver_adapter import SqlServerAuditAdapter
#from storage.adapters.postgres_adapter import PostgresAuditAdapter

class RepositoryFactory:
    """Factory class to create database adapters based on the configured dialect."""

    _engine : Optional[Engine] = None

    @classmethod
    def get_engine(cls) -> Engine:
        """Returns a singleton SQLAlchemy engine based on the configured dialect."""
        if cls._engine is None:
            config = ConfigFactory.get_config()
            connection_url = config.build_connection_url()
            cls._engine = create_engine(connection_url, echo=False, future=True)
        return cls._engine

    @classmethod
    def get_repository(cls) -> AuditRepository:
        """Returns an instance of the appropriate AuditRepository implementation."""
            
        if isinstance(ConfigFactory.get_config(), SqlServerConfig):
            return SqlServerAuditAdapter(cls.get_engine())
        elif isinstance(ConfigFactory.get_config(), PostgresConfig):
           raise NotImplementedError("PostgresAuditAdapter is not yet implemented.")
        else:
            raise ValueError(f"No adapter registered for config type: {type(config)}")
    

