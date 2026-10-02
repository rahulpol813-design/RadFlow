"""SQL Server-specific query implementations for the audit repository."""
"""          Conceptual Query Blueprint
  ┌────────────────────────────────────────────────────────┐
  │                 storage/queries/sqlserver.py           │
  ├────────────────────────────────────────────────────────┤
  │ • RESOLVE_OR_CREATE_CLINICIAN                          │
  │ • RESOLVE_OR_CREATE_PATIENT                            │
  │ • RESOLVE_OR_CREATE_STUDY                              │
  │ • RESOLVE_OR_CREATE_ACTION_TYPE                        │
  │ • ENSURE_DATE_KEY                                      │
  │ • INSERT_FACT_IMAGE_ACTIVITY (OUTPUT INSERTED.activity_key)
  │ • INSERT_FACT_ASSIGNMENT (OUTPUT INSERTED.assignment_key)
  │ • MARK_ASSIGNMENT_IN_PROGRESS                          │
  │ • GET_EOD_HOD_REPORT (Aggregated status breakdown)     │
  └────────────────────────────────────────────────────────┘"""

"""
storage/queries/sqlserver.py
T-SQL Dialect Queries for RadFlow Star Schema.
"""

# ==============================================================================
# DIMENSION RESOLVERS (GET OR CREATE PATTERN)
# ==============================================================================

RESOLVE_OR_CREATE_CLINICIAN = """
SET NOCOUNT ON;
IF NOT EXISTS (SELECT 1 FROM dim_clinician WHERE clinician_id = :clinician_id)
BEGIN
    INSERT INTO dim_clinician (clinician_id, full_name, role, department, is_active)
    VALUES (:clinician_id, :full_name, :role, :department, 1);
END
SELECT clinician_key FROM dim_clinician WHERE clinician_id = :clinician_id;
"""

RESOLVE_OR_CREATE_PATIENT = """
SET NOCOUNT ON;
IF NOT EXISTS (SELECT 1 FROM dim_patient WHERE patient_id = :patient_id)
BEGIN
    INSERT INTO dim_patient (patient_id, gender, age_bucket)
    VALUES (:patient_id, :gender, :age_bucket);
END
SELECT patient_key FROM dim_patient WHERE patient_id = :patient_id;
"""

RESOLVE_OR_CREATE_STUDY = """
SET NOCOUNT ON;
IF NOT EXISTS (SELECT 1 FROM dim_study WHERE study_instance_uid = :study_instance_uid)
BEGIN
    INSERT INTO dim_study (
        study_instance_uid, modality, series_count, total_frames, 
        accession_number, body_part_examined
    )
    VALUES (
        :study_instance_uid, :modality, :series_count, :total_frames, 
        :accession_number, :body_part_examined
    );
END
SELECT study_key FROM dim_study WHERE study_instance_uid = :study_instance_uid;
"""

RESOLVE_OR_CREATE_ACTION_TYPE = """
SET NOCOUNT ON;
IF NOT EXISTS (SELECT 1 FROM dim_action_type WHERE action_name = :action_name)
BEGIN
    INSERT INTO dim_action_type (action_name, action_category)
    VALUES (:action_name, :action_category);
END
SELECT action_type_key FROM dim_action_type WHERE action_name = :action_name;
"""

ENSURE_DATE_KEY = """
SET NOCOUNT ON;
IF NOT EXISTS (SELECT 1 FROM dim_date WHERE date_key = :date_key)
BEGIN
    INSERT INTO dim_date (date_key, calendar_date, day_of_week, month_name, year, shift_id)
    VALUES (:date_key, :calendar_date, :day_of_week, :month_name, :year, :shift_id);
END
SELECT date_key FROM dim_date WHERE date_key = :date_key;
"""

# ==============================================================================
# FACT INSERTIONS (OUTPUT INSERTED SURROGATE KEYS)
# ==============================================================================

INSERT_FACT_IMAGE_ACTIVITY = """
SET NOCOUNT ON;
INSERT INTO fact_image_activity (
    clinician_key,
    patient_key,
    study_key,
    action_type_key,
    date_key,
    frame_id,
    is_cache_hit,
    latency_ms,
    timestamp
)
OUTPUT INSERTED.activity_key
VALUES (
    :clinician_key,
    :patient_key,
    :study_key,
    :action_type_key,
    :date_key,
    :frame_id,
    :is_cache_hit,
    :latency_ms,
    :timestamp
);
"""

INSERT_FACT_CLINICIAN_ASSIGNMENT = """
SET NOCOUNT ON;
INSERT INTO fact_clinician_assignment (
    clinician_key,
    patient_key,
    study_key,
    assigned_date_key,
    completed_date_key,
    assignment_status,
    first_viewed_at,
    completed_at,
    sla_hours,
    turnaround_minutes
)
OUTPUT INSERTED.assignment_key
VALUES (
    :clinician_key,
    :patient_key,
    :study_key,
    :assigned_date_key,
    NULL,
    'ASSIGNED',
    NULL,
    NULL,
    :sla_hours,
    NULL
);
"""

# ==============================================================================
# WORKFLOW STATE TRANSITIONS
# ==============================================================================

MARK_ASSIGNMENT_IN_PROGRESS = """
SET NOCOUNT ON;
UPDATE fact_clinician_assignment
SET 
    assignment_status = 'IN_PROGRESS',
    first_viewed_at = :first_viewed_at
WHERE study_key = :study_key
  AND clinician_key = :clinician_key
  AND first_viewed_at IS NULL;
"""

# ==============================================================================
# REPORTING & AGGREGATIONS (FOR POWER BI & HOD VIEW)
# ==============================================================================

GET_EOD_HOD_REPORT = """
SET NOCOUNT ON;
SELECT 
    c.clinician_id,
    c.full_name AS clinician_name,
    a.assignment_status,
    COUNT(a.assignment_key) AS total_cases,
    AVG(a.turnaround_minutes) AS avg_turnaround_min
FROM fact_clinician_assignment a
JOIN dim_clinician c ON a.clinician_key = c.clinician_key
WHERE a.assigned_date_key = :date_key
GROUP BY 
    c.clinician_id,
    c.full_name,
    a.assignment_status
ORDER BY 
    c.full_name, 
    a.assignment_status;
"""