# automatic-shutdown

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 项目简介

`automatic-shutdown` 是一个 Windows 下的定时关机工具，支持多计划、临时计划、托盘操作和倒计时提醒。适合需要定时关机、节能或家长控制等场景。

## 主要特性

- 支持每周每天自定义多个关机计划
- 支持添加临时关机计划（仅本次有效）
- 关机前弹窗倒计时提醒，可选择立即关机或跳过
- 托盘图标，右键菜单快速操作
- 支持浅色/深色主题切换
- 日志记录关机与操作历史

## 安装与运行

1. **环境要求**
   - Windows 10/11
   - Python 3.8 及以上

2. **依赖安装**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行项目** 
   ```bash
   python main.py
   ```
   运行后会在系统托盘显示图标，右键点击可进行各种操作。
4. **图标说明**
   ![image](lib/Light.ico)

## 文件结构

```
LICENSE
main.py
README.md
requirements.txt
config/
lib/
old/
```

- `main.py`：主程序入口，托盘与调度逻辑
- `lib/stop.py`：线程停止工具
- `lib/style.c`：主题检测C语言代码
- `config/config.json`：关机计划与设置
- `config/log.txt`：日志文件
- `old/`：过去的版本，算得上是我的怀念吧

## 使用说明

- 托盘菜单可快速修改计划、添加临时计划、查看帮助、设置主题、退出程序
- 支持多计划
- 日志自动记录每次关机与操作


## 初学者，做的比较简单，欢迎提出意见和建议。
## License

MIT License © 2024-2025 lowyyh