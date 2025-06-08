# utils/enums.py
import enum

class WorkState(enum.Enum):
    """Represents the operational state of a charging pile."""
    IDLE = "空闲"
    CHARGING = "充电中"
    FAULTY = "故障"
    OFFLINE = "离线"

class ChargeMode(enum.Enum):
    """Represents the charging mode requested by a user."""
    FAST = "快充"
    TRICKLE = "慢充"

class CarState(enum.Enum):
    """Represents the state of a car in the charging process."""
    IDLE = "空闲"
    WAITING_IN_MAIN_QUEUE = "在主队列等待"
    WAITING_AT_PILE_QUEUE = "在桩队列等待"
    CHARGING = "充电中"
    CHARGING_COMPLETED = "充电完成"
    AWAITING_PAYMENT = "等待缴费"

class PileState(enum.Enum):
    IDLE = "空闲"
    CHARGING = "充电中"
    FAULT = "故障"
    REPAIRING = "维修中"