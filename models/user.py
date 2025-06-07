# models/user.py
from dataclasses import dataclass
from models.car import Car

@dataclass
class User:
    """Represents a system user (driver)."""
    user_id: str
    password_hash: str # In a real system, this would be a hash
    car: Car