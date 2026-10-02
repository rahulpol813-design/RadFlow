"""┌────────────────────────────────────────────────────────┐
 │               <<Interface>> AuditRepository            │
 └───────────────────────────▲────────────────────────────┘
                             │
                             │ implements
 ┌───────────────────────────┴────────────────────────────┐
 │                  SqlServerAuditAdapter                 │
 ├────────────────────────────────────────────────────────┤
 │ - engine: sqlalchemy.Engine                            │
 ├────────────────────────────────────────────────────────┤
 │ + __init__(engine: Engine)                             │
 │ + initialize_schema() -> None                          │
 │ - _resolve_date_key(conn, dt: datetime) -> int         │
 │ - _resolve_clinician_key(conn, clinician_id: str) ->int│
 │ - _resolve_patient_key(conn, patient_id: str) -> int   │
 │ - _resolve_study_key(conn, study_uid: str) -> int      │
 │ - _resolve_action_key(conn, action_name: str) -> int   │
 │ + record_activity(log_dto: ActivityLogDTO) -> int      │
 │ + create_assignment(assignment_dto: AssignmentDTO)->int│
 │ + record_first_viewed(study_uid, clinician_id) -> None │
 │ + fetch_eod_report(date_val: Optional[date]) -> list   │
 └────────────────────────────────────────────────────────┘"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime, timezone

from sqlalchemy import text, Engine
from sqlalchemy.orm import Session
from storage.base import AuditRepository, ActivityLogDTO, AssignmentDTO
from storage.models import Base

import storage.models.dimensions  # noqa: F401
import storage.models.facts       # noqa: F401
import storage.queries.sqlserver as sql_queries

class SqlServerAuditAdapter(AuditRepository):
    """SQL Server implementation of the AuditRepository interface."""

    def __init__(self, engine: Engine):
        self.engine: Engine = engine

    # -------------------------------------------------------------------------
    # Public Abstract Repository Operations
    # -------------------------------------------------------------------------
    
    def initialize_schema(self) -> None:
        Base.metadata.create_all(bind=self.engine)

    def record_activity(self, log_dto: ActivityLogDTO) -> int:
        """
        Resolves dimension keys in an atomic transaction and inserts into
        fact_image_activity, returning the generated activity_key.
        """
        now = datetime.now(timezone.utc)

        with self.engine.begin() as conn:
            clinician_key = self._resolve_clinician_key(conn, log_dto.clinician_id)
            patient_key = self._resolve_patient_key(conn, log_dto.patient_id)
            study_key = self._resolve_study_key(conn, log_dto.study_instance_uid)
            action_type_key = self._resolve_action_key(conn, log_dto.action_name)
            date_key = self._resolve_date_key(conn, now)

            params = {
                "clinician_key": clinician_key,
                "patient_key": patient_key,
                "study_key": study_key,
                "action_type_key": action_type_key,
                "date_key": date_key,
                "frame_id": log_dto.frame_id,
                "is_cache_hit": 1 if log_dto.is_cache_hit else 0,
                "latency_ms": log_dto.latency_ms,
                "timestamp": now,
            }

            res = conn.execute(text(sql_queries.INSERT_FACT_IMAGE_ACTIVITY), params)
            activity_key = res.scalar_one()

            # Auto-trigger check: If study is assigned, mark viewed on first slice access
            conn.execute(
                text(sql_queries.MARK_ASSIGNMENT_IN_PROGRESS),
                {
                    "study_key": study_key,
                    "clinician_key": clinician_key,
                    "first_viewed_at": now,
                },
            )

            return activity_key

    def create_assignment(self, assignment_dto: AssignmentDTO) -> int:
        """
        Assigns a study to a clinician and records it in fact_clinician_assignment.
        """
        now = datetime.now(timezone.utc)

        with self.engine.begin() as conn:
            clinician_key = self._resolve_clinician_key(conn, assignment_dto.clinician_id)
            patient_key = self._resolve_patient_key(conn, assignment_dto.patient_id)
            study_key = self._resolve_study_key(conn, assignment_dto.study_instance_uid)
            assigned_date_key = self._resolve_date_key(conn, now)

            params = {
                "clinician_key": clinician_key,
                "patient_key": patient_key,
                "study_key": study_key,
                "assigned_date_key": assigned_date_key,
                "sla_hours": assignment_dto.sla_hours or 24,
            }

            res = conn.execute(text(sql_queries.INSERT_FACT_CLINICIAN_ASSIGNMENT), params)
            return res.scalar_one()

    def record_first_viewed(self, study_instance_uid: str, clinician_id: str) -> None:
        """
        Transitions assignment status to 'IN_PROGRESS' and captures first_viewed_at.
        """
        now = datetime.now(timezone.utc)
        with self.engine.begin() as conn:
            clinician_key = self._resolve_clinician_key(conn, clinician_id)
            study_key = self._resolve_study_key(conn, study_instance_uid)

            conn.execute(
                text(sql_queries.MARK_ASSIGNMENT_IN_PROGRESS),
                {
                    "study_key": study_key,
                    "clinician_key": clinician_key,
                    "first_viewed_at": now,
                },
            )

    def fetch_eod_report(self, date_val: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Fetches aggregated daily breakdown of assignments for HOD review.
        """
        target_date = date_val or date.today()
        date_key = int(target_date.strftime("%Y%m%d"))

        with self.engine.connect() as conn:
            res = conn.execute(text(sql_queries.GET_EOD_HOD_REPORT), {"date_key": date_key})
            return [dict(row) for row in res.mappings().all()]

    # -------------------------------------------------------------------------
    # Internal Dimension Resolvers
    # -------------------------------------------------------------------------

    def _resolve_date_key(self, conn, dt: datetime) -> int:
        """Computes or registers smart date key (YYYYMMDD)."""
        date_key = int(dt.strftime("%Y%m%d"))
        
        # Shift breakdown logic
        hour = dt.hour
        if 7 <= hour < 15:
            shift_id = "MORNING"
        elif 15 <= hour < 23:
            shift_id = "EVENING"
        else:
            shift_id = "NIGHT"

        params = {
            "date_key": date_key,
            "calendar_date": dt.date(),
            "day_of_week": dt.strftime("%A"),
            "month_name": dt.strftime("%B"),
            "year": dt.year,
            "shift_id": shift_id,
        }
        res = conn.execute(text(sql_queries.ENSURE_DATE_KEY), params)
        return res.scalar_one()

    def _resolve_clinician_key(
        self, conn, clinician_id: str, full_name: str = "Dr. Unknown", role: str = "RAD", dept: str = "Radiology"
    ) -> int:
        params = {
            "clinician_id": clinician_id,
            "full_name": full_name,
            "role": role,
            "department": dept,
        }
        res = conn.execute(text(sql_queries.RESOLVE_OR_CREATE_CLINICIAN), params)
        return res.scalar_one()

    def _resolve_patient_key(
        self, conn, patient_id: str, gender: str = "U", age_bucket: str = "Unknown"
    ) -> int:
        params = {
            "patient_id": patient_id,
            "gender": gender,
            "age_bucket": age_bucket,
        }
        res = conn.execute(text(sql_queries.RESOLVE_OR_CREATE_PATIENT), params)
        return res.scalar_one()

    def _resolve_study_key(
        self, conn, study_instance_uid: str, modality: str = "CT", series_count: int = 1, total_frames: int = 1
    ) -> int:
        params = {
            "study_instance_uid": study_instance_uid,
            "modality": modality,
            "series_count": series_count,
            "total_frames": total_frames,
            "accession_number": None,
            "body_part_examined": None,
        }
        res = conn.execute(text(sql_queries.RESOLVE_OR_CREATE_STUDY), params)
        return res.scalar_one()

    def _resolve_action_key(self, conn, action_name: str, category: str = "CLINICAL_VIEW") -> int:
        params = {
            "action_name": action_name,
            "action_category": category,
        }
        res = conn.execute(text(sql_queries.RESOLVE_OR_CREATE_ACTION_TYPE), params)
        return res.scalar_one()