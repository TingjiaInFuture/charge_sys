# services/charging_service.py
import uuid
from datetime import datetime
from models.car import ChargingRequest
from models.charging_pile import ChargingPile
from models.bill import ChargingSession
from repositories.repositories import (
    PileRepository, SessionRepository, BillRepository, RequestRepository, QueueRepository
)
from services.billing_service import BillingService
from services.queue_service import QueueService
from utils.enums import WorkState, CarState, ChargeMode

class ChargingService:
    def __init__(self, pile_repo: PileRepository, session_repo: SessionRepository, 
                 bill_repo: BillRepository, request_repo: RequestRepository, 
                 queue_repo: QueueRepository, billing_service: BillingService):
        self._pile_repo = pile_repo
        self._session_repo = session_repo
        self._bill_repo = bill_repo
        self._request_repo = request_repo
        self._queue_repo = queue_repo
        self._billing_service = billing_service
        self._queue_service = QueueService(queue_repo)

    def create_charging_request(self, car_id: str, mode: str, amount: float) -> ChargingRequest:
        """创建充电请求
        
        Args:
            car_id: 车辆ID
            mode: 充电模式（"FAST" 或 "TRICKLE"）
            amount: 充电量（kWh）
            
        Returns:
            ChargingRequest: 创建的充电请求
        """
        # 转换充电模式字符串为枚举值
        request_mode = ChargeMode.FAST if mode == "FAST" else ChargeMode.TRICKLE
        
        # 创建充电请求
        request = ChargingRequest(
            car_id=car_id,
            request_mode=request_mode,
            request_amount_kwh=amount,
            state=CarState.WAITING_IN_MAIN_QUEUE  # 设置初始状态
        )
        
        # 保存请求
        self._request_repo.save(request.car_id, request)
        
        # 使用队列服务添加到队列并生成排队号码
        queue_number = self._queue_service.add_to_queue(request)
        
        # 更新请求的排队号码
        request.queue_number = queue_number
        self._request_repo.save(request.car_id, request)
        
        return request

    def start_charging(self, pile: ChargingPile, request: ChargingRequest):
        if pile.state != WorkState.IDLE:
            print(f"[ChargingService] Error: Pile {pile.pile_id} is not idle.")
            return

        print(f"[ChargingService] Starting charge for Car {request.car_id} at Pile {pile.pile_id}.")
        pile.state = WorkState.CHARGING
        request.state = CarState.CHARGING
        
        session = ChargingSession(
            session_id=str(uuid.uuid4()),
            car_id=request.car_id,
            pile_id=pile.pile_id,
            start_time=datetime.now(),
            request_amount_kwh=request.request_amount_kwh
        )
        self._session_repo.save(session.session_id, session)
        pile.current_charging_session = session
        self._pile_repo.save(pile.pile_id, pile) # Update pile state in repo

    def end_charging(self, car_id: str):
        """结束充电
        
        Args:
            car_id: 车辆ID
        """
        # 查找当前充电会话
        current_session = None
        for session in self._session_repo.get_all():
            if session.car_id == car_id:
                current_session = session
                break

        if not current_session:
            print(f"[ChargingService] Error: No active charging session found for Car {car_id}")
            return None

        # 获取充电桩
        pile = self._pile_repo.get(current_session.pile_id)
        if not pile:
            print(f"[ChargingService] Error: Pile {current_session.pile_id} not found")
            return None

        print(f"[ChargingService] Ending charge for Car {car_id} at Pile {pile.pile_id}")
        print(f"[ChargingService] Current pile state: {pile.state.value}")
        print(f"[ChargingService] Current pile charged_kwh: {pile.charged_kwh}")

        # 计算账单
        bill = self._billing_service.calculate_and_create_bill(current_session, pile, datetime.now())
        self._bill_repo.save(bill.bill_id, bill)
        print(f"[ChargingService] Created bill for Car {car_id}")
        
        # 更新请求状态
        request = self._request_repo.get(car_id)
        if request:
            request.state = CarState.CHARGING_COMPLETED
            self._request_repo.save(request.car_id, request)
            print(f"[ChargingService] Updated request state to CHARGING_COMPLETED for Car {car_id}")

        # 更新充电桩状态
        pile.end_charging(pile.charged_kwh, bill.total_fee)
        self._pile_repo.save(pile.pile_id, pile)
        print(f"[ChargingService] Updated pile state to {pile.state.value} for Pile {pile.pile_id}")
        print(f"[ChargingService] Pile charged_kwh after end_charging: {pile.charged_kwh}")
        
        # 删除会话
        self._session_repo.delete(current_session.session_id)
        print(f"[ChargingService] Deleted charging session for Car {car_id}")
        
        print(f"[ChargingService] Charging completed for Car {car_id}. Total amount: {bill.total_fee}")
        return bill
        
    def report_pile_failure(self, pile_id: str):
        pile = self._pile_repo.get(pile_id)
        if not pile: return

        print(f"[ChargingService] EMERGENCY: Pile {pile_id} reported a failure!")
        pile.state = WorkState.FAULTY
        
        # If a car was charging, interrupt it
        if pile.current_charging_session:
            session = pile.current_charging_session
            print(f"  -> Interrupting charge for Car {session.car_id}.")
            # A real system would calculate partial bill and re-queue the car
            # For simplicity, we just end the session without a full bill
            interrupted_request = self._request_repo.get(session.car_id)
            interrupted_request.state = CarState.WAITING_IN_MAIN_QUEUE
            self._queue_repo.add_to_front_of_queue(interrupted_request) # Re-add to front of the queue
            print(f"  -> Car {session.car_id} has been re-queued with priority.")
            
            pile.current_charging_session = None
            self._session_repo.delete(session.session_id)
            
        self._pile_repo.save(pile.pile_id, pile)

    def recover_pile(self, pile_id: str):
        pile = self._pile_repo.get(pile_id)
        if pile and pile.state == WorkState.FAULTY:
            pile.state = WorkState.IDLE
            self._pile_repo.save(pile.pile_id, pile)
            print(f"[ChargingService] Pile {pile_id} has been recovered and is now IDLE.")