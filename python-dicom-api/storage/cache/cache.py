from abc import ABC, abstractmethod
from typing import Optional, Any

class CacheService(ABC):
    
    # Pixel Buffer Operations
    @abstractmethod
    def get_frame(self, study_instance_uid:str, frame_id:int) -> Optional[bytes]:
        """
        Retrieves the raw frame byte payload if present; returns None on cache miss.
        """
        pass   

    @abstractmethod
    def set_frame(self, study_instance_uid:str, frame_id:int, frame_data:bytes, ttl:Optional[int] = None) -> None:
        """
        Stores the frame with an explicit or default sliding TTL (in seconds).
        """
        pass

    @abstractmethod
    def get_frames_batch(self,study_instance_uid:str, frame_ids:list[int]) -> dict[int, Optional[bytes]]:
        """
        Allows pre-fetching consecutive frames (predictive caching for cine/stack scrolls) using multi-key lookups.
        """
        pass

    # Manifest & Metadata Operations
    @abstractmethod
    def get_manifest(self, study_instance_uid: str) -> Optional[dict[str,Any]]:
        """
        Retrieves the study structure (frame counts, photometric interpretation, slice thickness)
        """
        pass

    @abstractmethod
    def set_manifest(self, study_instance_uid: str, manifest:dict[str,Any], ttl: Optional[int] = None) -> None:
        """Saves JSON-serializable study metadata."""
        pass

    # Session & Active Viewer Management
    @abstractmethod
    def touch_session(self, session_id:str, clinician_id: str, ttl:int = 900) -> None :
        """
        Sets or extends the TTL (heartbeat) for an active viewing session.
        """
        pass
   
    @abstractmethod
    def is_session_active(self,session_id:str ) -> bool:
        """
        Checks whether a session token remains unexpired in the cache
        """
        pass

    # Eviction & Invalidation

    @abstractmethod
    def invalidate_study(self, study_instance_uid: str) -> None:
        """
        Purges all cached frames and manifest entries associated with a study when new series are ingested or corrected.
        """
        pass