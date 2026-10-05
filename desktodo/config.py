"""路径与常量。

数据默认放在程序目录下的 ``data/``，而不是 ``%APPDATA%``：MSIX 打包的应用（例如某些桌面客户端）
里启动的进程，对 ``%APPDATA%`` 的读写会被系统重定向到一份私有副本，和开机自启 / 双击启动时
读写的真实文件不是同一份，数据会悄悄分叉。可以用环境变量 ``DESKTODO_DATA_DIR`` 改到别处。
"""

import os

APP_NAME = "DeskTodo"

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(PACKAGE_DIR)
ENTRY_SCRIPT = os.path.join(ROOT_DIR, "desk_todo.pyw")
QML_FILE = os.path.join(PACKAGE_DIR, "qml", "Main.qml")

DATA_DIR = os.environ.get("DESKTODO_DATA_DIR") or os.path.join(ROOT_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "todos.json")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
LOG_FILE = os.path.join(DATA_DIR, "desk_todo.log")
KEEP_BACKUPS = 30

# 更早的版本把数据放在 %APPDATA%\DeskTodo；新位置为空时从这里接收一次
LEGACY_FILE = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), APP_NAME,
                           "todos.json")

STARTUP_DIR = os.path.join(os.environ.get("APPDATA") or "", "Microsoft", "Windows",
                           "Start Menu", "Programs", "Startup")
STARTUP_VBS = os.path.join(STARTUP_DIR, "DeskTodo.vbs")

# 单实例锁兼「呼出」通道
LOCK_PORT = int(os.environ.get("DESKTODO_PORT") or 50573)

# 布局（逻辑像素）
SHADOW = 28                 # 卡片外围留给阴影的透明边
GAP = 14                    # 悬浮模式下卡片离屏幕边的距离
DEF_W, DEF_H = 340, 460
MIN_W, MIN_H = 280, 240
