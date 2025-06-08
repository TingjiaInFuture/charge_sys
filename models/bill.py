# models/bill.py
from dataclasses import dataclass
from datetime import datetime
from utils.enums import ChargeMode

@dataclass
class ChargingSession:
    """Represents an active charging session."""
    session_id: str
    car_id: str
    pile_id: str
    start_time: datetime
    request_amount_kwh: float
    
    def to_dict(self) -> dict:
        """将充电会话对象转换为字典"""
        return {
            'session_id': self.session_id,
            'car_id': self.car_id,
            'pile_id': self.pile_id,
            'start_time': self.start_time.isoformat(),
            'request_amount_kwh': self.request_amount_kwh
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChargingSession':
        """从字典创建充电会话对象"""
        return cls(
            session_id=data['session_id'],
            car_id=data['car_id'],
            pile_id=data['pile_id'],
            start_time=datetime.fromisoformat(data['start_time']),
            request_amount_kwh=data['request_amount_kwh']
        )

@dataclass
class Bill:
    """Represents the final bill for a completed charging session."""
    bill_id: str
    car_id: str
    pile_id: str
    start_time: datetime
    end_time: datetime
    charged_kwh: float
    charge_mode: ChargeMode
    charge_fee: float
    service_fee: float
    total_fee: float

    def to_dict(self) -> dict:
        """将账单对象转换为字典"""
        return {
            'bill_id': self.bill_id,
            'car_id': self.car_id,
            'pile_id': self.pile_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'charged_kwh': self.charged_kwh,
            'charge_mode': self.charge_mode.value,
            'charge_fee': self.charge_fee,
            'service_fee': self.service_fee,
            'total_fee': self.total_fee
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Bill':
        """从字典创建账单对象"""
        return cls(
            bill_id=data['bill_id'],
            car_id=data['car_id'],
            pile_id=data['pile_id'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            charged_kwh=data['charged_kwh'],
            charge_mode=ChargeMode(data['charge_mode']),
            charge_fee=data['charge_fee'],
            service_fee=data['service_fee'],
            total_fee=data['total_fee']
        )