"""用到的少量 Win32 API（ctypes）。"""

import ctypes
import ctypes.wintypes as wt

user32 = ctypes.windll.user32
user32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_uint]
user32.SetWindowPos.restype = wt.BOOL
user32.SetForegroundWindow.argtypes = [wt.HWND]
user32.FindWindowW.argtypes = [wt.LPCWSTR, wt.LPCWSTR]
user32.FindWindowW.restype = wt.HWND
user32.GetWindow.argtypes = [wt.HWND, ctypes.c_uint]
user32.GetWindow.restype = wt.HWND
user32.IsWindow.argtypes = [wt.HWND]
user32.SetWindowLongPtrW.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_ssize_t]
user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t

HWND_TOP = 0
SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE = 0x0001, 0x0002, 0x0010
GW_OWNER = 4
GWLP_HWNDPARENT = -8
WM_HOTKEY = 0x0312
MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x1, 0x2, 0x4000


def bring_to_front(hwnd):
    """像点击一样带到前面（不置顶）。"""
    user32.SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
    user32.SetForegroundWindow(hwnd)


def desktop_window():
    return user32.FindWindowW("Progman", None)


def attach_to_desktop(hwnd):
    """把窗口的「所有者」设为桌面（Progman）。

    「显示桌面」（Win+D、触摸板三指下滑）会收起所有普通顶层窗口，但不收起属于桌面的窗口。
    只改所有者、不改父窗口：键盘输入仍走本进程，不牵连资源管理器。
    """
    progman = desktop_window()
    if not progman:
        return False
    if user32.GetWindow(hwnd, GW_OWNER) != progman:
        user32.SetWindowLongPtrW(hwnd, GWLP_HWNDPARENT, progman)
    return user32.GetWindow(hwnd, GW_OWNER) == progman


def is_window(hwnd):
    return bool(user32.IsWindow(hwnd))
