# models/car.py
from dataclasses import dataclass, field
from datetime import datetime
from utils.enums import ChargeMode, CarState
from typing import Optional, Dict, Any

@dataclass
class ChargingRequest:
    """Represents a charging request."""
    car_id: str
    request_mode: ChargeMode
    request_amount_kwh: float # Requested energy in kWh
    request_time: datetime = field(default_factory=datetime.now)
    state: CarState = CarState.WAITING_IN_MAIN_QUEUE
    pile_id: Optional[str] = None
    queue_number: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'car_id': self.car_id,
            'request_mode': self.request_mode.value,
            'request_amount_kwh': self.request_amount_kwh,
            'request_time': self.request_time.isoformat(),
            'state': self.state.value,
            'pile_id': self.pile_id,
            'queue_number': self.queue_number
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChargingRequest':
        """从字典创建对象"""
        request = cls(
            car_id=data['car_id'],
            request_mode=ChargeMode(data['request_mode']),
            request_amount_kwh=data['request_amount_kwh']
        )
        request.request_time = datetime.fromisoformat(data['request_time'])
        request.state = CarState(data['state'])
        request.pile_id = data.get('pile_id')
        request.queue_number = data.get('queue_number')
        return request

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