# Copyright (c) 2024 lowyyh
# SPDX-License-Identifier: MIT

import ctypes
import pystray
import json
import tkinter as tk
from tkinter import ttk, messagebox
from winsound import MessageBeep, MB_ICONEXCLAMATION  # 用于播放提示音
from PIL import Image
from sys import exit
from os import system
from threading import Thread, Event, RLock
from datetime import datetime as dt, timedelta
import lib.stop
from pathlib import Path
import logging
import logging.handlers
import atexit
import signal
import copy


class LogProcessing:
    """日志处理"""
    def __init__(self, log_file_path:Path):
        self.log_file = Path(log_file_path)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            # 使用 RotatingFileHandler 防止日志文件过大
            handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )

            # 指定格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s'
            )
            handler.setFormatter(formatter)

            self.logger.addHandler(handler)

        # 注册退出处理
        atexit.register(self._cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _cleanup(self):
        """程序退出时清理资源"""
        self.logger.info("Application shutting down")
        logging.shutdown()

    def _signal_handler(self, signum, frame):
        """信号处理"""
        self.logger.info(f"Received signal {signum}, shutting down")
        self._cleanup()
        exit(0)

    def log(self, level, message, exc_info=None):
        """统一的日志记录方法"""
        try:
            if level == 'INFO':
                self.logger.info(message, exc_info=exc_info)

            elif level == 'ERROR':
                self.logger.error(message, exc_info=exc_info)

            elif level == 'WARNING':
                self.logger.warning(message, exc_info=exc_info)

            elif level == 'DEBUG':
                self.logger.debug(message, exc_info=exc_info)

        except Exception as error:
            # 如果日志记录本身失败，回退到标准输出
            print(f"Logging failed: {error}, Original message: {message}")

    # 便捷方法
    def info(self, message):
        self.log('INFO', message)

    def error(self, message, exc_info=False):
        self.log('ERROR', message, exc_info=exc_info)

    def warning(self, message):
        self.log('WARNING', message)

    def debug(self, message):
        self.log('DEBUG', message)


class Config:
    """配置处理"""
    def __init__(self, config_file_path:Path, configuration_information:dict, logger: LogProcessing):
        self._config = configuration_information
        self.config_file_path = config_file_path
        self.logger = logger
        self._lock = RLock()

    def get(self, key: str, default=None):
        with self._lock:
            return self._config.get(key, default)

    def set(self, key: str, value) -> None:
        with self._lock:
            self._config[key] = value

    def update(self, config_information: dict):  # 全部更新
        with self._lock:
            self._config = config_information

    def read(self):  # 完整字典
        with self._lock:
            return copy.deepcopy(self._config)  # 使用深度拷贝, 使用copy方法在ScheduleEditor.save中, 判断重复时会出bug

    def save(self):  # 保存
        try:
            with self.config_file_path.open("w", encoding="utf-8") as file:
                with self._lock:
                    json.dump(self._config, file, indent=2, ensure_ascii=False)

            return True

        except (OSError, PermissionError):
            self.logger.error("保存配置出错", exc_info=True)
            return False


class ShutdownApp(tk.Toplevel):
    """关机倒计时提示窗口"""

    def __init__(self, planning, timeout, logger: LogProcessing):
        super().__init__()
        self.lab = None
        self.t = timeout
        self.planning = planning
        self.title("关机提醒")
        self.geometry("610x190")
        self.wm_attributes("-topmost", True)
        self.logger = logger

        # 播放提示音
        MessageBeep(MB_ICONEXCLAMATION)

        # 创建界面元素
        self.create_widgets()
        self.start_countdown()

    def create_widgets(self):
        """创建界面组件"""
        # 倒计时标签
        self.lab = tk.Label(self, text=f"电脑将在{self.t}秒后关机!",
                            font=("", 35), fg="red")
        self.lab.pack(pady=10)

        # 按钮框架
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        # 立即关机按钮
        btn_shutdown = tk.Button(button_frame, text="现在关机",
                                 command=self.shutdown_now,
                                 width=15, height=2, bg="#ff4d4d")
        btn_shutdown.pack(side="left", padx=10)

        # 跳过计划按钮
        btn_skip = tk.Button(button_frame, text="跳过此计划",
                             command=self.skip_plan,
                             width=15, height=2, bg="#4da6ff")
        btn_skip.pack(side="left", padx=10)

    def start_countdown(self):
        """启动倒计时"""
        self.update_countdown()

    def update_countdown(self):
        """更新倒计时显示"""
        if self.t > 0:
            self.t -= 1
            self.lab.config(text=f"电脑将在{self.t}秒后关机!")
            self.after(1000, self.update_countdown)
        else:
            self.shutdown_now()

    def shutdown_now(self):
        """立即关机"""
        self.destroy()
        self.logger.info(f"正常执行计划 - {self.planning}")
        system("shutdown -s -f -t 02")
        exit_program()

    def skip_plan(self):
        """跳过当前计划"""
        self.destroy()
        self.logger.warning(f"用户跳过了计划 - {self.planning}")


class Scheduler:
    """关机计划调度器"""

    def __init__(self, config:Config, logger: LogProcessing):
        self.config = config
        self.stop_event = Event()
        self.logger = logger

    def run(self):
        """运行调度器主循环"""
        now = dt.now()
        self.logger.info("调度器开始运行")

        # 获取当天的计划
        weekday_key = str(now.weekday() + 1)  # 1=周一, 7=周日
        plans = self.config.get("plan", {}).get(weekday_key, [])

        if not plans:
            self.logger.warning("当天没有关机计划")
            # 等待到次日0点
            self.wait_until_next_day()

        # 处理当天的计划
        self.process_daily_plans(plans, now)

        # 当天计划处理完成后等待次日
        self.wait_until_next_day()

    def process_daily_plans(self, plans, current_time):
        """处理当天的关机计划"""

        for plan in plans:
            # 解析计划时间
            plan_parts = plan.split(':')
            if len(plan_parts) < 4:
                continue

            plan_time = dt(current_time.year, current_time.month, current_time.day,
                           int(plan_parts[0]), int(plan_parts[1]), int(plan_parts[2]))
            countdown = int(plan_parts[3])

            # 如果计划时间已过，则跳过
            if plan_time < current_time:
                continue

            else:
                # 等待计划时间到达
                wait_seconds = (plan_time - current_time).total_seconds()
                self.logger.info(f"等待计划执行: {plan} (等待时间: {wait_seconds:.0f}秒)")

                # 等待计划时间或提前终止
                if wait_seconds > 0:
                    self.stop_event.wait(timeout=wait_seconds)
                    if self.stop_event.is_set():
                        return

                # 执行计划
                self.execute_plan(plan, countdown)

            # 更新当前时间
            current_time = dt.now()

    def execute_plan(self, plan_str, countdown_seconds):
        """执行单个关机计划"""

        # # 解析倒计时时间
        # countdown_seconds = int(plan_str.split(':')[3])

        self.logger.info(f"执行关机计划: {plan_str}")

        # 创建并显示关机提示窗口
        # shutdown_app = ShutdownApp(countdown_seconds)
        # shutdown_app.mainloop()

        root.after(0, lambda: ShutdownApp(planning=plan_str, timeout=countdown_seconds, logger=self.logger))

    def wait_until_next_day(self):
        """等待到次日0点"""
        now = dt.now()
        next_day = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        wait_seconds = (next_day - now).total_seconds()

        self.logger.info(f"等待次日，休眠时间: {wait_seconds:.0f}秒")

        if wait_seconds > 0:
            self.stop_event.wait(timeout=wait_seconds)
            self.stop_event.clear()  # 重置事件


class TemporaryPlanDialog:
    """添加临时计划对话框"""

    def __init__(self, config:Config, logger: LogProcessing):
        self.countdown_entry = None
        self.time_entry = None
        self.window = None
        self.day = dt.now().weekday() + 1
        self.logger = logger
        self.tmp_config = config.read()

    def main(self):
        # 通过 root.after 把弹窗调度到主线程
        root.after(0, self._show_dialog)

    def _show_dialog(self):
        self.window = tk.Toplevel(root)
        self.window.title("添加临时关机计划")
        self.window.geometry("400x200")
        self.window.resizable(False, False)

        form_frame = ttk.Frame(self.window, padding=10)
        ttk.Label(form_frame, text="计划时间 (HH:MM:SS):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.time_entry = tk.Entry(form_frame, width=10)
        self.time_entry.insert(0, dt.now().strftime("%H:%M:%S"))
        self.time_entry.grid(row=0, column=1, sticky=tk.W, pady=5)

        ttk.Label(form_frame, text="倒计时 (秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.countdown_entry = tk.Entry(form_frame, width=10)
        self.countdown_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        self.countdown_entry.insert(0, "60")

        ttk.Label(form_frame, text="格式: 小时:分钟:秒", foreground="gray").grid(row=0, column=2, padx=5)
        ttk.Label(form_frame, text="例如: 20", foreground="gray").grid(row=1, column=2, padx=5)

        button_frame = ttk.Frame(self.window, padding=10)
        ttk.Button(button_frame, text="确定", command=self.confirm).pack(side="right", padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side="right", padx=5)

        form_frame.pack(fill="both", expand=True)
        button_frame.pack(fill="x")

    def confirm(self):
        """确认添加临时计划"""
        time_str = self.time_entry.get()
        countdown_str = self.countdown_entry.get()

        try:
            # 验证时间格式
            time_parts = time_str.split(':')
            if len(time_parts) != 3:
                raise ValueError("时间格式不正确")

            hour, minute, second = map(int, time_parts)
            if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
                raise ValueError("时间值超出范围")

            # 验证倒计时
            countdown = int(countdown_str)
            if countdown <= 0:
                raise ValueError("倒计时必须为正数")

            # 创建计划字符串
            plan = f"{hour:02d}:{minute:02d}:{second:02d}:{countdown}"

            self.tmp_config["plan"][str(self.day)].append(plan)
            self.tmp_config["plan"][str(self.day)] = dedup_time_strings(self.tmp_config["plan"][str(self.day)])

            # 重启调度器
            global scheduler, scheduler_thread
            lib.stop.stop_thread(scheduler_thread)

            # 创建新的调度器线程
            scheduler = Scheduler(Config(Path("./config/config.json"), self.tmp_config, self.logger), self.logger)
            scheduler_thread = Thread(target=scheduler.run)
            scheduler_thread.daemon = True
            scheduler_thread.start()

            self.logger.info(f"添加临时计划: {plan}")

            self.window.destroy()

        except ValueError as error:
            messagebox.showerror("输入错误", f"无效输入: {str(error)}")

    def cancel(self):
        """取消对话框"""
        self.window.destroy()


class ScheduleEditor:
    """计划编辑器(修改计划)"""

    def __init__(self, config:Config, logger: LogProcessing):
        self.config = config
        # self.old_config = config.read()  # 临时配置，防止未做更改却重启线程
        self.tmp_config = self.config.read()
        self.logger = logger

        self.day_frames = {}
        self.plan_entries = {}

    def main(self):
        root.after(0, self._show_dialog)

    def _show_dialog(self):
        self.window = tk.Toplevel(root)
        self.window.title("编辑关机计划")
        self.window.geometry("600x400")
        self.window.resizable(False, False)

        # 创建界面
        self.create_ui()

        # 加载数据
        self.load_data()

    def create_ui(self):
        """创建用户界面"""
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill="both", expand=True)

        # 创建标签框架
        tab_control = ttk.Notebook(main_frame)
        tab_control.pack(fill="both", expand=True, padx=5, pady=5)

        # 为每一天创建一个标签页
        self.day_frames = {}
        self.plan_entries = {}

        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for i, day in enumerate(days, start=1):
            frame = ttk.Frame(tab_control, padding=10)
            tab_control.add(frame, text=day)

            # 创建计划列表
            scrollbar = tk.Scrollbar(frame)
            scrollbar.pack(side="right", fill="y")

            listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, width=40, height=8)
            listbox.pack(fill="both", expand=True, pady=5)
            scrollbar.config(command=listbox.yview)

            # 添加按钮
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill="x", pady=5)

            ttk.Button(btn_frame, text="添加计划",
                       command=lambda d=i: self.add_plan(d)).pack(side="left", padx=2)
            ttk.Button(btn_frame, text="删除计划",
                       command=lambda lb=listbox, d=i: self.remove_plan(lb, d)).pack(side="left", padx=2)

            # 保存引用
            self.day_frames[i] = frame
            self.plan_entries[i] = listbox

        # 添加按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)

        ttk.Button(btn_frame, text="保存", command=self.save).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="取消", command=self.cancel).pack(side="right", padx=5)

    def load_data(self):
        """加载计划数据"""
        for day, listbox in self.plan_entries.items():
            plans = self.tmp_config["plan"].get(str(day), [])
            for plan in plans:
                listbox.insert(tk.END, plan)

    def add_plan(self, day):
        """添加新计划"""
        # 创建添加计划对话框
        dialog = AddPlanDialog(self.window)

        dialog.main()

        self.window.wait_window(dialog.window)

        if dialog.plan:
            self.plan_entries[day].insert(tk.END, dialog.plan)

            # 添加到配置
            if str(day) not in self.tmp_config["plan"]:
                self.tmp_config["plan"][str(day)] = []

            self.tmp_config["plan"][str(day)].append(dialog.plan)
            self.tmp_config["plan"][str(day)] = dedup_time_strings(self.tmp_config["plan"][str(day)])

    def remove_plan(self, listbox, day):
        """删除选中的计划"""
        selected = listbox.curselection()
        if not selected:
            return

        # 从列表框中移除
        plan = listbox.get(selected[0])
        listbox.delete(selected[0])

        # 从配置中移除
        if str(day) in self.tmp_config["plan"] and plan in self.tmp_config["plan"][str(day)]:
            self.tmp_config["plan"][str(day)].remove(plan)

    def save(self):
        """保存修改"""
        if self.config.read() != self.tmp_config:
            # 保存到配置文件
            self.config.update(self.tmp_config)
            self.config.save()

            # 重启调度器
            global scheduler, scheduler_thread
            lib.stop.stop_thread(scheduler_thread)  # 停止当前调度器
            # 创建新的调度器
            scheduler = Scheduler(self.config , self.logger)
            scheduler_thread = Thread(target=scheduler.run)
            scheduler_thread.daemon = True
            scheduler_thread.start()

            self.window.destroy()

        else:  # 未做出更改
            pass

        messagebox.showinfo("成功", "计划已保存并生效")

    def cancel(self):
        """取消编辑"""
        self.window.destroy()


