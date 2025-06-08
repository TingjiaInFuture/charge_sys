# models/user.py
from dataclasses import dataclass, asdict
from models.car import Car

@dataclass
class User:
    """Represents a system user (driver)."""
    user_id: str
    password_hash: str # In a real system, this would be a hash
    car: Car

    def to_dict(self) -> dict:
        """将用户对象转换为字典"""
        return {
            'user_id': self.user_id,
            'password_hash': self.password_hash,
            'car': self.car.to_dict() if self.car else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """从字典创建用户对象"""
        car_data = data.get('car')
        car = Car.from_dict(car_data) if car_data else None
        return cls(
            user_id=data['user_id'],
            password_hash=data['password_hash'],
            car=car
        )