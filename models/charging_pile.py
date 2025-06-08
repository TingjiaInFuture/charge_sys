# models/charging_pile.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from collections import deque
from utils.enums import WorkState, ChargeMode, CarState
from models.car import ChargingRequest
from models.bill import ChargingSession
from datetime import datetime

@dataclass
class ChargingPile:
    """Base class for a charging pile."""
    pile_id: str
    pile_type: ChargeMode
    state: WorkState = WorkState.IDLE
    power_kw: float = 0.0 # Power in kW
    local_queue: deque = field(default_factory=lambda: deque(maxlen=2))
    current_charging_session: Optional['ChargingSession'] = None
    is_faulty: bool = False
    total_charging_sessions: int = 0
    total_charging_time: float = 0.0  # in hours
    total_charging_energy: float = 0.0  # in kWh
    current_car_id: Optional[str] = None
    start_time: Optional[datetime] = None
    charged_kwh: float = 0.0
    total_charged_kwh: float = 0.0
    total_charging_count: int = 0
    total_income: float = 0.0

    def add_to_local_queue(self, request: ChargingRequest):
        if len(self.local_queue) < self.local_queue.maxlen and not self.is_faulty:
            request.state = CarState.WAITING_AT_PILE_QUEUE
            self.local_queue.append(request)
            return True
        return False
        
    def get_next_car_from_queue(self) -> Optional[ChargingRequest]:
        if self.local_queue and not self.is_faulty:
            return self.local_queue.popleft()
        return None

    def set_faulty(self, is_faulty: bool):
        """Set the charging pile's faulty state."""
        self.is_faulty = is_faulty
        if is_faulty:
            self.state = WorkState.FAULTY
        else:
            self.state = WorkState.IDLE

    def to_dict(self) -> Dict[str, Any]:
        """将充电桩对象转换为字典"""
        return {
            'pile_id': self.pile_id,
            'pile_type': self.pile_type.value,
            'power_kw': self.power_kw,
            'state': self.state.value,
            'current_car_id': self.current_car_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'charged_kwh': self.charged_kwh,
            'total_charged_kwh': self.total_charged_kwh,
            'total_charging_time': self.total_charging_time,
            'total_charging_count': self.total_charging_count,
            'total_income': self.total_income
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChargingPile':
        """从字典创建充电桩对象"""
        pile = cls(
            pile_id=data['pile_id'],
            pile_type=ChargeMode(data['pile_type']),
            power_kw=data['power_kw'],
            state=WorkState(data['state'])
        )
        pile.current_car_id = data['current_car_id']
        pile.start_time = datetime.fromisoformat(data['start_time']) if data['start_time'] else None
        pile.charged_kwh = data['charged_kwh']
        pile.total_charged_kwh = data['total_charged_kwh']
        pile.total_charging_time = data['total_charging_time']
        pile.total_charging_count = data['total_charging_count']
        pile.total_income = data['total_income']
        return pile
    
    def start_charging(self, car_id: str):
        """开始充电"""
        self.current_car_id = car_id
        self.start_time = datetime.now()
        self.charged_kwh = 0.0
        self.state = WorkState.CHARGING
    
    def end_charging(self, charged_kwh: float, income: float):
        """结束充电"""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds() / 3600
            self.total_charging_time += duration
            self.total_charged_kwh += charged_kwh
            self.total_charging_count += 1
            self.total_income += income
        
        self.current_car_id = None
        self.start_time = None
        self.charged_kwh = 0.0
        self.state = WorkState.IDLE
        self.current_charging_session = None  # 确保清除当前充电会话
    
    def update_charging(self, charged_kwh: float):
        """更新充电量"""
        self.charged_kwh = charged_kwh
    
    def set_state(self, state: WorkState):
        """设置充电桩状态"""
        self.state = state

@dataclass
class FastChargingPile(ChargingPile):
    """Represents a fast charging pile."""
    pile_type: ChargeMode = ChargeMode.FAST
    power_kw: float = 30.0  # 30 kW for fast charger

    def to_dict(self) -> Dict[str, Any]:
        """将快充充电桩对象转换为字典"""
        data = super().to_dict()
        data['pile_class'] = 'FastChargingPile'
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FastChargingPile':
        """从字典创建快充充电桩对象"""
        return super().from_dict(data)

@dataclass
class TrickleChargingPile(ChargingPile):
    """Represents a trickle (slow) charging pile."""
    pile_type: ChargeMode = ChargeMode.TRICKLE
    power_kw: float = 10.0  # 10 kW for slow charger

    def to_dict(self) -> Dict[str, Any]:
        """将慢充充电桩对象转换为字典"""
        data = super().to_dict()
        data['pile_class'] = 'TrickleChargingPile'
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrickleChargingPile':
        """从字典创建慢充充电桩对象"""
        return super().from_dict(data)