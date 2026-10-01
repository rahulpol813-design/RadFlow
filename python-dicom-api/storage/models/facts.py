"""┌─────────────────────────┐         ┌─────────────────────────┐
 │       DimClinician      │         │        DimPatient       │
 ├─────────────────────────┤         ├─────────────────────────┤
 │ PK clinician_key: int   │         │ PK patient_key: int     │
 │    clinician_id: str    │         │    patient_id: str      │
 │    full_name: str       │         │    gender: str?         │
 │    role: str            │         │    age_bucket: str?     │
 │    department: str?     │         └────────────┬────────────┘
 │    is_active: bool      │                      │
 └────────────┬────────────┘                      │
              │                                   │
              │ 1:N                               │ 1:N
   ┌──────────┴──────────────────────────┐        │
   │                                     │        │
   ▼                                     ▼        ▼
 ┌─────────────────────────────────┐   ┌─────────────────────────────────┐
 │    FactClinicianAssignment      │   │        FactImageActivity        │
 ├─────────────────────────────────┤   ├─────────────────────────────────┤
 │ PK assignment_key: int          │   │ PK activity_key: int            │
 │ FK clinician_key: int           │   │ FK clinician_key: int           │
 │ FK patient_key: int             │   │ FK patient_key: int             │
 │ FK study_key: int               │   │ FK study_key: int               │
 │ FK assigned_date_key: int       │   │ FK action_type_key: int         │
 │ FK completed_date_key: int?     │   │ FK date_key: int                │
 │    assignment_status: str       │   │    frame_id: str                │
 │    first_viewed_at: datetime?   │   │    is_cache_hit: bool           │
 │    completed_at: datetime?      │   │    latency_ms: int              │
 │    sla_hours: int               │   │    timestamp: datetime          │
 │    turnaround_minutes: int?     │   └───────▲───────────────▲─────────┘
 └──────────────┬──────────────────┘           │               │
                │                              │ 1:N           │ 1:N
                │ 1:N                          │               │
                ▼                              │               │
 ┌─────────────────────────┐                   │               │
 │        DimStudy         ├───────────────────┘               │
 ├─────────────────────────┤                                   │
 │ PK study_key: int       │                                   │
 │    study_instance_uid   │                                   │
 │    modality: str        │                                   │
 │    series_count: int    │                                   │
 │    total_frames: int    │                                   │
 └─────────────────────────┘                                   │
                                                               │
 ┌─────────────────────────┐       ┌───────────────────────────┴─┐
 │      DimActionType      │       │           DimDate           │
 ├─────────────────────────┤       ├─────────────────────────────┤
 │ PK action_type_key: int │       │ PK date_key: int (YYYYMMDD) │
 │    action_name: str     │       │    calendar_date: date      │
 │    action_category: str │       │    day_of_week: str         │
 └──────────────┬──────────┘       │    month_name: str          │
                │ 1:N              │    year: int                │
                └──────────────────┤    shift_id: str?           │
                                   └─────────────────────────────┘"""



from storage.models import Base
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy import (
    ForeignKey,
    BigInteger,
    Integer,
    SmallInteger,
    String,
    Boolean,
    Date,
    DateTime,
)


class FactImageActivity(Base):
    """Primary Key: activity_key (BigInteger, surrogate, autoincrementing)."""
    __tablename__ = "fact_image_activity"
    
    activity_key : Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True) #PK
    clinician_key : Mapped[int] = mapped_column(BigInteger, ForeignKey("dim_clinician.clinician_key"), nullable=False) #FK to dim_clinician.clinician_key
    patient_key : Mapped[int] = mapped_column(BigInteger, ForeignKey("dim_patient.patient_key"), nullable=False) #FK to dim_patient.patient_key
    study_key : Mapped[int] = mapped_column(BigInteger, ForeignKey("dim_study.study_key"), nullable=False) #FK to dim_study.study_key
    action_type_key : Mapped[int] = mapped_column(BigInteger, ForeignKey("dim_action_type.action_type_key"), nullable=False) #FK to dim_action_type.action_type_key
    date_key : Mapped[int] = mapped_column(Integer, ForeignKey("dim_date.date_key"), nullable=False) #FK to dim_date.date_key
    frame_id : Mapped[Optional[int]] = mapped_column(Integer, nullable=True) #Frame ID for frame-level actions, nullable for study-level actions
    is_cache_hit : Mapped[bool] = mapped_column(Boolean, nullable=False, default=False) #Indicates if the image was retrieved from cache
    latency_ms : Mapped[Optional[int]] = mapped_column(Integer, nullable=True) #Latency in milliseconds for the action, nullable if not applicable
    timestamp : Mapped[datetime] = mapped_column(DateTime, nullable=False) #Timestamp of the action

class FactClinicianAssignment(Base):
    """Primary Key: assignment_key (BigInteger, surrogate, autoincrementing)."""
    __tablename__ = "fact_clinician_assignment"
    
    assignment_key : Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True) #PK
    clinician_key : Mapped[int] = mapped_column(BigInteger, ForeignKey("dim_clinician.clinician_key"), nullable=False) #FK to dim_clinician.clinician_key
    patient_key : Mapped[int] = mapped_column(BigInteger, ForeignKey("dim_patient.patient_key"), nullable=False) #FK to dim_patient.patient_key
    study_key : Mapped[int] = mapped_column(BigInteger, ForeignKey("dim_study.study_key"), nullable=False) #FK to dim_study.study_key
    assigned_date_key : Mapped[int] = mapped_column(Integer, ForeignKey("dim_date.date_key"), nullable=False) #FK to dim_date.date_key
    completed_date_key : Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("dim_date.date_key"), nullable=True) #FK to dim_date.date_key, nullable if not completed
    first_viewed_at : Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True) #Timestamp when the assignment was first viewed, nullable if not viewed
    completed_at : Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sla_hours : Mapped[Optional[int]] = mapped_column(Integer, nullable=True) #Service Level Agreement in hours, nullable if not applicable
    turnaround_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    assignment_status: Mapped[str] = mapped_column(String(32), default="ASSIGNED", nullable=False)
