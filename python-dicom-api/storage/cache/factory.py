import os
import redis

from pathlib import Path
from dotenv import load_dotenv
from .cache import CacheService 
from storage.cache.redis_adapter import RedisCacheAdapter
from typing import Optional



env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if not env_path.exists():
    env_path = Path.cwd() / ".env"
load_dotenv(dotenv_path=env_path)

class CacheFactory:
    """
    Singleton factory for Redis connection pooling and CacheService instantiation.
    """

    _pool: Optional[redis.ConnectionPool] = None
    _instance: Optional[CacheService] = None

    @classmethod
    def _get_connection_pool(cls) -> redis.ConnectionPool:
        if cls._pool is None:
            host = os.getenv("REDIS_HOST", "127.0.0.1")
            port = int(os.getenv("REDIS_PORT", 6379))
            db = int(os.getenv("REDIS_DB", 0))
            password = os.getenv("REDIS_PASSWORD", None)
            cache_enabled = os.getenv("CACHE_ENABLED")

            cls._pool = redis.ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False,      # Preserve raw binary byte buffers for frames
                socket_timeout=2.0,          # Prevent blocking DICOM threads if Redis hangs
                socket_connect_timeout=2.0,
                max_connections=50,
            )
        return cls._pool

    @classmethod
    def get_cache_service(cls) -> CacheService:
        """
        Returns a singleton instance of RedisCacheAdapter using the shared connection pool.
        """
        if cls._instance is None:
            default_ttl = int(os.getenv("REDIS_DEFAULT_TTL", 7200))
            rediscl = redis.Redis(connection_pool=cls._get_connection_pool())
            cls._instance = RedisCacheAdapter(redis_client=rediscl, default_ttl=default_ttl)
        
        assert cls._instance is not None
        return cls._instance

    @classmethod
    def ping(cls) -> bool:
        """
        Quick health check for service startup / readiness probes.
        """
        try:
            pool = cls._get_connection_pool()
            client = redis.Redis(connection_pool=pool)
            return bool(client.ping())
        except (redis.ConnectionError, redis.TimeoutError):
            return False
    

