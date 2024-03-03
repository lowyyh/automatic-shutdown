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

    def log(self, strs):
        try:
            with open(r".\shut\log.txt", "a", encoding="utf-8") as f:
                f.write(strs)
        except:
            try:
                with open(r".\log.txt", "a", encoding="utf-8") as f:
                    f.write(strs)
            except:
                with open(r".\log.txt", "w", encoding="utf-8") as f:
                    f.write(strs)

    def clicked(self):
        messagebox.showinfo("shut", "已取消关机")
        self.root.destroy()
        self.log(dt.now().strftime('%Y-%m-%d %H:%M:%S') + ' 关机操作被取消\n\n')
        program_exit()

    def yes(self):
        self.root.destroy()
        self.log(dt.now().strftime('%Y-%m-%d %H:%M:%S') + ' 正常关机\n\n')
        system("shutdown -s -f -t 01")
        program_exit()

    def next_plan(self):
        global tg
        self.root.destroy()
        tg = True
        self.log(dt.now().strftime('%Y-%m-%d %H:%M:%S') + ' 跳过当前计划\n\n')
        return


class main:
    def __init__(self):
        pass

    def main(self):
        print("ok")
        now = dt.now()  # 获取当前时间
        self.log('-' * 20 + "\n")
        self.log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序开始运行\n')
        try:
            weekList = ["1", "2", "3", "4", "5", "6", "7"]
            week = weekList[dt.now().weekday()]
            times = open(r".\shut\%s.txt" % week, encoding='utf-8').readlines()
            if not times:
                self.log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:没有指定关机计划或计划为None\n\n')
                messagebox.showerror('shut', '没有指定关机计划或计划为None')  # 错误提示
                program_exit()
            elif times[0] == 'None':
                self.log(now.strftime('%Y-%m-%d %H::%S') + ' 主程序结束 原因:没有指定关机计划或计划为None\n\n')
                messagebox.showerror('shut', '没有指定关机计划或计划为None')  # 错误提示
                program_exit()
            for i in times:
                if int(i.split(':')[0]) >= int(now.strftime('%H')):
                    icon.title = i
                    self.log('    ' + now.strftime('%Y-%m-%d %H:%M:%S') + ' 等待%s中...: \n' % i)
                    self.main_if(i)
                else:
                    pass
            else:
                self.log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:没有可执行的操作\n\n')
            program_exit()
        except FileNotFoundError:
            self.log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:未找到文件\n\n')
            program_exit()

    def log(self, strs):
        try:
            with open(r".\shut\log.txt", "a", encoding="utf-8") as f:
                f.write(strs)
        except:
            try:
                with open(r".\log.txt", "a", encoding="utf-8") as f:
                    f.write(strs)
            except:
                with open(r".\log.txt", "w", encoding="utf-8") as f:
                    f.write(strs)

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
        while True:
            now = dt.now()  # 获取当前时间信息
            print("running")
            if int(i_in.split(':')[0]) == int(now.strftime('%H')):
                if int(i_in.split(':')[1]) == int(now.strftime('%M')):
                    if int(i_in.split(':')[2]) <= int(now.strftime('%S')):
                        self.log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 吉时已到 %s\n' % i_in)
                        temp = int(i_in.split(':')[3])
                        self.make_window(temp)
                        return
            sleep(0.6)


def program_exit():
    icon.stop()
    sys_exit()


if __name__ == '__main__':
    tg = False
    main_task = main()
    main_th = Thread(target=main_task.main)
    main_th.daemon = True
    icon = pystray.Icon("icon")
    icon.icon = Image.open("icon.ico")
    icon.title = "shutdown"
    icon.menu = pystray.Menu(pystray.MenuItem("退出", program_exit))
    main_th.start()
    icon.run()
