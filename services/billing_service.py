# services/billing_service.py
import uuid
from datetime import datetime
from models.bill import Bill
from models.charging_pile import ChargingPile
from utils import config

class BillingService:
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