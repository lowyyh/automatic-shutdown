"""
Copyright (c) 2024 lowyyh
automatic-shutdown is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:
         http://license.coscl.org.cn/MulanPSL2
THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
See the Mulan PSL v2 for more details.
"""
import pystray
import ctypes
from json import dumps, loads
from lib.stop import stop_thread
from PIL import Image
from sys import exit as sys_exit
from time import sleep
from os import system
import tkinter as tk
from threading import Thread
from multiprocessing import Queue
from tkinter import messagebox
from datetime import datetime as dt


class App(tk.Frame):
    def __init__(self, timeout, window=None):
        super().__init__()
        self.t = timeout
        self.root = window
        self.la = tk.Label(self.root, text=f"电脑将在{self.t}秒后关机!")  # 显示的文本
        btn = tk.Button(self.root, text="取消关机", command=self.clicked, width=10,
                        height=2)  # 按钮 text为按钮名称, command为操作
        btn2 = tk.Button(self.root, text="现在关机", command=self.yes, width=10, height=2)
        btn3 = tk.Button(self.root, text="跳过此计划", command=self.next_plan, width=10, height=2)
        self.la["font"] = ("", 40)
        self.la.grid(row=0, column=0, columnspan=3, sticky="ew")
        btn.grid(row=1, column=0, sticky="ew")
        btn2.grid(row=1, column=1, sticky="ew")
        btn3.grid(row=1, column=2, sticky="ew")
        self.count_down()

    def count_down(self):
        while self.t > 0:
            # print("in while")
            self.t -= 1
            sleep(1)
            self.la.config(text=f"电脑将在{self.t}秒后关机!")
            try:
                self.root.update()
            except:
                self.root.mainloop()
        else:
            self.yes()

    def clicked(self):
        messagebox.showinfo("automatic-shutdown", "已取消关机")
        self.root.destroy()
        log(dt.now().strftime('%Y-%m-%d %H:%M:%S') + ' 关机操作被取消\n\n')
        program_exit()

    def yes(self):
        self.root.destroy()
        log(dt.now().strftime('%Y-%m-%d %H:%M:%S') + ' 正常关机\n\n')
        system("shutdown -s -f -t 01")
        program_exit()

    def next_plan(self):
        global tg
        self.root.destroy()
        tg = True
        log(dt.now().strftime('%Y-%m-%d %H:%M:%S') + ' 跳过当前计划\n\n')
        return


class main:
    def __init__(self, config):
        self.config = config

    def main(self):
        now = dt.now()  # 获取当前时间
        log('-' * 20 + "\n")
        log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序开始运行\n')
        try:
            times = self.config["plan"][["1", "2", "3", "4", "5", "6", "7"][dt.now().weekday()]]  # 获取当天的计划
            if (not times) or times[0] == 'None':
                log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:没有指定关机计划或计划为None\n\n')
                messagebox.showerror('automatic-shutdown', '没有指定关机计划或计划为None')  # 错误提示
                return

            for i in times:
                plan_h = int(i.split(':')[0])
                now_h = int(now.strftime('%H'))
                if (plan_h > now_h) or ((plan_h == now_h) and int(i.split(':')[1]) > int(now.strftime('%M'))):
                    log('    ' + now.strftime('%Y-%m-%d %H:%M:%S') + ' 等待%s中...: \n' % i)
                    self.main_if(i)
                else:
                    pass
            else:
                log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:没有可执行的操作\n\n')
            program_exit()
        except FileNotFoundError:
            log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:未找到文件\n\n')
            program_exit()

    def make_window(self, tmp):
        root = tk.Tk()
        root.title("注意!")
        root.geometry("610x180")
        root.wm_attributes("-topmost", True)
        try:
            app = App(tmp, root)
        except tk.TclError:
            global tg
            if tg:
                tg = False
                return
            else:
                program_exit()

    def main_if(self, i_in):
        global icon
        icon.title = i_in
        while True:
            now = dt.now()  # 获取当前时间信息
            # print("running")
            if int(i_in.split(':')[0]) == int(now.strftime('%H')):
                if int(i_in.split(':')[1]) == int(now.strftime('%M')):
                    if int(i_in.split(':')[2]) <= int(now.strftime('%S')):
                        log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 吉时已到 %s\n' % i_in)
                        temp = int(i_in.split(':')[3])
                        self.make_window(temp)
                        return
            sleep(0.6)


