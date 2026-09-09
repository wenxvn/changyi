"""Repository contracts for region-scoped resource access."""

from .doctor_repository import DoctorRepository
from .hospital_repository import HospitalRepository
from .transit_repository import TransitRepository

__all__ = ["DoctorRepository", "HospitalRepository", "TransitRepository"]
