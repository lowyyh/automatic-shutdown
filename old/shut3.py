import sys
import time
from os import system
from tkinter import *
from threading import Thread
from tkinter import messagebox
from datetime import datetime as dt


def log(strs):
    try :
        with open(r".\shut\log.txt", "a", encoding="utf-8") as f:
            f.write(strs)
    except :
        try :
            with open(r".\log.txt", "w", encoding="utf-8") as f:
                f.write(strs)
        except:
            with open(r".\log.txt", "w", encoding="utf-8") as f:
                f.write(strs)


def main(timeout):
    window = Tk()
    window.title("将要关机!")
    window.geometry("610x180")

    def clicked():
        system('shutdown -a')
        messagebox.showinfo("shut", "已取消关机")
        window.destroy()

    lbl = Label(window, text="您的电脑将在%sS后关机!" % timeout)  # 显示的文本
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


def count_down(temp):
    a = TimeShow(temp)
    a.start()


if __name__ == '__main__':
    log('-' * 20 + "\n")
    now = dt.now()  # 获取当前时间
    log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 程序开始运行\n')
    try:
        weekList = ["1", "2", "3", "4", "5", "6", "7"]
        week = weekList[dt.now().weekday()]
        times = open(r".\shut\%s.txt" % week, encoding='utf-8').readlines()
        if times[0] == 'None':
            log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 程序结束 原因:计划为None\n\n')
            sys.exit()
        for i in times:
            log('    ' + now.strftime('%Y-%m-%d %H:%M:%S') + ' 开始判断%s: ' % i)
            if int(i.split(':')[0]) >= int(now.strftime('%H')):
                if int(i.split(':')[0]) > int(now.strftime('%H')):
                    log('  目标小时 > 当前小时(%s >= %s), 开始判断\n' % (i.split(':')[0], now.strftime('%H')))
                    while True:
                        now = dt.now()  # 获取当前时间信息
                        if int(i.split(':')[0]) == int(now.strftime('%H')):
                            if int(i.split(':')[1]) == int(now.strftime('%M')):
                                if int(i.split(':')[2]) <= int(now.strftime('%S')):
                                    log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 程序结束,了吧 原因:操作执行完毕,操作:%s\n\n' % i)
                                    temp = int(i.split(':')[3])
                                    system("shutdown -s -f -t %d" % temp)
                                    t = Thread(target=count_down, args=(temp,))
                                    t.setDaemon(True)
                                    main(temp)
                                    log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 关机操作被取消\n\n')
                                    sys.exit()
                elif int(i.split(':')[0]) == int(now.strftime('%H')):
                    log(' 目标小时 = 当前小时(%s = %s)' % (i.split(':')[0], now.strftime('%H')))
                    if int(i.split(':')[1]) > int(now.strftime('%M')):
                        log(' 目标分钟 > 当前分钟(%s >= %s), 开始判断\n' % (i.split(':')[1], now.strftime('%M')))
                        while True:
                            now = dt.now()  # 获取当前时间信息
                            if int(i.split(':')[1]) == int(now.strftime('%M')):
                                if int(i.split(':')[2]) <= int(now.strftime('%S')):
                                    log(now.strftime(
                                        '%Y-%m-%d %H:%M:%S') + ' 程序结束,了吧 原因:操作执行完毕,操作:%s\n\n' % i)
                                    temp = int(i.split(':')[3])
                                    system("shutdown -s -f -t %d" % temp)
                                    t = Thread(target=count_down, args=(temp,))
                                    t.setDaemon(True)
                                    main(temp)
                                    log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 关机操作被取消\n\n')
                                    sys.exit()
                    else:
                        pass
        log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 程序结束 原因:没有可执行的操作\n\n')
        sys.exit()
    except FileNotFoundError:
        log(now.strftime('%Y-%m-%d %H:%M:%S') + ' 程序结束 原因:未找到文件\n\n')
        sys.exit()
