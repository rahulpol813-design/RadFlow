"""┌────────────────────────────────────────────────────────────────────────┐
 │                      <<Interface>> AuditRepository                      │
 ├────────────────────────────────────────────────────────────────────────┤
 │ + initialize_schema() -> None                                          │
 │ + get_or_create_clinician(clinician_id, full_name, role, dept) -> int  │
 │ + get_or_create_patient(patient_id, gender, age_bucket) -> int         │
 │ + get_or_create_study(study_uid, modality, series_cnt, frames) -> int  │
 │ + get_action_type_key(action_name) -> int                              │
 │ + log_image_activity(activity_data: ActivityLogDTO) -> int             │
 │ + assign_study(assignment_data: AssignmentDTO) -> int                  │
 │ + mark_assignment_viewed(study_key: int, clinician_key: int) -> None   │
 │ + complete_assignment(assignment_key: int) -> None                     │
 └───────────────────────────────────▲────────────────────────────────────┘
                                     │
                     ┌───────────────┴───────────────┐
                     │                               │
        ┌────────────┴───────────┐      ┌────────────┴───────────┐
        │  SqlServerAuditAdapter │      │  PostgresAuditAdapter  │
        └────────────────────────┘      └────────────────────────┘"""


from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional, List, Dict, Any


@dataclass
class ActivityLogDTO:
    """Data Transfer Object for logging image activity."""
    clinician_id: str
    patient_id: str
    study_instance_uid: str
    action_name: str
    frame_id: Optional[int] = None
    is_cache_hit: bool = False
    latency_ms: Optional[int] = None

@dataclass
class AssignmentDTO:
    """Data Transfer Object for creating clinician assignments."""
    clinician_id: str
    patient_id: str
    study_instance_uid: str
    sla_hours: Optional[int] = 24


class AuditRepository(ABC):
    """Abstract Repository Interface decoupling DB dialect logic from upper services."""

    @abstractmethod
    def initialize_schema(self) -> None:
        """Initialize the database schema and tables if they do not exist."""
        pass

    @abstractmethod
    def record_activity(self, log_dto: ActivityLogDTO) -> int:
        """
        Resolves or auto-populates dimension keys (clinician, patient, study, action, date),
        inserts a record into fact_image_activity, and returns the generated activity_key.
        """
        pass

    @abstractmethod
    def create_assignment(self, assignment_dto: AssignmentDTO) -> int:
        """
        Resolves dimension keys and records an assignment in fact_clinician_assignment.
        Returns the generated assignment_key.
        """
        pass

    @abstractmethod
    def record_first_viewed(self, study_instance_uid: str, clinician_id: str) -> None:
        """
        Checks if an assignment exists for this pair, transitions assignment_status
        to 'IN_PROGRESS', and records first_viewed_at timestamp.
        """
        pass

    @abstractmethod
    def fetch_eod_report(self, date_val: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Retrieves assignments and operational KPIs grouped by radiologist/status
        for Head of Department (HOD) oversight.
        """
        pass