class Add_temp_play:  # 添加临时计划
    def __init__(self):
        self.entry_wait = None
        self.add_temp_play_window = None
        self.entry_time = None

    def determine(self):
        plan_time = self.entry_time.get() + ":" + self.entry_wait.get()
        try:
            plan_time_list = [int(i) for i in plan_time.split(":")]
            if len(plan_time_list) == 4 and 0 <= plan_time_list[0] <= 24 and 0 <= plan_time_list[1] <= 60 and 0 <= \
                    plan_time_list[2] <= 60:
                now = dt.now()
                spring = dt(now.year, now.month, now.day, plan_time_list[0], plan_time_list[1], plan_time_list[2])
                second = (spring - now).days
                if second < 0:
                    tk.messagebox.showwarning(title="automatic-shutdown", message="当前时间大于计划时间")

                global main_th
                stop_thread(main_th)  # 停止旧线程，开启新的线程
                main_th = Thread(target=main_task.main_if, args=(plan_time,))
                main_th.daemon = True
                main_th.start()
                self.add_temp_play_window.destroy()
                log(now.strftime('%Y-%m-%d %H:%M:%S') + f' 添加临时计划 {plan_time}\n')
            else:
                tk.messagebox.showerror(title="automatic-shutdown", message="格式错误!")
        except ValueError:
            tk.messagebox.showerror(title="automatic-shutdown", message="请输入数字!")

    def cancellation(self):
        self.add_temp_play_window.destroy()
        return

    def main(self):
        self.add_temp_play_window = tk.Tk()
        label_time = tk.Label(text="请输入时间, 如:'12:00:00'")
        self.entry_time = tk.Entry(self.add_temp_play_window)
        label_wait = tk.Label(text="请输入倒计时时间(秒), 如:'20'")
        self.entry_wait = tk.Entry(self.add_temp_play_window)
        fr_bt = tk.Frame(self.add_temp_play_window, relief=tk.RAISED, bd=0)
        bt1 = tk.Button(fr_bt, text="确定", command=self.determine)
        bt2 = tk.Button(fr_bt, text="取消", command=self.cancellation)
        bt1.grid(row=0, column=0)
        bt2.grid(row=0, column=1)
        label_time.pack()
        self.entry_time.pack()
        label_wait.pack()
        self.entry_wait.pack()
        fr_bt.pack()
        self.add_temp_play_window.mainloop()


class Add_modify:  # 添加计划-修改-添加
    def __init__(self, add_play_window_modify, plan_list, queue):
        self.plan_list = None
        self.entry_wait = None
        self.entry_time = None
        self.add_modify_window = None
        self.Queue = queue
        self.window = add_play_window_modify
        self.plan_list = plan_list

    def list(self, plan_time_list, time_str):
        time_format = "%H:%M:%S"
        time_str_obj = dt.strptime(time_str, time_format).time()

        # 将时间字符串转换为datetime.time对象，并检查是否有与time_str相同的时间
        sorted_time_objs = []
        for time_str in plan_time_list:
            time_obj = dt.strptime(time_str, time_format).time()
            sorted_time_objs.append(time_obj)

        # 将time_str插入到排序后的时间对象列表中
        sorted_time_objs.append(time_str_obj)
        sorted_time_objs.sort()

        # 将排序后的时间对象列表转换回时间字符串列表
        sorted_time_strs = [time_obj.strftime(time_format) for time_obj in sorted_time_objs]

        return sorted_time_strs

    def add_modify_window_determine(self):
        plan_time_list = [self.entry_time.get(), self.entry_wait.get()]
        try:
            plan_time_list_cheek = [int(i) for i in plan_time_list[0].split(":")]
            plan_time_list_cheek.append(plan_time_list[1])
            if len(plan_time_list_cheek) == 4 and 0 <= plan_time_list_cheek[0] <= 24 and 0 <= plan_time_list_cheek[
                1] <= 60 and 0 <= \
                    plan_time_list_cheek[2] <= 60:
                dict_key = [':'.join([i for i in i2.split(":")[:-1]]) for i2 in self.plan_list]
                dict_value = [i2.split(":")[-1] for i2 in self.plan_list]
                plan_dict = dict(zip(dict_key, dict_value))
                plan_dict[plan_time_list[0]] = plan_time_list[1]
                self.Queue.put([i + ':' + plan_dict[i] for i in self.list(dict_key, plan_time_list[0])])
                self.add_modify_window.quit()
                self.add_modify_window.destroy()
            else:
                tk.messagebox.showerror(title="automatic-shutdown", message="格式错误!")
        except KeyboardInterrupt:
            tk.messagebox.showerror(title="automatic-shutdown", message="请输入数字!")

    def add_modify_window_cancellation(self):
        self.Queue.put(None)
        self.add_modify_window.quit()
        self.add_modify_window.destroy()

    def main(self):
        self.add_modify_window = tk.Toplevel(self.window)
        # self.add_modify_window = tk.Tk()
        label_time = tk.Label(self.add_modify_window, text="请输入时间, 如:'12:00:00'")
        self.entry_time = tk.Entry(self.add_modify_window)
        label_wait = tk.Label(self.add_modify_window, text="请输入倒计时时间(秒), 如:'20'")
        self.entry_wait = tk.Entry(self.add_modify_window)
        fr_bt = tk.Frame(self.add_modify_window, relief=tk.RAISED, bd=0)
        bt1 = tk.Button(fr_bt, text="确定", command=self.add_modify_window_determine)
        bt2 = tk.Button(fr_bt, text="取消", command=self.add_modify_window_cancellation)
        bt1.grid(row=0, column=0)
        bt2.grid(row=0, column=1)
        label_time.pack()
        self.entry_time.pack()
        label_wait.pack()
        self.entry_wait.pack()
        fr_bt.pack()
        self.add_modify_window.mainloop()
        pass


