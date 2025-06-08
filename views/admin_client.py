import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from models.charging_pile import ChargingPile
from utils.enums import WorkState, ChargeMode

class AdminClient(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("充电站管理员客户端")
        self.geometry("1000x700")
        
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
        
        # 管理框架
        management_frame = ttk.LabelFrame(self.main_frame, text="充电桩管理", padding=20)
        management_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建表格
        columns = ("充电桩ID", "类型", "状态", "累计充电次数", "累计充电时长", "累计充电量")
        self.pile_tree = ttk.Treeview(management_frame, columns=columns, show="headings")
        
        # 设置列标题
        for col in columns:
            self.pile_tree.heading(col, text=col)
            self.pile_tree.column(col, width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(management_frame, orient=tk.VERTICAL, command=self.pile_tree.yview)
        self.pile_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.pile_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 控制按钮框架
        control_frame = ttk.Frame(management_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        # 选择充电桩
        ttk.Label(control_frame, text="选择充电桩:").pack(side=tk.LEFT, padx=5)
        self.pile_id_var = tk.StringVar()
        self.pile_id_combo = ttk.Combobox(control_frame, textvariable=self.pile_id_var)
        self.pile_id_combo.pack(side=tk.LEFT, padx=5)
        
        # 操作按钮
        ttk.Button(control_frame, text="启动", command=lambda: self.toggle_pile_state(True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="关闭", command=lambda: self.toggle_pile_state(False)).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="查看排队车辆", command=self.show_queue_info).pack(side=tk.LEFT, padx=5)
        
        # 返回按钮
        ttk.Button(self.main_frame, text="返回主菜单", command=self.show_main_menu).pack(pady=10)
    
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
        
        # 创建新窗口
        queue_window = tk.Toplevel(self)
        queue_window.title(f"充电桩 {pile_id} 排队信息")
        queue_window.geometry("600x400")
        
        # 创建表格
        columns = ("用户ID", "车辆电池总容量", "请求充电量", "排队时长")
        queue_tree = ttk.Treeview(queue_window, columns=columns, show="headings")
        
        # 设置列标题
        for col in columns:
            queue_tree.heading(col, text=col)
            queue_tree.column(col, width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(queue_window, orient=tk.VERTICAL, command=queue_tree.yview)
        queue_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        queue_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # TODO: 实现实际的排队信息获取逻辑
    
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
    
    def toggle_pile_state(self, start: bool):
        """切换充电桩状态"""
        pile_id = self.pile_id_var.get()
        if not pile_id:
            messagebox.showerror("错误", "请选择充电桩")
            return
        
        # TODO: 实现实际的充电桩状态切换逻辑
        state = "启动" if start else "关闭"
        messagebox.showinfo("成功", f"充电桩 {pile_id} 已{state}")
    
    def refresh_report(self):
        """刷新报表数据"""
        # TODO: 实现实际的报表数据刷新逻辑
        messagebox.showinfo("成功", "报表已刷新")
    
    def logout(self):
        """退出登录"""
        self.show_login_frame()

if __name__ == "__main__":
    app = AdminClient()
    app.mainloop() 