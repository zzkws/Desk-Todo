"""程序入口。"""

import os
import subprocess
import sys
import time

from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem  # noqa: F401  注册类型，focusObject() 才能拿到 QQuickItem

from . import config, storage, system, winapi
from .backend import Backend
from .desk import Desk, EventBridge


def _log(_mode, _ctx, msg):
    try:
        with open(config.LOG_FILE, "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (time.strftime("%H:%M:%S"), msg))
    except OSError:
        pass


def _relaunch_after_explorer_restart():
    """窗口挂在桌面下面，资源管理器重启会把它连带销毁；等桌面重建后自己再起来。"""
    for _ in range(60):
        if winapi.desktop_window():
            break
        time.sleep(1)
    time.sleep(2)
    subprocess.Popen([system.pythonw_path(), config.ENTRY_SCRIPT],
                     creationflags=subprocess.DETACHED_PROCESS
                     | subprocess.CREATE_NEW_PROCESS_GROUP)


def main():
    lock = system.acquire_lock()
    if lock is None:
        system.notify_existing()     # 已在运行：把它呼出来
        return 0

    os.makedirs(config.DATA_DIR, exist_ok=True)
    open(config.LOG_FILE, "w").close()
    qInstallMessageHandler(_log)
    storage.daily_backup()

    app = QGuiApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    backend = Backend()
    backend.save()                   # 旧格式迁移后立刻以新格式写回

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(config.QML_FILE))
    if not engine.rootObjects():
        _log(None, None, "QML 加载失败")
        lock.close()
        return 1

    events = EventBridge()
    desk = Desk(app, engine.rootObjects()[0], backend, events)
    desk.start()
    # 后台线程要在 Desk 接上信号之后再启动，否则「快捷键已注册」的消息会丢
    system.start_lock_listener(lock, events)
    system.start_hotkey_thread(events)

    code = app.exec()
    backend.save()
    lock.close()
    if not desk.quitting:
        _relaunch_after_explorer_restart()
    return code
