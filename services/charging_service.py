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
from utils.enums import WorkState, CarState

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

    def create_charging_request(self, car_id: str, mode, amount) -> ChargingRequest:
        request = ChargingRequest(car_id=car_id, request_mode=mode, request_amount_kwh=amount)
        self._request_repo.save(request.car_id, request) # Using car_id as unique request ID for simplicity
        self._queue_repo.add_to_queue(request)
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

    def end_charging(self, pile_id: str):
        pile = self._pile_repo.find_by_id(pile_id)
        if not pile or pile.state != WorkState.CHARGING or not pile.current_charging_session:
            print(f"[ChargingService] Error: Cannot end charge for Pile {pile_id}.")
            return None

        session = pile.current_charging_session
        print(f"[ChargingService] Ending charge for Car {session.car_id} at Pile {pile_id}.")

        bill = self._billing_service.calculate_and_create_bill(session, pile, datetime.now())
        self._bill_repo.save(bill.bill_id, bill)
        
        request = self._request_repo.find_by_id(session.car_id)
        request.state = CarState.AWAITING_PAYMENT

        # Reset pile
        pile.state = WorkState.IDLE
        pile.current_charging_session = None
        self._session_repo.delete(session.session_id)
        self._pile_repo.save(pile.pile_id, pile) # Update pile state
        
        return bill
        
    def report_pile_failure(self, pile_id: str):
        pile = self._pile_repo.find_by_id(pile_id)
        if not pile: return

        print(f"[ChargingService] EMERGENCY: Pile {pile_id} reported a failure!")
        pile.state = WorkState.FAULTY
        
        # If a car was charging, interrupt it
        if pile.current_charging_session:
            session = pile.current_charging_session
            print(f"  -> Interrupting charge for Car {session.car_id}.")
            # A real system would calculate partial bill and re-queue the car
            # For simplicity, we just end the session without a full bill
            interrupted_request = self._request_repo.find_by_id(session.car_id)
            interrupted_request.state = CarState.WAITING_IN_MAIN_QUEUE
            self._queue_repo.add_to_front_of_queue(interrupted_request) # Re-add to front of the queue
            print(f"  -> Car {session.car_id} has been re-queued with priority.")
            
            pile.current_charging_session = None
            self._session_repo.delete(session.session_id)
            
        self._pile_repo.save(pile.pile_id, pile)

    def recover_pile(self, pile_id: str):
        pile = self._pile_repo.find_by_id(pile_id)
        if pile and pile.state == WorkState.FAULTY:
            pile.state = WorkState.IDLE
            self._pile_repo.save(pile.pile_id, pile)
            print(f"[ChargingService] Pile {pile_id} has been recovered and is now IDLE.")