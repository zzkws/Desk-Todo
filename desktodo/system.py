"""进程级功能：单实例、全局快捷键、开机自启。"""

import ctypes
import ctypes.wintypes as wt
import os
import socket
import sys
import threading

from . import config
from .winapi import MOD_ALT, MOD_CONTROL, MOD_NOREPEAT, WM_HOTKEY, user32

# 依次尝试，前一个被别的软件占用时顺延
HOTKEYS = [
    (MOD_CONTROL | MOD_ALT, 0x54, "Ctrl+Alt+T"),
    (MOD_CONTROL | MOD_ALT, 0x59, "Ctrl+Alt+Y"),
    (MOD_CONTROL | MOD_ALT, 0x4A, "Ctrl+Alt+J"),
]


# ---------------- 单实例 ----------------
def acquire_lock(port=None):
    """占住本地端口作为单实例锁；成功返回 socket，已有实例时返回 None。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port or config.LOCK_PORT))
        s.listen(4)
        return s
    except OSError:
        s.close()
        return None


def notify_existing(port=None):
    """通知已在运行的实例把自己呼出来。"""
    try:
        c = socket.create_connection(("127.0.0.1", port or config.LOCK_PORT), timeout=1.0)
        c.sendall(b"show")
        c.close()
        return True
    except OSError:
        return False


def start_lock_listener(sock, events):
    """后台线程：收到二次启动的通知就发出 ``summon`` 事件。"""
    def run():
        while True:
            try:
                c, _ = sock.accept()
            except OSError:
                return
            try:
                c.settimeout(1.0)
                data = c.recv(16)
            except OSError:
                data = b""
            finally:
                c.close()
            if data.startswith(b"show"):
                events.put(("summon", None))

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t


# ---------------- 全局快捷键 ----------------
def start_hotkey_thread(events):
    """后台线程注册全局快捷键，先发出 ``hotkey_label``（注册成功的组合，失败为 None），
    之后每次按下发出 ``summon``。RegisterHotKey 绑定到调用线程，所以消息循环也在这个线程里。"""
    def run():
        label = None
        for mods, vk, name in HOTKEYS:
            if user32.RegisterHotKey(None, 1, mods | MOD_NOREPEAT, vk):
                label = name
                break
        events.put(("hotkey_label", label))
        if not label:
            return
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY:
                events.put(("summon", None))

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t


# ---------------- 开机自启 ----------------
def pythonw_path():
    """当前解释器对应的 pythonw.exe（无控制台窗口）。"""
    exe = sys.executable or ""
    if os.path.basename(exe).lower() == "python.exe":
        cand = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.exists(cand):
            return cand
    return exe


def startup_script():
    cmd = '"%s" "%s"' % (pythonw_path(), config.ENTRY_SCRIPT)
    lit = '"' + cmd.replace('"', '""') + '"'
    return ('Set WshShell = CreateObject("WScript.Shell")\r\n'
            'WshShell.Run ' + lit + ', 0, False\r\n')


def autostart_enabled():
    return os.path.exists(config.STARTUP_VBS)


def set_autostart(on):
    """在「启动」文件夹里放 / 删一个 VBS（不弹控制台）。"""
    try:
        if on:
            os.makedirs(config.STARTUP_DIR, exist_ok=True)
            with open(config.STARTUP_VBS, "w", encoding="mbcs", errors="replace") as f:
                f.write(startup_script())
        elif os.path.exists(config.STARTUP_VBS):
            os.remove(config.STARTUP_VBS)
    except OSError:
        pass
    return autostart_enabled()
