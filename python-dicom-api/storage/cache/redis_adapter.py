
from .cache import CacheService
from redis import Redis
from typing import Optional,cast,Any
import json


class RedisCacheAdapter(CacheService):
   
    def __init__(self, redis_client: Redis, default_ttl: int = 7200) -> None:
        self.redis =  redis_client
        self.default_ttl = default_ttl

    @staticmethod
    def _frame_key(study_uid: str, frame_id: int) -> str :
        print(f"frame_key = radflow:study:{study_uid}:frame:{frame_id}")
        return f"radflow:study:{study_uid}:frame:{frame_id}"
    
    @staticmethod
    def _manifest_key(study_uid: str) -> str:
        print(f"radflow:study:{study_uid}:manifest")
        return f"radflow:study:{study_uid}:manifest"

    @staticmethod
    def _session_key(session_id: str) -> str:
        print(f"radflow:session:{session_id}")
        return f"radflow:session:{session_id}"

    @staticmethod
    def _study_prefix(study_uid:str) -> str:
        print(f"radflow:study:{study_uid}:*")
        return f"radflow:study:{study_uid}:*"        


    # -------------------------------------------------------------------------
    # Pixel Operations & Predictive Batching
    # -------------------------------------------------------------------------
    def get_frame(self, study_instance_uid:str, frame_id:int) -> Optional[bytes]:
        key = self._frame_key(study_instance_uid,frame_id)
        frame_data = self.redis.get(key)
        return cast(Optional[bytes],frame_data)
        # if frame_data is not None :
        #     self.redis.expire(name=key, time=self.default_ttl)
        # return frame_data

    def set_frame(self, study_instance_uid:str, frame_id:int, frame_data:bytes, ttl:Optional[int] = None) -> None:
        key = self._frame_key(study_instance_uid,frame_id)
        expiration = ttl if ttl is not None else self.default_ttl
        self.redis.set(name=key, value=frame_data, ex=expiration)

    def get_frames_batch(self,study_instance_uid:str, frame_ids:list[int]) -> dict[int, Optional[bytes]]:

        if not frame_ids:
            return {}
         
        keys = [self._frame_key(study_instance_uid,id) for id in frame_ids]
        pipe = self.redis.pipeline()
        pipe.mget(keys)
        # Also refresh the TTL for all keys in the same batch round-trip
        for key in keys:
            pipe.expire(name=key, time=self.default_ttl)

        result = pipe.execute()

        mget_results: list[Optional[bytes]] = result[0] if len(result) > 0 else []
        
        return { 
            frame_id: (frame_data if isinstance(frame_data, bytes) else None) for frame_id, frame_data in zip(frame_ids,mget_results)}          

    # -------------------------------------------------------------------------
    # Manifest Handling
    # -------------------------------------------------------------------------
    def get_manifest(self, study_instance_uid: str) -> Optional[dict[str, Any]]:
        key = self._manifest_key(study_uid=study_instance_uid)
        serialized_manifest = self.redis.get(key)
        if serialized_manifest is None:
            return None

        try:
            return json.loads(serialized_manifest)
        except (json.JSONDecodeError, TypeError):
            return None

    def set_manifest(self, study_instance_uid: str, manifest:dict[str,Any], ttl: Optional[int] = None) -> None:
        mkey = self._manifest_key(study_uid=study_instance_uid)
        expiration = ttl if ttl is not None else self.default_ttl
        
        # Serialize dict to string and encode directly to UTF-8 bytes
        serialized_manifest = json.dumps(manifest,ensure_ascii=False).encode('utf-8')
        self.redis.set(name=mkey, value=serialized_manifest, ex=expiration)
    
    # Session Handling

    def touch_session(self, session_id:str, clinician_id: str, ttl:int = 900) -> None :
        self.redis.set(self._session_key(session_id=session_id),value=clinician_id, ex=ttl)

    def is_session_active(self,session_id:str ) -> bool:
        return self.redis.exists(self._session_key(session_id=session_id)) > 0
            
    # -------------------------------------------------------------------------
    # Eviction & Invalidation
    # -------------------------------------------------------------------------

    def invalidate_study(self, study_instance_uid: str) -> None:
        batch: list[bytes | str] = []
        batch_size = 500
        total_deleted = 0

        for key in self.redis.scan_iter(match=self._study_prefix(study_uid=study_instance_uid)):
            batch.append(key)
            if len(batch) >= batch_size:
                total_deleted += self.redis.delete(*batch)
                batch.clear()

        if batch:
            total_deleted += self.redis.delete(*batch)

        if total_deleted > 0:
            print(f"{total_deleted} keys deleted for study_uid: {study_instance_uid} from Redis.")
        else:
            print(f"No keys found for study_uid: {study_instance_uid}")

    