class Modify:  # 修改计划-修改
    def __init__(self, config, add_play_window, lb):
        self.choose = None
        self.Queue = Queue()
        self.lb_modify = None
        self.var_modify = None
        self.plan_time_list = None
        self.add_play_window_modify = None
        self.config = config
        self.window = add_play_window
        self.lb = lb

    def the_list(self, plan_time_list):
        time_format = "%H:%M:%S"

        sorted_time_objs = []
        for time_str in plan_time_list:
            time_obj = dt.strptime(time_str, time_format).time()
            sorted_time_objs.append(time_obj)

        sorted_time_objs.sort()

        # 将排序后的时间对象列表转换回时间字符串列表
        sorted_time_strs = [time_obj.strftime(time_format) for time_obj in sorted_time_objs]

        return sorted_time_strs

    def complete_modify(self):
        self.add_play_window_modify.quit()

    def cancellation_modify(self):
        self.config = None
        self.add_play_window_modify.quit()

    def remove_modify(self):
        rm_key = self.lb_modify.curselection()
        del self.config["plan"][str(self.choose[0] + 1)][rm_key[0]]
        self.lb_modify.delete(rm_key[0])

    def add_modify(self):
        bl = Add_modify(self.add_play_window_modify, self.plan_time_list, self.Queue)
        bl.main()
        self.plan_time_list = self.Queue.get()
        if self.plan_time_list is not None:
            self.config["plan"][str(self.choose[0] + 1)] = self.plan_time_list
            self.var_modify.set(self.plan_time_list)

    def main(self):
        self.choose = self.lb.curselection()
        if self.choose:
            self.add_play_window_modify = tk.Toplevel(self.window)
            self.var_modify = tk.StringVar()
            self.plan_time_list = self.config["plan"][str(self.choose[0] + 1)]
            self.var_modify.set(self.plan_time_list)
            self.lb_modify = tk.Listbox(self.add_play_window_modify, listvariable=self.var_modify)
            fr_add_play_modify = tk.Frame(self.add_play_window_modify, relief=tk.RAISED, bd=0)
            bt_add_modify = tk.Button(fr_add_play_modify, text="添加", command=self.add_modify)
            bt_remove_modify = tk.Button(fr_add_play_modify, text="删除", command=self.remove_modify)
            bt_complete_modify = tk.Button(fr_add_play_modify, text="完成", command=self.complete_modify)
            bt_cancellation_modify = tk.Button(fr_add_play_modify, text="取消", command=self.cancellation_modify)
            bt_add_modify.grid(row=0, column=0)
            bt_complete_modify.grid(row=0, column=1)
            bt_remove_modify.grid(row=0, column=2)
            bt_cancellation_modify.grid(row=0, column=3)
            self.lb_modify.pack()
            fr_add_play_modify.pack()
            self.add_play_window_modify.mainloop()
            self.add_play_window_modify.destroy()
            return self.config
        else:
            tk.messagebox.showerror(title="automatic-shutdown", message="请选择要修改的日期!")


