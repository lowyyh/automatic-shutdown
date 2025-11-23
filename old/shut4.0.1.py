# Copyright (c) 2025 lowyyh
# SPDX-License-Identifier: MIT

import multiprocessing

import sys
import time
import tkinter.messagebox
from os import system
from tkinter import *
from threading import Thread
from tkinter import messagebox
from datetime import datetime as dt
from multiprocessing import Process


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


def temp_in_plan(file, plan):
    with open(file, encoding="utf-8") as f1:
        data = f1.read().split()
    with open(file, "w", encoding="utf-8") as f2:
        writes = []
        for i in data:
            if i == plan:
                pass
            else:
                writes.append(i)
        f2.write("\n".join(writes))


def main(timeout):
    window = Tk()
    window.title("将要关机!")
    window.geometry("610x180")

    def clicked():
        system('shutdown -a')
        messagebox.showinfo("shut", "已取消关机")
        window.destroy()

    lbl = Label(window, text="电脑将在%sS后关机!" % timeout)  # 显示的文本
    btn = Button(window, text="取消", command=clicked, width=10, height=2)  # 按钮 text为按钮名称, command为操作
    lbl["font"] = ("", 40)
    btn.pack(side='bottom')
    lbl.pack()
    window.mainloop()


class TimeShow():  # 实现倒计时

    def __init__(self, time_show=5):
        self.timeShowWin = Tk()
        self.timeShowWin.overrideredirect(True)
        self.timeShowWin.attributes('-alpha', 1)
        self.timeShowWin.attributes('-topmost', True)
        self.timeShowWin.attributes('-transparentcolor', 'black')
        self.time_show = time_show
        self.time_label = Label(self.timeShowWin, text='倒计时{}秒后关机'.format(self.time_show),
                                font=('楷体', 25), fg='red',
                                bg='black')
        self.time_label.pack(fill='x', anchor='center')
        self.timeShowWin.geometry('+' + str(int(self.timeShowWin.winfo_screenwidth() / 2)) + '+' + str(125))
        self.timeShowWin.after(1, self.show)

    def show(self):
        while self.time_show >= 0:
            # print('time_label={}'.format(self.time_label))
            self.time_label['text'] = '{}秒后关机'.format(self.time_show)
            self.timeShowWin.update()
            self.time_show -= 1
            time.sleep(1)
        self.timeShowWin.destroy()

    def start(self):
        self.timeShowWin.mainloop()


def count_down(temp):  # 由于创建线程时执行函数,所以创建次函数
    a = TimeShow(temp)
    a.start()


def main1(i):
    while True:
        now = dt.now()  # 获取当前时间信息
        if int(i.split(':')[0]) == int(now.strftime('%H')):
            if int(i.split(':')[1]) == int(now.strftime('%M')):
                # if int(i.split(':')[0]) == int(nows.strftime('%M')):
                #     return
                if int(i.split(':')[2]) == int(now.strftime('%S')):
                    log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 程序结束,了吧 原因:操作执行完毕,操作:%s\n\n' % i)
                    temp = int(i.split(':')[3])
                    system("shutdown -s -f -t %d" % temp)
                    t = Thread(target=count_down, args=(temp,))
                    t.setDaemon(True)
                    t.start()
                    main(temp)
                    log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 关机操作被取消\n\n')
                    return


def main2(i):
    while True:
        now = dt.now()  # 获取当前时间信息
        if int(i.split(':')[1]) == int(now.strftime('%M')):
            if int(i.split(':')[2]) == int(now.strftime('%S')):
                log(now.strftime(
                    '%Y-%m-%d %H:%M:%S') + ' 程序结束,了吧 原因:操作执行完毕,操作:%s\n\n' % i)
                temp = int(i.split(':')[3])
                system("shutdown -s -f -t %d" % temp)
                t = Thread(target=count_down, args=(temp,))
                t.setDaemon(True)
                t.start()
                main(temp)
                log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 关机操作被取消\n\n')
                return


if __name__ == '__main__':
    multiprocessing.freeze_support()  # 最初的4.0版本没有这一行，导致编译后出现无限进程bug
    now = dt.now()  # 获取当前时间
    log('-' * 20 + "\n")
    log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序开始运行\n')
    try:
        weekList = ["1", "2", "3", "4", "5", "6", "7"]
        week = weekList[dt.now().weekday()]
        times = open(r".\shut\%s.txt" % week, encoding='utf-8').readlines()
        if times[0] == 'None':
            log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:计划为None\n\n')
            tkinter.messagebox.showerror('shut', '计划为None')  # 错误提示
            sys.exit()
        for i in times:
            log('    ' + now.strftime('%Y-%m-%d %H:%M:%S') + ' 开始判断%s: ' % i)
            if int(i.split(':')[0]) >= int(now.strftime('%H')):
                if int(i.split(':')[0]) >= int(now.strftime('%H')):
                    print(i)
                    if "temp" in i:
                        temp_in_plan(".\shut\%s.txt" % week, i)
                    else:
                        log('    ' + now.strftime('%Y-%m-%d %H:%M:%S') + ' 开始创建进程main1\n')
                        p_main = Process(target=main1, args=(i,))
                        # p_main.setDaemon(True)
                        p_main.start()
                        log('    ' + now.strftime('%Y-%m-%d %H:%M:%S') + ' 进程main1开始\n')
                        p_main.join()
                        log('    ' + now.strftime('%Y-%m-%d %H:%M:%S') + ' 进程main1结束\n')
                elif int(i.split(':')[0]) == int(now.strftime('%H')):
                    log(' 目标小时 = 当前小时(%s = %s)' % (i.split(':')[0], now.strftime('%H')))
                    if int(i.split(':')[1]) >= int(now.strftime('%M')):
                        print(i)
                        if "temp" in i:
                            temp_in_plan(".\shut\%s.txt" % week, i)
                        else:
                            log('    ' + now.strftime('%Y-%m-%d %H:%M:%S') + ' 开始创建进程, 执行main2\n')
                            p_main = Process(target=main2, args=(i,))
                            p_main.start()
                            log('    ' + now.strftime('%Y-%m-%d %H:%M:%S') + ' 进程main2开始\n')
                            p_main.join()
                            log('    ' + now.strftime('%Y-%m-%d %H:%M:%S') + ' 进程main2结束\n')
                    else:
                        pass
                else:
                    pass
        log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:没有可执行的操作\n\n')
        sys.exit()
    except FileNotFoundError:
        log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 主程序结束 原因:未找到文件\n\n')
        sys.exit()
