import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from models.charging_pile import ChargingPile
from utils.enums import WorkState, ChargeMode
from utils.network_client import NetworkClient

class AdminClient(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("充电站管理员客户端")
        self.geometry("1000x700")
        
        # 初始化网络客户端
        self.network_client = NetworkClient()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 初始化界面
        self.show_login_frame()
    
    def show_login_frame(self):
        """显示登录界面"""
        self.clear_main_frame()
        
        # 登录框架
        login_frame = ttk.LabelFrame(self.main_frame, text="管理员登录", padding=20)
        login_frame.pack(pady=50)
        
        # 用户名
        ttk.Label(login_frame, text="管理员ID:").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = ttk.Entry(login_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 密码
        ttk.Label(login_frame, text="密码:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 登录按钮
        ttk.Button(login_frame, text="登录", command=self.login).grid(row=2, column=0, columnspan=2, pady=20)
    
    def show_main_menu(self):
        """显示主菜单"""
        self.clear_main_frame()
        
        # 菜单框架
        menu_frame = ttk.LabelFrame(self.main_frame, text="管理员菜单", padding=20)
        menu_frame.pack(pady=50)
        
        # 功能按钮
        ttk.Button(menu_frame, text="充电桩管理", command=self.show_pile_management).pack(fill=tk.X, pady=5)
        ttk.Button(menu_frame, text="查看报表", command=self.show_reports).pack(fill=tk.X, pady=5)
        ttk.Button(menu_frame, text="退出登录", command=self.logout).pack(fill=tk.X, pady=5)
    
    def show_pile_management(self):
        """显示充电桩管理界面"""
        self.clear_main_frame()
        
        # 创建主容器
        main_container = ttk.Frame(self.main_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 创建标题
        title_label = ttk.Label(main_container, text="充电桩管理", font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # 创建控制面板
        control_frame = ttk.Frame(main_container)
        control_frame.pack(fill=tk.X, pady=10)
        
        # 左侧控制区
        left_control = ttk.Frame(control_frame)
        left_control.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 充电桩选择
        ttk.Label(left_control, text="选择充电桩:").pack(side=tk.LEFT, padx=5)
        self.pile_id_var = tk.StringVar()
        self.pile_combo = ttk.Combobox(left_control, textvariable=self.pile_id_var, width=10)
        self.pile_combo.pack(side=tk.LEFT, padx=5)
        
        # 操作按钮
        action_frame = ttk.Frame(left_control)
        action_frame.pack(side=tk.LEFT, padx=20)
        ttk.Button(action_frame, text="启动充电桩", command=self.start_pile).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="关闭充电桩", command=self.stop_pile).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="查看排队信息", command=self.show_queue_info).pack(side=tk.LEFT, padx=5)
        
        # 右侧控制区
        right_control = ttk.Frame(control_frame)
        right_control.pack(side=tk.RIGHT)
        ttk.Button(right_control, text="刷新数据", command=self.refresh_pile_data).pack(side=tk.RIGHT)
        
        # 创建表格容器
        table_frame = ttk.Frame(main_container)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建表格
        columns = ("充电桩ID", "状态", "类型", "累计充电次数", "累计充电时长(小时)", "累计充电量(度)", "累计收入(元)")
        self.pile_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # 设置列标题
        for col in columns:
            self.pile_tree.heading(col, text=col)
            self.pile_tree.column(col, width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.pile_tree.yview)
        self.pile_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局表格和滚动条
        self.pile_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建底部按钮容器
        bottom_frame = ttk.Frame(main_container)
        bottom_frame.pack(fill=tk.X, pady=20)
        
        # 添加返回按钮
        ttk.Button(bottom_frame, text="返回主菜单", command=self.show_main_menu).pack(side=tk.LEFT, padx=10)
        
        # 加载充电桩数据
        self.refresh_pile_data()
    
    def show_reports(self):
        """显示报表界面"""
        self.clear_main_frame()
        
        # 报表框架
        report_frame = ttk.LabelFrame(self.main_frame, text="报表查看", padding=20)
        report_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 时间范围选择
        time_frame = ttk.Frame(report_frame)
        time_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(time_frame, text="时间范围:").pack(side=tk.LEFT, padx=5)
        self.time_range = tk.StringVar(value="day")
        ttk.Radiobutton(time_frame, text="日", variable=self.time_range, value="day").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(time_frame, text="周", variable=self.time_range, value="week").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(time_frame, text="月", variable=self.time_range, value="month").pack(side=tk.LEFT, padx=5)
        
        # 创建表格
        columns = ("时间", "充电桩编号", "累计充电次数", "累计充电时长", 
                  "累计充电量", "累计充电费用", "累计服务费用", "累计总费用")
        self.report_tree = ttk.Treeview(report_frame, columns=columns, show="headings")
        
        # 设置列标题
        for col in columns:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=self.report_tree.yview)
        self.report_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 刷新按钮
        ttk.Button(report_frame, text="刷新报表", command=self.refresh_report).pack(pady=10)
        
        # 返回按钮
        ttk.Button(self.main_frame, text="返回主菜单", command=self.show_main_menu).pack(pady=10)
    
    def show_queue_info(self):
        """显示排队车辆信息"""
        pile_id = self.pile_id_var.get()
        if not pile_id:
            messagebox.showerror("错误", "请选择充电桩")
            return
        
        try:
            # 获取排队信息
            queue_data = self.network_client.get_pile_queue(pile_id)
            
            # 创建新窗口
            queue_window = tk.Toplevel(self)
            queue_window.title(f"充电桩 {pile_id} 排队信息")
            queue_window.geometry("800x500")
            
            # 创建表格
            columns = ("用户ID", "车辆电池总容量(度)", "请求充电量(度)", "排队时长(小时)")
            queue_tree = ttk.Treeview(queue_window, columns=columns, show="headings")
            
            # 设置列标题
            for col in columns:
                queue_tree.heading(col, text=col)
                queue_tree.column(col, width=150)
            
            # 添加滚动条
            scrollbar = ttk.Scrollbar(queue_window, orient=tk.VERTICAL, command=queue_tree.yview)
            queue_tree.configure(yscrollcommand=scrollbar.set)
            
            # 布局
            queue_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            
            # 填充数据
            for vehicle in queue_data:
                queue_tree.insert('', 'end', values=(
                    vehicle['user_id'],
                    f"{vehicle['battery_capacity']:.2f}",
                    f"{vehicle['request_amount']:.2f}",
                    f"{vehicle['waiting_time']:.2f}"
                ))
            
            # 添加刷新按钮
            refresh_frame = ttk.Frame(queue_window)
            refresh_frame.pack(fill=tk.X, padx=10, pady=5)
            ttk.Button(refresh_frame, text="刷新数据", 
                      command=lambda: self.refresh_queue_info(queue_tree, pile_id)).pack(side=tk.RIGHT)
            
            # 如果没有排队车辆，显示提示信息
            if not queue_data:
                queue_tree.insert('', 'end', values=("暂无排队车辆", "", "", ""))
                
        except Exception as e:
            messagebox.showerror("错误", f"获取排队信息失败: {str(e)}")
    
    def refresh_queue_info(self, queue_tree, pile_id):
        """刷新排队信息"""
        try:
            # 清空现有数据
            for item in queue_tree.get_children():
                queue_tree.delete(item)
            
            # 获取新的排队信息
            queue_data = self.network_client.get_pile_queue(pile_id)
            
            # 填充数据
            for vehicle in queue_data:
                queue_tree.insert('', 'end', values=(
                    vehicle['user_id'],
                    f"{vehicle['battery_capacity']:.2f}",
                    f"{vehicle['request_amount']:.2f}",
                    f"{vehicle['waiting_time']:.2f}"
                ))
            
            # 如果没有排队车辆，显示提示信息
            if not queue_data:
                queue_tree.insert('', 'end', values=("暂无排队车辆", "", "", ""))
                
        except Exception as e:
            messagebox.showerror("错误", f"刷新排队信息失败: {str(e)}")
    
    def clear_main_frame(self):
        """清除主框架中的所有组件"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def login(self):
        """处理登录"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        # TODO: 实现实际的登录逻辑
        if username and password:
            self.show_main_menu()
        else:
            messagebox.showerror("错误", "请输入用户名和密码")
    
    def start_pile(self):
        """启动充电桩"""
        pile_id = self.pile_id_var.get()
        if not pile_id:
            messagebox.showerror("错误", "请选择充电桩")
            return
            
        try:
            # 调用网络客户端启动充电桩
            if self.network_client.toggle_pile_state(pile_id, True):
                messagebox.showinfo("成功", f"充电桩 {pile_id} 已启动")
                self.refresh_pile_data()  # 刷新显示
            else:
                messagebox.showerror("错误", f"启动充电桩 {pile_id} 失败")
        except Exception as e:
            messagebox.showerror("错误", f"启动充电桩失败: {str(e)}")
    
    def stop_pile(self):
        """关闭充电桩"""
        pile_id = self.pile_id_var.get()
        if not pile_id:
            messagebox.showerror("错误", "请选择充电桩")
            return
            
        try:
            # 调用网络客户端关闭充电桩
            if self.network_client.toggle_pile_state(pile_id, False):
                messagebox.showinfo("成功", f"充电桩 {pile_id} 已关闭")
                self.refresh_pile_data()  # 刷新显示
            else:
                messagebox.showerror("错误", f"关闭充电桩 {pile_id} 失败")
        except Exception as e:
            messagebox.showerror("错误", f"关闭充电桩失败: {str(e)}")
    
    def refresh_report(self):
        """刷新报表数据"""
        # TODO: 实现实际的报表数据刷新逻辑
        messagebox.showinfo("成功", "报表已刷新")
    
    def logout(self):
        """退出登录"""
        self.show_login_frame()
    
    def refresh_pile_data(self):
        """刷新充电桩数据"""
        try:
            # 清空现有数据
            for item in self.pile_tree.get_children():
                self.pile_tree.delete(item)
            
            # 获取充电桩数据
            piles = self.network_client.get_all_piles()
            if not piles:
                messagebox.showwarning("警告", "没有找到充电桩数据")
                return
            
            # 更新下拉框选项
            pile_ids = [pile['pile_id'] for pile in piles]
            self.pile_combo['values'] = pile_ids
            if pile_ids and not self.pile_id_var.get():
                self.pile_id_var.set(pile_ids[0])
            
            # 填充表格数据
            for pile in piles:
                self.pile_tree.insert('', 'end', values=(
                    pile['pile_id'],
                    pile['state'],
                    pile['pile_type'],
                    pile['total_charging_count'],
                    f"{pile['total_charging_time']:.2f}",
                    f"{pile['total_charged_kwh']:.2f}",
                    f"{pile['total_income']:.2f}"
                ))
        except Exception as e:
            messagebox.showerror("错误", f"获取充电桩数据失败: {str(e)}")

if __name__ == "__main__":
    app = AdminClient()
    app.mainloop() 