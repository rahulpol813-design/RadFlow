from storage.models import Base
from datetime import date
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy import (
    BigInteger,
    Integer,
    SmallInteger,
    String,
    Boolean,
    Date,
)


class DimClinician(Base):
    __tablename__ = "dim_clinician"

    clinician_key : Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    clinician_id : Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    full_name : Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    department : Mapped[str] = mapped_column(String(64), nullable=False)
    is_active : Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class DimPatient(Base):
    __tablename__ = "dim_patient"

    patient_key :Mapped[int] =mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id : Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    gender : Mapped[str] = mapped_column(String(16), nullable=False)
    age_bucket : Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

class DimStudy(Base):
    __tablename__ = "dim_study"

    study_key : Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    study_instance_uid : Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    modality : Mapped[str] = mapped_column(String(16), nullable=False)
    series_count : Mapped[int] = mapped_column(Integer, nullable=False)
    total_frames : Mapped[int] = mapped_column(Integer, nullable=False)
    accession_number: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    body_part_examined: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

class DimActionType(Base):
    __tablename__ = "dim_action_type"

    action_type_key : Mapped[int] =mapped_column(BigInteger, primary_key=True, autoincrement=True)
    action_name : Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    action_category : Mapped[str] = mapped_column(String(64), nullable=False)

class DimDate(Base):
    __tablename__ = "dim_date"

    date_key : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    calendar_date : Mapped[date] = mapped_column(Date, unique=True, index=True, nullable=False)
    day_of_week : Mapped[str] = mapped_column(String(16), nullable=False)
    year : Mapped[int] = mapped_column(Integer, nullable=False)
    month_name: Mapped[str] = mapped_column(String(16), nullable=False)
    shift_id : Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

