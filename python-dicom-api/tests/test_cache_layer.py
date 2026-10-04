"""
tests/test_cache_layer.py
Standalone Verification Harness for Redis Cache Layer (Frames, Manifests, Sessions).
"""

import sys
import time
from storage.cache.factory import CacheFactory


def run_cache_verification():
    print("=" * 70)
    print(">>> INITIALIZING RADFLOW REDIS CACHE LAYER VERIFICATION HARNESS")
    print("=" * 70)

    # 1. Connectivity Health Check
    print("\n[Step 1] Checking Redis Service Connectivity...")
    if not CacheFactory.ping():
        print("[-] ERROR: Unable to ping Redis. Ensure Redis is running and reachable.")
        sys.exit(1)
    print("[+] Redis Connection Active & Ping Successful.")

    # 2. Retrieve Cache Service Adapter
    print("\n[Step 2] Instantiating CacheService via Factory...")
    cache = CacheFactory.get_cache_service()
    print(f"[+] Loaded Service: {cache.__class__.__name__}")

    # Test Identifiers & Mock Payloads
    test_study_uid = "1.2.840.113619.2.55.3.2831.999.test"
    test_session_id = "test_sess_radiologist_007"
    test_clinician_id = "DR_SMITH_RAD"

    # Simulated raw frame bytes (simulating uncompressed pixel array)
    mock_frame_1_bytes = b"\x00\x01\x02\x03\xFF\xFE\xFD\xFC" * 128
    mock_frame_3_bytes = b"\x10\x20\x30\x40\xAA\xBB\xCC\xDD" * 128

    # 3. Single Frame Set and Get
    print("\n[Step 3] Testing Single Frame Write & Binary Integrity...")
    cache.set_frame(test_study_uid, frame_id=1, frame_data=mock_frame_1_bytes, ttl=300)
    retrieved_frame = cache.get_frame(test_study_uid, frame_id=1)

    assert retrieved_frame is not None, "Failed: Frame 1 returned None on read."
    assert retrieved_frame == mock_frame_1_bytes, "Failed: Binary payload mismatch on frame 1."
    print(f"[+] Frame 1 stored and retrieved successfully ({len(retrieved_frame)} bytes).")

    # 4. Batch Frame Fetch & Miss Handling (Predictive Caching Simulation)
    print("\n[Step 4] Testing Predictive Batch Frame Lookup (Hits vs Misses)...")
    # Frame 1 is seeded; Frame 3 is seeded; Frame 2 is intentionally omitted (cache miss)
    cache.set_frame(test_study_uid, frame_id=3, frame_data=mock_frame_3_bytes, ttl=300)

    batch_result = cache.get_frames_batch(test_study_uid, frame_ids=[1, 2, 3])

    assert 1 in batch_result and batch_result[1] == mock_frame_1_bytes, "Failed: Frame 1 batch retrieval error."
    assert 2 in batch_result and batch_result[2] is None, "Failed: Frame 2 should be None (cache miss)."
    assert 3 in batch_result and batch_result[3] == mock_frame_3_bytes, "Failed: Frame 3 batch retrieval error."
    print("[+] Batch lookup verified: Frame 1 (Hit), Frame 2 (Miss), Frame 3 (Hit).")

    # 5. Study Manifest Storage & Deserialization
    print("\n[Step 5] Testing DICOM Study Manifest Serialization...")
    mock_manifest = {
        "study_instance_uid": test_study_uid,
        "modality": "CT",
        "series_count": 2,
        "total_frames": 512,
        "photometric_interpretation": "MONOCHROME2",
        "rows": 512,
        "columns": 512,
    }
    cache.set_manifest(test_study_uid, manifest=mock_manifest, ttl=300)
    retrieved_manifest = cache.get_manifest(test_study_uid)

    assert retrieved_manifest is not None, "Failed: Manifest retrieved as None."
    assert retrieved_manifest.get("modality") == "CT", "Failed: Manifest content mismatch."
    assert retrieved_manifest.get("total_frames") == 512, "Failed: Manifest frame count mismatch."
    print(f"[+] Manifest stored and parsed successfully: Modality={retrieved_manifest['modality']}, Frames={retrieved_manifest['total_frames']}.")

    # 6. Active Viewer Session & Heartbeat
    print("\n[Step 6] Testing Viewer Session Heartbeat Lifecycle...")
    short_ttl = 2  # 2 seconds TTL for verification
    cache.touch_session(session_id=test_session_id, clinician_id=test_clinician_id, ttl=short_ttl)

    assert cache.is_session_active(test_session_id) is True, "Failed: Session should be active."
    print(f"[+] Active session heartbeat confirmed for clinician: {test_clinician_id}")

    print(f"    Sleeping {short_ttl + 1}s to verify TTL expiration...")
    time.sleep(short_ttl + 1)

    assert cache.is_session_active(test_session_id) is False, "Failed: Session did not expire as expected."
    print("[+] Session expired as expected after TTL passed.")

    # 7. Study Eviction / Invalidation
    print("\n[Step 7] Testing Study-Level Cache Invalidation...")
    # cache.invalidate_study(test_study_uid)

    assert cache.get_frame(test_study_uid, frame_id=1) is None, "Failed: Frame 1 remained after invalidation."
    assert cache.get_frame(test_study_uid, frame_id=3) is None, "Failed: Frame 3 remained after invalidation."
    assert cache.get_manifest(test_study_uid) is None, "Failed: Manifest remained after invalidation."
    print("[+] All cached study frames and manifest entries purged cleanly.")

    print("\n" + "=" * 70)
    print(">>> ALL CACHE TESTS PASSED: L1 Redis Service Layer is functional.")
    print("=" * 70)


if __name__ == "__main__":
    run_cache_verification()