# services/billing_service.py
import uuid
from datetime import datetime, time
from models.bill import Bill
from models.charging_pile import ChargingPile
from utils import config
from dataclasses import dataclass
from typing import Tuple

@dataclass
class BillingConfig:
    """Configuration for billing rates."""
    PEAK_RATE = 1.0  # 元/度
    NORMAL_RATE = 0.7  # 元/度
    VALLEY_RATE = 0.4  # 元/度
    SERVICE_RATE = 0.8  # 元/度

    @staticmethod
    def get_peak_hours() -> list:
        return [
            (time(10, 0), time(15, 0)),
            (time(18, 0), time(21, 0))
        ]

    @staticmethod
    def get_normal_hours() -> list:
        return [
            (time(7, 0), time(10, 0)),
            (time(15, 0), time(18, 0)),
            (time(21, 0), time(23, 0))
        ]

    @staticmethod
    def get_valley_hours() -> list:
        return [
            (time(23, 0), time(23, 59, 59)),
            (time(0, 0), time(7, 0))
        ]

class BillingService:
    """Service for handling charging billing calculations."""

    def __init__(self):
        # 分时段电价（元/度）
        self.PEAK_RATE = 1.0  # 峰时：10:00~15:00，18:00~21:00
        self.NORMAL_RATE = 0.7  # 平时：7:00~10:00，15:00~18:00，21:00~23:00
        self.VALLEY_RATE = 0.4  # 谷时：23:00~次日7:00
        
        # 服务费单价（元/度）
        self.SERVICE_RATE = 0.8

    def _get_time_rate(self, current_time: time) -> float:
        """获取当前时段的电价"""
        hour = current_time.hour
        
        # 峰时
        if (10 <= hour < 15) or (18 <= hour < 21):
            return self.PEAK_RATE
        
        # 平时
        if (7 <= hour < 10) or (15 <= hour < 18) or (21 <= hour < 23):
            return self.NORMAL_RATE
        
        # 谷时
        return self.VALLEY_RATE

    def calculate_charging_cost(self, charged_kwh: float, start_time: datetime, end_time: datetime) -> Tuple[float, float, float]:
        """计算充电费用
        
        Args:
            charged_kwh: 充电量（度）
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            Tuple[float, float, float]: (充电费用, 服务费用, 总费用)
        """
        # 计算充电费用
        charge_fee = 0.0
        current_time = start_time
        
        # 如果充电跨天，需要分段计算
        while current_time < end_time:
            # 计算当前时段的结束时间
            if current_time.hour < 7:
                next_time = current_time.replace(hour=7, minute=0, second=0)
            elif current_time.hour < 10:
                next_time = current_time.replace(hour=10, minute=0, second=0)
            elif current_time.hour < 15:
                next_time = current_time.replace(hour=15, minute=0, second=0)
            elif current_time.hour < 18:
                next_time = current_time.replace(hour=18, minute=0, second=0)
            elif current_time.hour < 21:
                next_time = current_time.replace(hour=21, minute=0, second=0)
            elif current_time.hour < 23:
                next_time = current_time.replace(hour=23, minute=0, second=0)
            else:
                next_time = current_time.replace(hour=23, minute=59, second=59)
            
            # 如果下一个时间点超过了结束时间，就使用结束时间
            if next_time > end_time:
                next_time = end_time
            
            # 计算当前时段的时长（小时）
            duration = (next_time - current_time).total_seconds() / 3600
            
            # 计算当前时段的充电量
            total_duration = (end_time - start_time).total_seconds() / 3600
            current_kwh = charged_kwh * (duration / total_duration)
            
            # 计算当前时段的费用
            rate = self._get_time_rate(current_time.time())
            charge_fee += current_kwh * rate
            
            # 更新时间
            current_time = next_time
        
        # 计算服务费
        service_fee = charged_kwh * self.SERVICE_RATE
        
        # 计算总费用
        total_fee = charge_fee + service_fee
        
        return charge_fee, service_fee, total_fee

    def calculate_and_create_bill(self, session, pile: ChargingPile, end_time: datetime) -> Bill:
        duration_hours = (end_time - session.start_time).total_seconds() / 3600
        charged_kwh = min(pile.power_kw * duration_hours, session.request_amount_kwh)
        
        price_per_kwh = config.PRICE_PER_KWH[pile.pile_type]
        charge_fee = charged_kwh * price_per_kwh
        service_fee = config.SERVICE_FEE
        total_fee = charge_fee + service_fee
        
        bill = Bill(
            bill_id=str(uuid.uuid4()),
            car_id=session.car_id,
            pile_id=session.pile_id,
            start_time=session.start_time,
            end_time=end_time,
            charged_kwh=round(charged_kwh, 2),
            charge_mode=pile.pile_type,
            charge_fee=round(charge_fee, 2),
            service_fee=round(service_fee, 2),
            total_fee=round(total_fee, 2)
        )
        print(f"[BillingService] Bill created for Car {bill.car_id}. Total: ${bill.total_fee:.2f}")
        return bill