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
from json import dumps, loads
from lib.stop import stop_thread
from PIL import Image
from sys import exit as sys_exit
from time import sleep
from os import system
import tkinter as tk
from threading import Thread
from tkinter import messagebox
from datetime import datetime as dt


class App(tk.Frame):
    def __init__(self, timeout, window=None):
        super().__init__(window)
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
        print("ok")
        now = dt.now()  # 获取当前时间
        log('-' * 20 + "\n")
        log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序开始运行\n')
        try:
            times = self.config["plan"][["1", "2", "3", "4", "5", "6", "7"][dt.now().weekday()]]  # 获取当天的计划
            if (not times) or times[0] == 'None':
                log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:没有指定关机计划或计划为None\n\n')
                messagebox.showerror('automatic-shutdown', '没有指定关机计划或计划为None')  # 错误提示
                program_exit()

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
        global tg
        root = tk.Tk()
        root.title("注意!")
        root.geometry("610x180")
        root.wm_attributes("-topmost", True)
        try:
            app = App(tmp, root)
        except tk.TclError:
            if tg:
                tg = False
                return
            else:
                program_exit()

    def main_if(self, i_in):
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


class Add_play:  # 修改计划
    def __init__(self, modify, config, add_modify):
        self.lb = None
        self.add_play_window = None
        self._modify = modify
        self.config = config
        self.add_modify = add_modify

    def modify(self):
        self.config = self._modify(self.lb, self.add_play_window, )

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


class Modify:  # 修改计划-修改
    def __init__(self, config, add_modify):
        self.add_play_window_modify = None
        self.config = config
        self._add_modify = add_modify

    def complete_modify(self):
        pass

    def cancellation_modify(self):
        self.add_play_window_modify.destroy()

    def remove_modify(self):
        pass

    def add_modify(self):
        self._add_modify.main(self.add_play_window_modify)

    def main(self, lb, add_play_window):
        choose = lb.curselection()
        if choose:
            self.add_play_window_modify = tk.Toplevel(add_play_window)
            var_modify = tk.StringVar()
            plan_time_list = self.config["plan"][str(choose[0] + 1)]
            var_modify.set(plan_time_list)
            lb_modify = tk.Listbox(self.add_play_window_modify, listvariable=var_modify)
            fr_add_play_modify = tk.Frame(self.add_play_window_modify, relief=tk.RAISED, bd=0)
            bt_add_modify = tk.Button(fr_add_play_modify, text="添加", command=self.add_modify)
            bt_remove_modify = tk.Button(fr_add_play_modify, text="删除", command=self.remove_modify)
            bt_complete_modify = tk.Button(fr_add_play_modify, text="完成", command=self.complete_modify)
            bt_cancellation_modify = tk.Button(fr_add_play_modify, text="取消", command=self.cancellation_modify)
            bt_add_modify.grid(row=0, column=0)
            bt_complete_modify.grid(row=0, column=1)
            bt_remove_modify.grid(row=0, column=2)
            bt_cancellation_modify.grid(row=0, column=3)
            lb_modify.pack()
            fr_add_play_modify.pack()
            self.add_play_window_modify.mainloop()
        else:
            tk.messagebox.showerror(title="automatic-shutdown", message="请选择要修改的日期!")


class Add_modify:  # 添加计划-修改-添加
    def __init__(self):
        self.add_modify_window = None

    def add_modify_window_determine(self):
        plan_time = self.entry_time.get() + ":" + self.entry_wait.get()
        try:
            plan_time_list = [int(i) for i in plan_time.split(":")]
            if len(plan_time_list) == 4 and 0 <= plan_time_list[0] <= 24 and 0 <= plan_time_list[1] <= 60 and 0 <= \
                    plan_time_list[2] <= 60:
                time_format = "%H:%M:%S"
                time_str_obj = dt.strptime(plan_time, time_format).time()

                # 将时间字符串转换为datetime.time对象，并检查是否有与time_str相同的时间
                sorted_time_objs = []
                same_time_found = False
                for time_str in plan_time_list:
                    time_obj = dt.strptime(time_str, time_format).time()
                    if time_obj == time_str_obj:
                        same_time_found = True
                    sorted_time_objs.append(time_obj)

                # 将time_str插入到排序后的时间对象列表中
                sorted_time_objs.append(time_str_obj)
                sorted_time_objs.sort()

                # 将排序后的时间对象列表转换回时间字符串列表
                sorted_time_strs = [time_obj.strftime(time_format) for time_obj in sorted_time_objs]

                # 如果找到与time_str相同的时间，则给出提示
                if same_time_found:
                    # print(f"The time '{plan_time}' is already present in the list.")
                    return

                # return sorted_time_strs
                self.add_modify_window.destroy()
            else:
                tk.messagebox.showerror(title="automatic-shutdown", message="格式错误!")
        except ValueError:
            tk.messagebox.showerror(title="automatic-shutdown", message="请输入数字!")

    def add_modify_window_cancellation(self):
        pass

    def main(self, add_play_window_modify):
        self.add_modify_window = tk.Tk(add_play_window_modify)
        label_time = tk.Label(text="请输入时间, 如:'12:00:00'")
        self.entry_time = tk.Entry(self.add_modify_window)
        label_wait = tk.Label(text="请输入倒计时时间(秒), 如:'20'")
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


def program_exit():
    icon.stop()
    sys_exit()


def setting():
    pass


def help_():
    help_window = tk.Tk()
    a = tk.Label(help_window, text='修改计划：修改后的计划永久有效')
    b = tk.Label(help_window, text='添加临时计划：只等待临时计划，只在本次运行有效')
    a.pack()
    b.pack()
    help_window.mainloop()


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


if __name__ == '__main__':
    with open(r'./config/config.json', "r", encoding='utf-8') as f:
        data_str = f.read()
        config = loads(data_str)

    tg = False
    add_modify = Add_modify()
    add_temp_play = Add_temp_play()
    modify = Modify(config, add_modify)
    add_play = Add_play(modify.main, config, add_modify)
    main_task = main(config)
    main_th = Thread(target=main_task.main)
    main_th.daemon = True
    icon = pystray.Icon("icon")
    if config["style"] == "Light":
        icon.icon = Image.open("./lib/icon2.ico")
    else:  # Dark
        icon.icon = Image.open("./lib/icon.ico")
    icon.title = "automatic-shutdown"
    icon.menu = pystray.Menu(pystray.MenuItem("修改计划", add_play.main),
                             pystray.MenuItem("添加临时计划", add_temp_play.main),
                             pystray.MenuItem("帮助", help_),
                             pystray.MenuItem("设置", setting),
                             pystray.MenuItem("退出程序", program_exit)
                             )
    main_th.start()
    icon.run()
