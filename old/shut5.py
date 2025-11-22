import _tkinter
import sys
import time
from os import system
import tkinter as tk
from tkinter import messagebox
from datetime import datetime as dt


def log(strs):
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


class App(tk.Frame):
    def __init__(self, timeout, window=None):
        super().__init__(window)
        self.t = timeout
        self.root = window
        self.la = tk.Label(self.root, text=f"电脑将在{self.t}秒后关机!")  # 显示的文本
        btn = tk.Button(self.root, text="取消关机", command=self.clicked, width=10, height=2)  # 按钮 text为按钮名称, command为操作
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
            time.sleep(1)
            self.la.config(text=f"电脑将在{self.t}秒后关机!")
            try:
                self.root.update()
            except:
                self.root.mainloop()
        else:
            self.yes()

    def clicked(self):
        messagebox.showinfo("shut", "已取消关机")
        self.root.destroy()
        log(dt.now().strftime('%Y-%m-%d %H:%M:%S') + ' 关机操作被取消\n\n')
        sys.exit()

    def yes(self):
        self.root.destroy()
        log(dt.now().strftime('%Y-%m-%d %H:%M:%S') + ' 正常关机\n\n')
        system("shutdown -s -f -t 01")
        sys.exit()

    def next_plan(self):
        global tg
        self.root.destroy()
        tg = True
        log(dt.now().strftime('%Y-%m-%d %H:%M:%S') + ' 跳过当前计划\n\n')
        return


def make_window(tmp):
    global tg
    root = tk.Tk()
    root.title("注意!")
    root.geometry("610x180")
    root.wm_attributes("-topmost", True)
    try :
        app = App(tmp, root)
    except _tkinter.TclError:
        if tg:
            tg = False
            return
        else:
            sys.exit()


def main(i_in):
    while True:
        now = dt.now()  # 获取当前时间信息
        if int(i_in.split(':')[0]) == int(now.strftime('%H')):
            if int(i_in.split(':')[1]) == int(now.strftime('%M')):
                if int(i_in.split(':')[2]) <= int(now.strftime('%S')):
                    log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 吉时已到 %s\n' % i_in)
                    temp = int(i_in.split(':')[3])
                    make_window(temp)
                    return


if __name__ == '__main__':
    tg = False
    now = dt.now()  # 获取当前时间
    log('-' * 20 + "\n")
    log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序开始运行\n')
    try:
        weekList = ["1", "2", "3", "4", "5", "6", "7"]
        week = weekList[dt.now().weekday()]
        times = open(r".\shut\%s.txt" % week, encoding='utf-8').readlines()
        if not times:
            log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:没有指定关机计划或计划为None\n\n')
            messagebox.showerror('shut', '没有指定关机计划或计划为None')  # 错误提示
            sys.exit()
        elif times[0] == 'None':
            log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:没有指定关机计划或计划为None\n\n')
            messagebox.showerror('shut', '没有指定关机计划或计划为None')  # 错误提示
            sys.exit()
        for i in times:
            if int(i.split(':')[0]) >= int(now.strftime('%H')):
                # print(i)
                log('    ' + now.strftime('%Y-%m-%d %H:%M:%S') + ' 等待%s中...: \n' % i)
                main(i)
            else:
                pass
        else:
            log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:没有可执行的操作\n\n')
        sys.exit()
    except FileNotFoundError:
        log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:未找到文件\n\n')
        sys.exit()
    # except :
    #     log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:发生未知错误\n\n')
