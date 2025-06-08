# models/car.py
from dataclasses import dataclass, field
from datetime import datetime
from utils.enums import ChargeMode, CarState

@dataclass
class ChargingRequest:
    """Represents a user's request to charge their vehicle."""
    car_id: str
    request_mode: ChargeMode
    request_amount_kwh: float # Requested energy in kWh
    request_time: datetime = field(default_factory=datetime.now)
    state: CarState = CarState.WAITING_IN_MAIN_QUEUE
    queue_number: str = "" # e.g., F1, T1

    def to_dict(self) -> dict:
        """将充电请求对象转换为字典"""
        return {
            'car_id': self.car_id,
            'request_mode': self.request_mode.value,
            'request_amount_kwh': self.request_amount_kwh,
            'queue_number': self.queue_number,
            'request_time': self.request_time.isoformat() if self.request_time else None,
            'status': self.state.value
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ChargingRequest':
        """从字典创建充电请求对象"""
        return cls(
            car_id=data['car_id'],
            request_mode=ChargeMode(data['request_mode']),
            request_amount_kwh=data['request_amount_kwh'],
            queue_number=data.get('queue_number', ''),
            request_time=datetime.fromisoformat(data['request_time']) if data.get('request_time') else datetime.now(),
            state=CarState(data['status'])
        )

@dataclass
class Car:
    """Represents a user's electric vehicle."""
    car_id: str
    user_id: str
    capacity_kwh: float
    state: CarState = CarState.IDLE

    def to_dict(self) -> dict:
        """将车辆对象转换为字典"""
        return {
            'car_id': self.car_id,
            'user_id': self.user_id,
            'capacity_kwh': self.capacity_kwh,
            'state': self.state.value
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Car':
        """从字典创建车辆对象"""
        return cls(
            car_id=data['car_id'],
            user_id=data['user_id'],
            capacity_kwh=data['capacity_kwh'],
            state=CarState(data.get('state', CarState.IDLE.value))
        )