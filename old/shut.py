# Copyright (c) 2025 lowyyh
# SPDX-License-Identifier: MIT

import datetime as dt
from os import system
from sys import exit
import time
from tkinter import Tk, Label


class TimeShow():  # 实现倒计时

    def __init__(self, time_show=5):
        self.timeShowWin = Tk()
        self.timeShowWin.overrideredirect(True)
        self.timeShowWin.attributes('-alpha', 1)
        self.timeShowWin.attributes('-topmost', True)
        self.timeShowWin.attributes('-transparentcolor', 'black')
        self.time_show = time_show
        self.time_label = Label(self.timeShowWin, text='倒计时{}秒后关机'.format(self.time_show), font=('楷体', 25), fg='red',
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


now = dt.datetime.now()#获取当前时间信息
times = open(r".\shut.txt").readlines()
for i in times:
    now = dt.datetime.now()  # 获取当前时间信息
    if int(i.split(':')[0]) >= int(now.strftime('%H')):
        if int(i.split(':')[1]) >= int(now.strftime('%M')):
            while True:
                now = dt.datetime.now()  # 获取当前时间信息
                if int(i.split(':')[0]) == int(now.strftime('%H')):
                    if int(i.split(':')[1]) == int(now.strftime('%M')):
                        if int(i.split(':')[2]) <= int(now.strftime('%S')):
                            temp = int(i.split(':')[-1])
                            system("shutdown -s -f -t %d" % temp)
                            a = TimeShow(temp)
                            a.start()
                            exit()