class Add_play:  # 修改计划
    def __init__(self, config):
        self.lb = None
        self.add_play_window = None
        self.config = config

    def modify(self):
        tmp_config = Modify(self.config, self.add_play_window, self.lb).main()
        if tmp_config is not None:
            self.config = tmp_config

    def main(self):
        self.add_play_window = tk.Tk()
        var = tk.StringVar()
        var.set(["周一", "周二", "周三", "周四", "周五", "周六", "周日"])
        self.lb = tk.Listbox(self.add_play_window, listvariable=var)
        fr_add_play = tk.Frame(self.add_play_window, relief=tk.RAISED, bd=0)
        bt_modify = tk.Button(fr_add_play, text="修改", command=self.modify)
        bt_complete = tk.Button(fr_add_play, text="完成", command=self.complete)
        bt_cancellation = tk.Button(fr_add_play, text="取消", command=self.cancellation)
        bt_modify.grid(row=0, column=0)
        bt_complete.grid(row=0, column=1)
        bt_cancellation.grid(row=0, column=2)
        self.lb.pack()
        fr_add_play.pack()
        self.add_play_window.mainloop()

    def cancellation(self):
        self.add_play_window.quit()
        self.add_play_window.destroy()

    def complete(self):
        json_data = dumps(self.config, indent=2, ensure_ascii=False)
        with open(r'./config/config.json', 'w', encoding='utf-8') as f:
            f.write(json_data)

        global main_task
        global main_th
        main_task = main(config)
        main_th = Thread(target=main_task.main)
        main_th.daemon = True
        main_th.start()
        self.add_play_window.quit()
        self.add_play_window.destroy()


def log(strs):
    try:
        with open(r".\config\log.txt", "a", encoding="utf-8") as f:
            f.write(strs)
    except:
        try:
            with open(r".\log.txt", "a", encoding="utf-8") as f:
                f.write(strs)
        except:
            with open(r".\log.txt", "w", encoding="utf-8") as f:
                f.write(strs)


def program_exit():
    icon.stop()
    sys_exit()


class Setting:
    def __init__(self, config):
        self.setting_tk = None
        self.config = config

    def style(self):
        setting_style_window = tk.Toplevel(self.setting_tk)
        variable_value = tk.StringVar()
        variable_value_dist = {
            "0": "Dark",
            "1": "Light",
            "2": "follow_system"
        }
        tk.Radiobutton(setting_style_window, text='黑夜', variable=variable_value, value=0).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(setting_style_window, text='白天', variable=variable_value, value=1).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(setting_style_window, text='跟随系统(win10)', variable=variable_value, value=2).pack(side=tk.LEFT, padx=5)

        def ensure():
            key = variable_value.get()
            if not key:
                return
            elif key == "2":
                dll = ctypes.cdll.LoadLibrary
                lib = dll('./style.dll')  # 库文件
                if lib.IsDarkModeEnabled():
                    config["style"] = "Dark"
                    icon.icon = Image.open("./lib/icon.ico")
                else :
                    config["style"] = "Light"
                    icon.icon = Image.open("./lib/icon2.ico")
            elif key:
                self.config["style"] = variable_value_dist[key]
                if config["style"] == "Light":
                    icon.icon = Image.open("./lib/icon2.ico")
                else:  # Dark
                    icon.icon = Image.open("./lib/icon.ico")

            json_data = dumps(self.config, indent=2, ensure_ascii=False)
            with open(r'./config/config.json', 'w', encoding='utf-8') as f:
                f.write(json_data)

            setting_style_window.quit()
            setting_style_window.destroy()

        tk.Button(setting_style_window, text="确定", command=ensure).pack(side=tk.LEFT, padx=5)
        setting_style_window.mainloop()

    def main(self):
        self.setting_tk = tk.Tk()
        tk.Button(self.setting_tk, text="主题", command=self.style).pack()
        self.setting_tk.mainloop()


def help_():
    help_window = tk.Tk()
    a = tk.Label(help_window, text='修改计划：修改后的计划永久有效')
    b = tk.Label(help_window, text='添加临时计划：只等待临时计划，只在本次运行有效')
    a.pack()
    b.pack()
    help_window.mainloop()


if __name__ == '__main__':
    with open(r'./config/config.json', "r", encoding='utf-8') as f:
        data_str = f.read()
        config = loads(data_str)

    tg = False
    add_tmp_plan = Add_temp_play()
    add_play = Add_play(config)
    main_task = main(config)
    setting = Setting(config)
    main_th = Thread(target=main_task.main)
    main_th.daemon = True
    icon = pystray.Icon("icon")
    if config["style"] == "Light":
        icon.icon = Image.open("./lib/icon2.ico")
    else:  # Dark
        icon.icon = Image.open("./lib/icon.ico")
    icon.title = "automatic-shutdown"
    icon.menu = pystray.Menu(
        pystray.MenuItem("修改计划", add_play.main),
        pystray.MenuItem("添加临时计划", add_tmp_plan.main),
        pystray.MenuItem("帮助", help_),
        pystray.MenuItem("设置", setting.main),
        pystray.MenuItem("退出程序", program_exit)
    )
    main_th.start()
    icon.run()
