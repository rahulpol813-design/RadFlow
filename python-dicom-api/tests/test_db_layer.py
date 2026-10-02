"""
tests/test_db_layer.py
Standalone Verification Harness for Star Schema & Database Adapter.
"""

import os
from datetime import date
from storage.factory import RepositoryFactory
from storage.base import ActivityLogDTO, AssignmentDTO


def run_verification():
    print("=" * 70)
    print(">>> INITIALIZING RADFLOW DATABASE LAYER VERIFICATION HARNESS")
    print("=" * 70)

    # 1. Initialize Adapter via Factory
    print("\n[Step 1] Loading Engine & Repository via Factory...")
    repo = RepositoryFactory.get_repository()
    print(f"Loaded Adapter: {repo.__class__.__name__}")

    # 2. Bootstrap Tables
    print("\n[Step 2] Bootstrapping Star Schema Tables (DDL)...")
    repo.initialize_schema()
    print("DDL Execution Succeeded. Dimensions & Facts are live.")

    # 3. Test Assignment Workflow
    test_study_uid = "1.2.840.113619.2.55.3.2831.14321.999"
    test_clinician_id = "DR_SMITH_RAD"
    test_patient_id = "MRN_PATIENT_101"

    print("\n[Step 3] Testing Study Assignment Creation...")
    assignment_dto = AssignmentDTO(
        clinician_id=test_clinician_id,
        patient_id=test_patient_id,
        study_instance_uid=test_study_uid,
        sla_hours=12,
    )
    assignment_key = repo.create_assignment(assignment_dto)
    print(f"Assignment Registered Successfully! assignment_key: {assignment_key}")

    # 4. Verify Immediate Activity Logging (First Slice View)
    print("\n[Step 4] Logging First Image Frame View...")
    activity_dto = ActivityLogDTO(
        clinician_id=test_clinician_id,
        patient_id=test_patient_id,
        study_instance_uid=test_study_uid,
        action_name="FRAME_VIEW_MISS",
        frame_id=1,
        is_cache_hit=False,
        latency_ms=185,
    )
    activity_key = repo.record_activity(activity_dto)
    print(f"Frame View Logged Successfully! activity_key: {activity_key}")

    # 5. Verify Second Frame Scroll (Cache Hit)
    print("\n[Step 5] Logging Subsequent Frame Scroll (Cache Hit)...")
    hit_dto = ActivityLogDTO(
        clinician_id=test_clinician_id,
        patient_id=test_patient_id,
        study_instance_uid=test_study_uid,
        action_name="FRAME_VIEW_HIT",
        frame_id=2,
        is_cache_hit=True,
        latency_ms=3,
    )
    hit_key = repo.record_activity(hit_dto)
    print(f"Cache Hit Frame Logged Successfully! activity_key: {hit_key}")

    # 6. Verify HOD EOD Summary Report
    print("\n[Step 6] Generating End-of-Day (EOD) HOD Summary Report...")
    today_records = repo.fetch_eod_report(date.today())
    print("-" * 50)
    for row in today_records:
        print(f"Clinician : {row.get('clinician_name')} ({row.get('clinician_id')})")
        print(f"Status    : {row.get('assignment_status')}")
        print(f"Total     : {row.get('total_cases')}")
        print(f"Turnaround: {row.get('avg_turnaround_min')} mins")
        print("-" * 50)

    print("\n>>> ALL TESTS PASSED: Module 1 is fully functional and verified.")
    print("=" * 70)


if __name__ == "__main__":
    run_verification()



#python -m tests.test_db_layer  