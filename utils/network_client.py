import socket
import json
import time
import threading
from typing import Dict, Any, Optional, List
from functools import wraps

def retry_on_failure(max_retries=3, delay=1):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # 指数退避
                        continue
            raise last_exception
        return wrapper
    return decorator

class NetworkClient:
    def __init__(self, host: str = 'localhost', port: int = 5000):
        self.host = host
        self.port = port
        self.socket = None
        self._lock = threading.Lock()
    
    def connect(self) -> bool:
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)  # 延长超时时间至30秒
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"连接服务器失败：{str(e)}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """断开与服务器的连接"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None
    
    @retry_on_failure(max_retries=5, delay=2)
    def send_request(self, action: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """发送请求到服务器并获取响应"""
        with self._lock:
            if not self.socket:
                if not self.connect():
                    raise ConnectionError("无法连接到服务器")
            
            try:
                # 构造请求
                request = {
                    'action': action,
                    'data': data
                }
                print(f"[NetworkClient] 发送请求: {request}")  # 添加请求日志
                
                # 发送请求
                request_data = json.dumps(request).encode('utf-8')
                self.socket.sendall(request_data)
                
                # 接收响应
                response_data = b''
                while True:
                    try:
                        chunk = self.socket.recv(4096)
                        if not chunk:
                            break
                        response_data += chunk
                        # 尝试解析JSON，如果成功则说明收到了完整的响应
                        try:
                            response = json.loads(response_data.decode('utf-8'))
                            break
                        except json.JSONDecodeError:
                            continue
                    except socket.timeout:
                        raise ConnectionError("接收响应超时")
                    except socket.error as e:
                        if e.winerror == 10038:  # 捕获非套接字操作错误
                            break
                        else:
                            raise
                
                if not response_data:
                    raise ConnectionError("服务器断开连接")
                
                # 解析响应
                response = json.loads(response_data.decode('utf-8'))
                if response.get('status') == 'error':
                    raise ValueError(response.get('message', '未知错误'))
                
                return response
                
            except (socket.timeout, ConnectionError) as e:
                self.disconnect()
                raise ConnectionError(f"网络错误: {str(e)}")
            except json.JSONDecodeError as e:
                raise ValueError(f"服务器响应格式错误: {str(e)}")
            except Exception as e:
                self.disconnect()
                raise
    
    def register(self, user_id: str, password: str, car_id: str, battery_capacity: float) -> bool:
        """注册新用户"""
        try:
            response = self.send_request('register', {
                'user_id': user_id,
                'password': password,
                'car_id': car_id,
                'battery_capacity': battery_capacity
            })
            return response.get('status') == 'success'
        except Exception as e:
            raise ConnectionError(f"注册失败: {str(e)}")
    
    def login(self, user_id: str, password: str) -> Optional[Dict[str, Any]]:
        """用户登录"""
        try:
            response = self.send_request('login', {
                'user_id': user_id,
                'password': password
            })
            if response and response.get('status') == 'success':
                return response.get('data')
            return None
        except Exception as e:
            print(f"登录失败: {str(e)}")
            return None
    
    def submit_charging_request(self, car_id: str, request_mode: str, amount: float) -> Optional[str]:
        """提交充电请求"""
        try:
            response = self.send_request('submit_charging_request', {
                'car_id': car_id,
                'request_mode': request_mode,
                'amount': amount
            })
            if response and response.get('status') == 'success':
                return response.get('data', {}).get('queue_number')
            return None
        except Exception as e:
            print(f"提交充电请求失败: {str(e)}")
            return None
    
    def end_charging(self, car_id: str) -> bool:
        """结束充电"""
        try:
            response = self.send_request('end_charging', {
                'car_id': car_id
            })
            return response and response.get('status') == 'success'
        except Exception as e:
            print(f"结束充电失败: {str(e)}")
            return False
    
    def get_charging_details(self, car_id: str) -> Optional[Dict[str, Any]]:
        """获取充电详单"""
        try:
            response = self.send_request('get_charging_details', {
                'car_id': car_id
            })
            if response and response.get('status') == 'success':
                return response.get('data')
            return None
        except Exception as e:
            print(f"获取充电详单失败: {str(e)}")
            return None
    
    def get_all_piles(self) -> List[Dict[str, Any]]:
        """获取所有充电桩数据"""
        response = self.send_request('get_all_piles', {})
        if response and response.get('status') == 'success':
            return response.get('data', [])
        return []
    
    def toggle_pile_state(self, pile_id: str, start: bool) -> bool:
        """切换充电桩状态"""
        response = self.send_request('toggle_pile_state', {
            'pile_id': pile_id,
            'start': start
        })
        return response and response.get('status') == 'success'
    
    def get_pile_queue(self, pile_id: str) -> List[Dict[str, Any]]:
        """获取充电桩排队信息"""
        response = self.send_request('get_pile_queue', {
            'pile_id': pile_id
        })
        if response and response.get('status') == 'success':
            return response.get('data', [])
        return []
    
    def get_reports(self, time_range: str) -> List[Dict[str, Any]]:
        """获取报表数据"""
        response = self.send_request('get_reports', {
            'time_range': time_range
        })
        if response and response.get('status') == 'success':
            return response.get('data', [])
        return []