class AddPlanDialog:
    """添加计划对话框"""

    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(self.parent)

        self.time_entry = None
        self.plan = None
        self.countdown_entry = None

    def main(self):
        self.parent.after(0, self._show_dialog)

    def _show_dialog(self):
        self.window.title("添加关机计划")
        self.window.geometry("300x200")
        self.window.resizable(False, False)

        # 创建表单
        self.create_form()

    def create_form(self):
        """创建表单"""
        form_frame = ttk.Frame(self.window, padding=15)
        form_frame.pack(fill="both", expand=True)

        # 时间输入
        ttk.Label(form_frame, text="24小时制时间 (HH:MM:SS):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.time_entry = ttk.Entry(form_frame, width=10)
        self.time_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.time_entry.insert(0, "22:00:00")

        # 倒计时输入
        ttk.Label(form_frame, text="倒计时 (秒):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.countdown_entry = ttk.Entry(form_frame, width=10)
        self.countdown_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        self.countdown_entry.insert(0, "60")

        # 添加按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)

        ttk.Button(button_frame, text="确定", command=self.confirm).pack(side="right", padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side="right", padx=5)

    def confirm(self):
        """确认添加计划"""
        try:
            time_str = self.time_entry.get()
            countdown = int(self.countdown_entry.get())

            # 验证时间格式
            parts = time_str.split(':')
            if len(parts) != 3:
                raise ValueError("时间格式不正确")

            hour, minute, second = map(int, parts)
            if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
                raise ValueError("时间值超出范围")

            # 创建计划字符串
            self.plan = f"{hour:02d}:{minute:02d}:{second:02d}:{countdown}"
            self.window.destroy()

        except ValueError as error:
            messagebox.showerror("输入错误", f"无效输入: {str(error)}")

    def cancel(self):
        """取消对话框"""
        self.window.destroy()
        self.plan = None


class SettingsDialog:
    """设置对话框"""

    def __init__(self, config:Config):
        self.config = config

        self.theme_var = None

    def main(self):
        root.after(0, self._show_dialog)

    def _show_dialog(self):
        self.window = tk.Toplevel()
        self.window.title("程序设置")
        self.window.geometry()
        self.window.resizable(False, False)

        # 创建界面
        self.create_ui()

    def create_ui(self):
        """创建用户界面"""
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.pack(fill="both", expand=True)

        # 主题设置
        ttk.Label(main_frame, text="主题设置:").pack(anchor="w", pady=5)

        self.theme_var = tk.StringVar(value=self.config.get("style", "Light"))
        theme_frame = ttk.Frame(main_frame)
        theme_frame.pack(fill="x", pady=5)

        ttk.Radiobutton(theme_frame, text="浅色模式", variable=self.theme_var,
                        value="Light").pack(side="left", padx=10)
        ttk.Radiobutton(theme_frame, text="深色模式", variable=self.theme_var,
                        value="Dark").pack(side="left", padx=10)
        ttk.Radiobutton(theme_frame, text="跟随系统", variable=self.theme_var,
                        value="Follow").pack(side="left", padx=10)

        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=15)

        ttk.Button(button_frame, text="保存", command=self.save).pack(side="right", padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side="right", padx=5)

    def save(self):
        """保存设置"""
        # 更新配置
        choose_style = self.theme_var.get()
        self.config.set("style", choose_style)

        # 更新图标
        global icon
        if choose_style == "Light":
            icon.icon = Image.open("lib/Light.ico")

        elif choose_style == "Dark":  # Dark
            icon.icon = Image.open("lib/Dark.ico")

        else:  # Follow
            c_dll = ctypes.cdll.LoadLibrary
            c_lib_file = c_dll('./lib/style.dll')  # 库文件

            if c_lib_file.IsDarkModeEnabled():
                icon.icon = Image.open("lib/Dark.ico")

            else:
                icon.icon = Image.open("lib/Light.ico")

        self.window.destroy()

        # 保存到文件
        if self.config.save():
            messagebox.showinfo("成功", "配置已保存并应用")

        else:
            messagebox.showwarning("注意", "保存出了些意外，但配置已成功应用")

    def cancel(self):
        """取消设置"""
        self.window.destroy()


def exit_program():
    """退出程序"""
    global icon
    global root

    if icon:
        icon.stop()

    root.destroy()
    exit()


def show_help():
    """显示帮助信息"""
    help_window = tk.Toplevel()
    help_window.title("帮助信息")
    help_window.geometry("400x200")

    content = """
    automatic-shutdown 使用说明

    1. 修改计划：修改后的计划永久有效
    2. 添加临时计划：只等待临时计划，只在本次运行有效且修改计划后失效
    3. 设置：更改程序主题等设置
    4. 退出程序：关闭本程序

    当关机倒计时开始时，您可以选择：
    - "现在关机"：立即关闭计算机
    - "跳过此计划"：取消当前关机计划

    初学者，有不好的地方还请理解
    """

    tk.Label(help_window, text=content, justify="left", padx=10, pady=10).pack()
    tk.Button(help_window, text="关闭", command=help_window.destroy).pack(pady=10)


def dedup_time_strings(time_list):
    seen = {}
    for s in time_list:
        key = s[:8]  # 提取前8个字符作为键（HH:MM:SS）
        if key not in seen:
            seen[key] = s
    # 按时间部分（前8个字符）排序
    return sorted(seen.values(), key=lambda x: x[:8])


# 全局变量
icon = None
scheduler = None
scheduler_thread = None
the_config = None

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()

    # 初始化日志功能
    the_logger = LogProcessing(Path("./config/log_file.log"))
    the_logger.info("主程序开始运行")

    # 加载配置
    the_config_file_path = Path("./config/config.json")
    default_configuration = {
        "style": "Light",
        "plan": {
            "1": ["22:00:00:60"],  # 周一
            "2": ["22:00:00:60"],  # 周二
            "3": ["22:00:00:60"],  # 周三
            "4": ["22:00:00:60"],  # 周四
            "5": ["22:00:00:60"],  # 周五
            "6": ["22:00:00:60"],  # 周六
            "7": ["22:00:00:60"]  # 周日
        }
    }  # 默认配置, 配置文件异常时使用

    try:
        with the_config_file_path.open("r", encoding='utf-8') as f:
            the_config = Config(the_config_file_path, json.load(f), the_logger)

    except json.JSONDecodeError as e:  # 文件格式错误
        the_logger.error(message="配置文件格式错误", exc_info=True)
        the_config = Config(the_config_file_path, default_configuration, the_logger)
        the_config.save() and the_logger.info("已创建默认配置文件")

    except FileNotFoundError:
        the_logger.warning(message="未找到配置文件")
        the_config_file_path.parent.mkdir(parents=True, exist_ok=True)
        the_config = Config(the_config_file_path, default_configuration, the_logger)
        the_config.save() and the_logger.info("已创建默认配置文件")


    # 创建系统托盘图标
    icon = pystray.Icon("automatic-shutdown")
    icon.title = "automatic-shutdown"

    # 设置图标
    try:
        style = the_config.get("style", None)
        if style == "Light":
            icon.icon = Image.open("lib/Light.ico")

        elif style == "Dark":  # Dark
            icon.icon = Image.open("lib/Dark.ico")

        else:
            dll = ctypes.cdll.LoadLibrary
            lib_file = dll('./lib/style.dll')  # 库文件
            if lib_file.IsDarkModeEnabled():
                icon.icon = Image.open("lib/Dark.ico")
            else:
                icon.icon = Image.open("lib/Light.ico")

    except FileNotFoundError as e:
        # 使用默认图标
        the_logger.error(message="未找到图标文件", exc_info=True)

    # 创建调度器
    scheduler = Scheduler(the_config, the_logger)

    # 创建线程
    scheduler_thread = Thread(target=scheduler.run)  # 调度器线程
    icon_th = Thread(target=icon.run)  # 拖盘图标线程

    scheduler_thread.daemon = True
    icon_th.daemon = True

    # 实例化
    temporary_plan_dialog = TemporaryPlanDialog(the_config, the_logger)  # 临时计划
    schedule_editor = ScheduleEditor(the_config, the_logger)  # 修改计划
    settings_dialog = SettingsDialog(the_config)  # 设置

    # 设置托盘菜单
    icon.menu = pystray.Menu(
        pystray.MenuItem("修改计划", schedule_editor.main),
        pystray.MenuItem("添加临时计划", temporary_plan_dialog.main),
        pystray.MenuItem("帮助", show_help),
        pystray.MenuItem("设置", settings_dialog.main),
        pystray.MenuItem("退出程序", exit_program)
    )

    # 启动线程
    scheduler_thread.start()  # 调度器线程
    icon_th.start()  # 运行系统托盘图标

    root.mainloop()