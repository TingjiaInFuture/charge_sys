import socket
import threading
import json
from typing import Dict, Any
from datetime import datetime
import time

from models.car import Car, ChargingRequest
from models.charging_pile import ChargingPile, FastChargingPile, TrickleChargingPile
from models.bill import ChargingSession, Bill
from models.user import User
from utils.enums import ChargeMode, CarState, PileState, WorkState
from repositories.repositories import (
    UserRepository, PileRepository, SessionRepository,
    BillRepository, RequestRepository, QueueRepository
)
from services.user_service import UserService
from services.charging_service import ChargingService
from services.billing_service import BillingService
from services.queue_service import QueueService
from services.dispatch_service import DispatchService
from services.scheduling_service import SchedulingService

class ChargeServer:
    def __init__(self, host: str = 'localhost', port: int = 5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # 初始化所有组件
        self._init_components()
        
        # 客户端连接
        self.clients: Dict[str, socket.socket] = {}
    
    def _init_components(self):
        """初始化所有组件"""
        print("正在初始化系统组件...")
        
        # 初始化仓库
        self.user_repo = UserRepository()
        self.pile_repo = PileRepository()
        self.session_repo = SessionRepository()
        self.bill_repo = BillRepository()
        self.request_repo = RequestRepository()
        self.queue_repo = QueueRepository()
        
        # 初始化服务
        self.billing_service = BillingService()
        self.user_service = UserService(self.user_repo)
        self.queue_service = QueueService(self.queue_repo)
        self.dispatch_service = DispatchService(self.pile_repo, self.queue_repo)
        self.charging_service = ChargingService(
            self.pile_repo, self.session_repo, self.bill_repo,
            self.request_repo, self.queue_repo, self.billing_service
        )
        self.scheduling_service = SchedulingService(
            self.pile_repo, 
            self.queue_repo, 
            self.charging_service,
            self.request_repo
        )
        
        # 初始化充电桩
        self._init_charging_piles()
        
        # 启动调度线程
        self._start_scheduling_thread()
        
        print("系统组件初始化完成！")
    
    def _init_charging_piles(self):
        """初始化充电桩"""
        print("正在初始化充电桩...")
        
        # 清空现有充电桩
        self.pile_repo.clear()
        
        # 创建快充充电桩（2个，30度/小时）
        for i in range(1, 3):
            pile_id = f"F{i:02d}"
            pile = FastChargingPile(
                pile_id=pile_id,
                pile_type=ChargeMode.FAST,
                power_kw=30.0,
                state=WorkState.IDLE
            )
            self.pile_repo.save(pile_id, pile)
            print(f"创建快充充电桩 {pile_id}")
        
        # 创建慢充充电桩（3个，10度/小时）
        for i in range(1, 4):
            pile_id = f"T{i:02d}"
            pile = TrickleChargingPile(
                pile_id=pile_id,
                pile_type=ChargeMode.TRICKLE,
                power_kw=10.0,
                state=WorkState.IDLE
            )
            self.pile_repo.save(pile_id, pile)
            print(f"创建慢充充电桩 {pile_id}")
        
        print("充电桩初始化完成！")
    
    def _start_scheduling_thread(self):
        """启动调度线程"""
        def scheduling_loop():
            while True:
                try:
                    self.scheduling_service.run_schedule_cycle()
                    time.sleep(5)  # 每5秒检查一次
                except Exception as e:
                    print(f"调度线程发生错误: {str(e)}")
                    time.sleep(5)  # 发生错误时等待5秒后继续

        scheduling_thread = threading.Thread(target=scheduling_loop, daemon=True)
        scheduling_thread.start()
        print("调度线程已启动")
    
    def start(self):
        """启动服务器"""
        try:
            # 绑定地址和端口
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"服务器启动成功，监听地址：{self.host}:{self.port}")
            
            # 初始化系统组件
            self._init_components()
            
            while True:
                # 接受客户端连接
                client_socket, address = self.server_socket.accept()
                print(f"接受来自 {address} 的连接")
                
                # 创建新线程处理客户端请求
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address)
                )
                client_thread.start()
                
        except Exception as e:
            print(f"服务器启动失败：{str(e)}")
        finally:
            self.stop()
    
    def stop(self):
        """停止服务器"""
        try:
            # 关闭所有客户端连接
            for client in self.clients.values():
                client.close()
            self.clients.clear()
            
            # 关闭服务器套接字
            if hasattr(self, 'server_socket'):
                self.server_socket.close()
            
            print("服务器已停止")
        except Exception as e:
            print(f"停止服务器时出错：{str(e)}")
    
    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """处理客户端请求"""
        try:
            while True:
                # 接收客户端消息，循环累积直到获取完整JSON
                buffer = b''
                while True:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    buffer += chunk
                    # 尝试解析JSON
                    try:
                        request = json.loads(buffer.decode('utf-8'))
                        break  # 解析成功，退出循环
                    except json.JSONDecodeError:
                        continue  # 继续接收数据
                if not buffer:
                    break  # 没有数据，退出外层循环
                
                # 处理请求并获取响应
                response = self._process_request(request)
                
                # 发送响应
                response_data = json.dumps(response).encode('utf-8')
                total_sent = 0
                while total_sent < len(response_data):
                    sent = client_socket.send(response_data[total_sent:])
                    if sent == 0:
                        raise RuntimeError("Socket connection broken")
                    total_sent += sent
                
        except Exception as e:
            print(f"处理客户端 {address} 请求时出错：{str(e)}")
        finally:
            client_socket.close()
            print(f"客户端 {address} 断开连接")
    
    def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理客户端请求"""
        action = request.get('action')
        data = request.get('data', {})
        
        try:
            if action == 'register':
                return self._handle_register(data)
            elif action == 'login':
                return self._handle_login(data)
            elif action == 'submit_charging_request':
                return self._handle_charging_request(data)
            elif action == 'end_charging':
                return self._handle_end_charging(data)
            elif action == 'get_charging_details':
                return self._handle_get_charging_details(data)
            elif action == 'get_all_piles':
                return self._handle_get_all_piles()
            elif action == 'toggle_pile_state':
                return self._handle_toggle_pile_state(data)
            elif action == 'get_pile_queue':
                return self._handle_get_pile_queue(data)
            elif action == 'get_reports':
                return self._handle_get_reports(data)
            else:
                return {'status': 'error', 'message': '未知的操作类型'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_register(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户注册请求"""
        user_id = data.get('user_id')
        password = data.get('password')
        car_id = data.get('car_id')
        battery_capacity = data.get('battery_capacity')
        
        try:
            self.user_service.register(user_id, password, car_id, battery_capacity)
            return {'status': 'success', 'message': '注册成功'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_login(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户登录请求"""
        user_id = data.get('user_id')
        password = data.get('password')
        
        try:
            print(f'开始处理登录请求，用户ID：{user_id}')
            user = self.user_service.login(user_id, password)
            print(f'用户{user_id}验证成功')
            car = self.user_service.get_user_car(user_id)
            print(f'获取用户{user_id}车辆信息成功')
            response = {
                'status': 'success',
                'message': '登录成功',
                'data': {
                    'user_id': user.user_id,
                    'car_id': car.car_id if car else None
                }
            }
            print(f'生成登录响应：{response}')
            return response
        except Exception as e:
            print(f'处理登录请求时发生异常：{str(e)}')
            return {'status': 'error', 'message': str(e)}
    
    def _handle_charging_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理充电请求"""
        try:
            # 获取并验证参数
            car_id = data.get('car_id')
            request_mode = data.get('request_mode')
            amount = data.get('amount')
            
            if not car_id or not request_mode or not amount:
                return {
                    'status': 'error',
                    'message': '缺少必要参数'
                }
            
            # 验证充电模式
            try:
                # 将中文模式转换为枚举值
                if request_mode == "快充":
                    request_mode = "FAST"
                elif request_mode == "慢充":
                    request_mode = "TRICKLE"
                else:
                    return {
                        'status': 'error',
                        'message': '无效的充电模式'
                    }
            except ValueError:
                return {
                    'status': 'error',
                    'message': '无效的充电模式'
                }
            
            # 验证充电量
            try:
                amount = float(amount)
                if amount <= 0:
                    return {
                        'status': 'error',
                        'message': '充电量必须大于0'
                    }
            except ValueError:
                return {
                    'status': 'error',
                    'message': '充电量必须是数字'
                }
            
            # 创建充电请求
            request = self.charging_service.create_charging_request(
                car_id, request_mode, amount
            )
            
            if not request or not request.queue_number:
                return {
                    'status': 'error',
                    'message': '创建充电请求失败'
                }
            
            return {
                'status': 'success',
                'message': '充电请求已提交',
                'data': {
                    'queue_number': request.queue_number
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'提交充电请求失败: {str(e)}'
            }
    
    def _handle_end_charging(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理结束充电请求"""
        try:
            car_id = data.get('car_id')
            if not car_id:
                return {'status': 'error', 'message': '缺少车辆ID'}

            print(f"[Server] 正在处理车辆 {car_id} 的结束充电请求...")
            
            bill = self.charging_service.end_charging(car_id)
            if bill:
                return {
                    'status': 'success',
                    'message': '充电已结束',
                    'data': {
                        'bill': bill.to_dict()
                    }
                }
            else:
                return {'status': 'error', 'message': '结束充电失败'}
        except Exception as e:
            error_msg = f"结束充电失败: {str(e)}"
            print(f"[Server] {error_msg}")
            return {'status': 'error', 'message': error_msg}
    
    def _handle_get_charging_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取充电详情的请求"""
        try:
            car_id = data.get('car_id')
            if not car_id:
                return {'status': 'error', 'message': '缺少车辆ID'}

            print(f"[Server] 正在获取车辆 {car_id} 的充电详情...")

            # 获取当前充电请求
            current_request = self.request_repo.find_by_id(car_id)
            print(f"[Server] 当前充电请求: {current_request.to_dict() if current_request else None}")

            # 获取当前充电会话
            current_session = None
            for session in self.session_repo.get_all():
                if session.car_id == car_id:
                    current_session = session
                    break
            
            # 如果找到了充电会话但请求状态不是充电中，说明状态不一致，需要清理
            if current_session and (not current_request or current_request.state != CarState.CHARGING):
                self.session_repo.delete(current_session.session_id)
                current_session = None
            print(f"[Server] 当前充电会话: {current_session.to_dict() if current_session else None}")

            # 获取历史账单
            bills = [bill for bill in self.bill_repo.get_all() if bill.car_id == car_id]
            print(f"[Server] 历史账单数量: {len(bills)}")

            # 如果请求已完成且没有当前会话，则清除当前请求
            if current_request and current_request.state == CarState.CHARGING_COMPLETED and not current_session:
                current_request = None

            # 构建响应数据
            response_data = {
                'status': 'success',
                'data': {
                    'current_request': current_request.to_dict() if current_request else None,
                    'current_session': current_session.to_dict() if current_session else None,
                    'bills': [bill.to_dict() for bill in sorted(bills, key=lambda x: x.end_time, reverse=True)]
                }
            }

            print(f"[Server] 充电详情获取成功")
            return response_data

        except Exception as e:
            error_msg = f"获取充电详情失败: {str(e)}"
            print(f"[Server] {error_msg}")
            return {'status': 'error', 'message': error_msg}
    
    def _handle_get_all_piles(self) -> Dict[str, Any]:
        """处理获取所有充电桩数据的请求"""
        try:
            piles = self.pile_repo.get_all()
            return {
                'status': 'success',
                'data': [pile.to_dict() for pile in piles]
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_toggle_pile_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理切换充电桩状态的请求"""
        try:
            pile_id = data.get('pile_id')
            start = data.get('start', True)
            
            pile = self.pile_repo.get(pile_id)
            if not pile:
                return {'status': 'error', 'message': '充电桩不存在'}
            
            if start:
                pile.set_state(WorkState.IDLE)
            else:
                pile.set_state(WorkState.OFFLINE)
            
            self.pile_repo.save(pile_id, pile)
            return {'status': 'success', 'message': '状态更新成功'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_get_pile_queue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取充电桩排队信息的请求"""
        try:
            pile_id = data.get('pile_id')
            pile = self.pile_repo.get(pile_id)
            if not pile:
                return {'status': 'error', 'message': '充电桩不存在'}
            
            queue = self.queue_service.get_queue_status(pile.pile_type)
            queue_data = []
            
            for request in queue:
                if request.pile_id == pile_id:
                    queue_data.append({
                        'user_id': request.car_id,
                        'battery_capacity': request.request_amount_kwh,
                        'request_amount': request.request_amount_kwh,
                        'waiting_time': (datetime.now() - request.request_time).total_seconds() / 3600
                    })
            
            return {
                'status': 'success',
                'data': queue_data
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _handle_get_reports(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取报表数据的请求"""
        try:
            time_range = data.get('time_range', 'day')
            # TODO: 实现实际的报表数据生成逻辑
            return {
                'status': 'success',
                'data': []
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

if __name__ == '__main__':
    server = ChargeServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n服务器正在关闭...")
    finally:
        server.stop()