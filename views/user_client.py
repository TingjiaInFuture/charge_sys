import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from utils.enums import ChargeMode, CarState
from utils.network_client import NetworkClient

class UserClient(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("充电站用户客户端")
        self.geometry("800x600")
        
        # 初始化网络客户端
        self.network_client = NetworkClient()
        
        # 用户信息
        self.user_id = None
        self.car_id = None
        
        # 创建主框架
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 初始化界面
        self.show_login_frame()
    
    def show_login_frame(self):
        """显示登录界面"""
        self.clear_main_frame()
        
        # 登录框架
        login_frame = ttk.LabelFrame(self.main_frame, text="用户登录", padding=20)
        login_frame.pack(pady=20)
        
        # 用户ID
        ttk.Label(login_frame, text="用户ID:").grid(row=0, column=0, padx=5, pady=5)
        self.user_id_entry = ttk.Entry(login_frame)
        self.user_id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 密码
        ttk.Label(login_frame, text="密码:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(login_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="登录", command=self.login).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="注册", command=self.show_register_frame).pack(side=tk.LEFT, padx=5)
    
    def show_register_frame(self):
        """显示注册界面"""
        self.clear_main_frame()
        
        # 注册框架
        register_frame = ttk.LabelFrame(self.main_frame, text="用户注册", padding=20)
        register_frame.pack(pady=20)
        
        # 用户ID
        ttk.Label(register_frame, text="用户ID:").grid(row=0, column=0, padx=5, pady=5)
        self.reg_user_id_entry = ttk.Entry(register_frame)
        self.reg_user_id_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(register_frame, text="(4-20位字母、数字或下划线)").grid(row=0, column=2, padx=5, pady=5)
        
        # 密码
        ttk.Label(register_frame, text="密码:").grid(row=1, column=0, padx=5, pady=5)
        self.reg_password_entry = ttk.Entry(register_frame, show="*")
        self.reg_password_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(register_frame, text="(至少8位，包含大小写字母、数字和特殊字符)").grid(row=1, column=2, padx=5, pady=5)
        
        # 车辆ID
        ttk.Label(register_frame, text="车辆ID:").grid(row=2, column=0, padx=5, pady=5)
        self.car_id_entry = ttk.Entry(register_frame)
        self.car_id_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(register_frame, text="(4-10位大写字母或数字)").grid(row=2, column=2, padx=5, pady=5)
        
        # 电池容量
        ttk.Label(register_frame, text="电池容量(kWh):").grid(row=3, column=0, padx=5, pady=5)
        self.battery_capacity_entry = ttk.Entry(register_frame)
        self.battery_capacity_entry.grid(row=3, column=1, padx=5, pady=5)
        ttk.Label(register_frame, text="(0-100kWh)").grid(row=3, column=2, padx=5, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(register_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="注册", command=self.register).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="返回登录", command=self.show_login_frame).pack(side=tk.LEFT, padx=5)
    
    def show_main_menu(self):
        """显示主菜单"""
        self.clear_main_frame()
        
        # 主菜单框架
        menu_frame = ttk.LabelFrame(self.main_frame, text="主菜单", padding=20)
        menu_frame.pack(pady=20)
        
        # 用户信息
        ttk.Label(menu_frame, text=f"用户ID: {self.user_id}").pack(pady=5)
        ttk.Label(menu_frame, text=f"车辆ID: {self.car_id}").pack(pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(menu_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="提交充电请求", command=self.show_charging_request_frame).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="查看充电详单", command=self.show_charging_details).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="查看本车排队号码", command=self.show_queue_number).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="查看本充电模式下前车等待数量", command=self.show_waiting_count).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="结束充电", command=self.end_charging).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="退出登录", command=self.logout).pack(side=tk.LEFT, padx=5)
    
    def show_charging_request_frame(self):
        """显示充电请求界面"""
        self.clear_main_frame()
        
        # 充电请求框架
        request_frame = ttk.LabelFrame(self.main_frame, text="提交充电请求", padding=20)
        request_frame.pack(pady=20)
        
        # 充电模式
        ttk.Label(request_frame, text="充电模式:").grid(row=0, column=0, padx=5, pady=5)
        self.charge_mode_var = tk.StringVar(value=ChargeMode.FAST.value)
        ttk.Radiobutton(request_frame, text="快速充电", variable=self.charge_mode_var, 
                       value=ChargeMode.FAST.value).grid(row=0, column=1, padx=5, pady=5)
        ttk.Radiobutton(request_frame, text="慢速充电", variable=self.charge_mode_var,
                       value=ChargeMode.TRICKLE.value).grid(row=0, column=2, padx=5, pady=5)
        
        # 充电量
        ttk.Label(request_frame, text="充电量(kWh):").grid(row=1, column=0, padx=5, pady=5)
        self.charge_amount_entry = ttk.Entry(request_frame)
        self.charge_amount_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(request_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="提交", command=self.submit_charging_request).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="返回主菜单", command=self.show_main_menu).pack(side=tk.LEFT, padx=5)
    
    def login(self):
        """用户登录"""
        user_id = self.user_id_entry.get()
        password = self.password_entry.get()
        
        if not user_id or not password:
            messagebox.showerror("错误", "请输入用户ID和密码")
            return
        
        try:
            result = self.network_client.login(user_id, password)
            if result:
                self.user_id = result['user_id']
                self.car_id = result['car_id']
                messagebox.showinfo("成功", "登录成功")
                self.show_main_menu()
            else:
                messagebox.showerror("错误", "登录失败，请检查用户ID和密码")
        except Exception as e:
            messagebox.showerror("错误", f"登录失败: {str(e)}")
    
    def register(self):
        """用户注册（异步版本）"""
        def async_register():
            try:
                # 获取输入
                user_id = self.reg_user_id_entry.get().strip()
                password = self.reg_password_entry.get()
                car_id = self.car_id_entry.get().strip()
                battery_capacity = self.battery_capacity_entry.get().strip()
                
                # 验证输入
                if not all([user_id, password, car_id, battery_capacity]):
                    self.after(0, lambda: messagebox.showerror("错误", "请填写所有字段"))
                    return
                
                # 尝试注册
                result = self.network_client.register(user_id, password, car_id, float(battery_capacity))
                self.after(0, lambda:
                    messagebox.showinfo("成功", "注册成功！请登录") if result
                    else messagebox.showerror("错误", "注册失败，请稍后重试")
                )
                if result:
                    self.after(0, self.show_login_frame)
            except ValueError as e:
                self.after(0, lambda: messagebox.showerror("输入错误", str(e)))
            except ConnectionError as e:
                self.after(0, lambda:
                    messagebox.showerror("网络错误", str(e))
                )
                # 尝试重新连接
                if messagebox.askyesno("连接错误", "是否要尝试重新连接？"):
                    self.network_client.disconnect()
                    if self.network_client.connect():
                        self.after(0, lambda: messagebox.showinfo("成功", "重新连接成功，请重试注册"))
                    else:
                        self.after(0, lambda: messagebox.showerror("错误", "重新连接失败，请检查服务器状态"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("错误", f"注册失败: {str(e)}"))
                print(f"注册时发生错误: {str(e)}")
        
        # 启动异步线程执行注册
        import threading
        threading.Thread(target=async_register, daemon=True).start()
    
    def submit_charging_request(self):
        """提交充电请求"""
        request_mode = self.charge_mode_var.get()
        amount = self.charge_amount_entry.get()
        
        if not amount:
            messagebox.showerror("错误", "请输入充电量")
            return
        
        try:
            amount = float(amount)
            if amount <= 0:
                messagebox.showerror("错误", "充电量必须大于0")
                return
        except ValueError:
            messagebox.showerror("错误", "充电量必须是数字")
            return
        
        try:
            queue_number = self.network_client.submit_charging_request(
                self.car_id, request_mode, amount
            )
            if queue_number:
                messagebox.showinfo("成功", f"充电请求已提交，排队号码：{queue_number}")
                self.show_main_menu()
            else:
                messagebox.showerror("错误", "提交充电请求失败")
        except Exception as e:
            messagebox.showerror("错误", f"提交充电请求失败: {str(e)}")
    
    def show_charging_details(self):
        """显示充电详情"""
        # 清空主框架
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
        # 创建详情框架
        details_frame = ttk.Frame(self.main_frame)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
        # 创建表格
        columns = ("状态", "时间", "充电桩", "充电量(kWh)", "时长(h)", "开始时间", "结束时间", "充电费用", "服务费用", "总费用")
        tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=10)
        
        # 设置列标题和宽度
        column_widths = {
            "状态": 80,
            "时间": 150,
            "充电桩": 80,
            "充电量(kWh)": 100,
            "时长(h)": 80,
            "开始时间": 150,
            "结束时间": 150,
            "充电费用": 100,
            "服务费用": 100,
            "总费用": 100
        }
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=column_widths[col], anchor="center")
    
        # 添加滚动条
        scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
        try:
            # 获取充电详情
            response = self.network_client.send_request('get_charging_details', {
                'car_id': self.car_id
            })
    
            if response.get('status') == 'success':
                data = response.get('data', {})
                
                # 显示当前会话
                current_session = data.get('current_session')
                if current_session:
                    start_time = datetime.fromisoformat(current_session['start_time'])
                    duration = (datetime.now() - start_time).total_seconds() / 3600
                    tree.insert("", 0, values=(
                        "充电中",
                        start_time.strftime("%Y-%m-%d %H:%M:%S"),
                        current_session['pile_id'],
                        f"{current_session['request_amount_kwh']:.2f}",
                        f"{duration:.2f}",
                        start_time.strftime("%Y-%m-%d %H:%M:%S"),
                        '',
                        '',
                        '',
                        ''
                    ))
    
                # 显示历史账单
                bills = data.get('bills', [])
                for bill in bills:
                    start_time = datetime.fromisoformat(bill['start_time'])
                    end_time = datetime.fromisoformat(bill['end_time'])
                    duration = (end_time - start_time).total_seconds() / 3600
                    tree.insert("", "end", values=(
                        "已完成",
                        end_time.strftime("%Y-%m-%d %H:%M:%S"),
                        bill['pile_id'],
                        f"{bill['charged_kwh']:.2f}",
                        f"{duration:.2f}",
                        start_time.strftime("%Y-%m-%d %H:%M:%S"),
                        end_time.strftime("%Y-%m-%d %H:%M:%S"),
                        f"¥{bill['charge_fee']:.2f}",
                        f"¥{bill['service_fee']:.2f}",
                        f"¥{bill['total_fee']:.2f}"
                    ))
    
                if not (current_session or bills):
                    ttk.Label(details_frame, text="暂无充电记录").pack(pady=20)
            else:
                ttk.Label(details_frame, text=f"获取充电详情失败: {response.get('message', '未知错误')}").pack(pady=20)
        except Exception as e:
            ttk.Label(details_frame, text=f"获取充电详情时发生错误: {str(e)}").pack(pady=20)
    
        # 添加返回按钮
        ttk.Button(self.main_frame, text="返回", command=self.show_main_menu).pack(pady=10)
    
    def logout(self):
        """退出登录"""
        self.user_id = None
        self.car_id = None
        self.network_client.disconnect()
        self.show_login_frame()
    
    def clear_main_frame(self):
        """清空主框架"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def __del__(self):
        """析构函数"""
        if hasattr(self, 'network_client'):
            self.network_client.disconnect()

    def show_queue_number(self):
        """显示本车排队号码"""
        try:
            # 获取充电详情
            response = self.network_client.get_charging_details(self.car_id)
            if response and response.get('status') == 'success':
                data = response.get('data', {})
                current_request = data.get('current_request')
                
                if current_request and current_request.get('queue_number'):
                    messagebox.showinfo("排队号码", f"您的排队号码是：{current_request['queue_number']}")
                else:
                    messagebox.showinfo("提示", "您当前没有排队中的充电请求")
            else:
                messagebox.showerror("错误", "获取排队号码失败")
        except Exception as e:
            messagebox.showerror("错误", f"获取排队号码失败: {str(e)}")

    def show_waiting_count(self):
        """显示本充电模式下前车等待数量"""
        try:
            # 获取充电详情
            response = self.network_client.get_charging_details(self.car_id)
            if response and response.get('status') == 'success':
                data = response.get('data', {})
                current_request = data.get('current_request')
                
                if current_request:
                    # 获取所有充电桩
                    piles = self.network_client.get_all_piles()
                    waiting_count = 0
                    
                    # 统计同模式下等待的车辆数量
                    for pile in piles:
                        if pile['pile_type'] == current_request['request_mode']:
                            queue_data = self.network_client.get_pile_queue(pile['pile_id'])
                            waiting_count += len(queue_data)
                    
                    messagebox.showinfo("等待数量", f"当前充电模式下共有 {waiting_count} 辆车在等待")
                else:
                    messagebox.showinfo("提示", "您当前没有排队中的充电请求")
            else:
                messagebox.showerror("错误", "获取等待数量失败")
        except Exception as e:
            messagebox.showerror("错误", f"获取等待数量失败: {str(e)}")

    def end_charging(self):
        """结束充电"""
        try:
            if messagebox.askyesno("确认", "确定要结束当前充电吗？"):
                if self.network_client.end_charging(self.car_id):
                    messagebox.showinfo("成功", "充电已结束")
                    self.show_main_menu()
                else:
                    messagebox.showerror("错误", "结束充电失败")
        except Exception as e:
            messagebox.showerror("错误", f"结束充电失败: {str(e)}")

if __name__ == "__main__":
    app = UserClient()
    app.mainloop()