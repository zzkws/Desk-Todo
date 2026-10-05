"""窗口的系统行为：钉在右上角、挂到桌面、快捷键呼出、点框外失焦。"""

import time

from PySide6.QtCore import QEvent, QMetaObject, QObject, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication

from . import config, storage, winapi


class EventBridge(QObject):
    """后台线程（全局快捷键、二次启动通知）→ 主线程。

    后台线程调 ``put((kind, value))``，信号以排队连接送到主线程并立即处理，不需要轮询。
    """
    fire = Signal(str, object)

    def put(self, item):
        self.fire.emit(item[0], item[1])


def _is_text_input(obj):
    return obj is not None and "Text" in obj.metaObject().className()


class FocusDropper(QObject):
    """点到正在输入的框以外的任何地方，输入框就失焦。

    在窗口层面看每一次按下，不受控件叠放影响；只负责失焦，点击照常交给被点的控件。
    """

    def __init__(self, win):
        super().__init__(win)
        self.win = win

    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.MouseButtonPress:
            fo = QGuiApplication.focusObject()
            if _is_text_input(fo):
                # 主输入框按整个外壳算（点左边的「+」也算在框里）
                box = fo.parentItem() if fo.objectName() == "input" else fo
                try:
                    tl = box.mapToScene(QPointF(0, 0))
                    rect = QRectF(tl.x(), tl.y(), box.width(), box.height())
                    inside = rect.contains(ev.position())
                except (AttributeError, RuntimeError):
                    inside = True
                if not inside:
                    QMetaObject.invokeMethod(self.win, "dropFocus", Qt.QueuedConnection)
        return False


class Desk(QObject):
    """管理 QML 根窗口的位置与系统行为。层级就是普通窗口，交给 Windows 处理。"""

    def __init__(self, app, win, backend, events):
        super().__init__()
        self.app, self.win, self.b = app, win, backend
        self.quitting = False        # 用户主动退出（区别于资源管理器重启把窗口带走）
        self._ticks = 0
        self._day = time.strftime("%Y%m%d")
        backend.geometryRequest.connect(self.place)
        backend.quitRequested.connect(self.quit)
        events.fire.connect(self.on_event)
        self.dropper = FocusDropper(win)
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.tick)

    def hwnd(self):
        return int(self.win.winId())

    def start(self):
        self.place()
        self.win.show()
        winapi.attach_to_desktop(self.hwnd())
        self.win.installEventFilter(self.dropper)
        self.timer.start()

    # ---------------- 位置 ----------------
    def target_pos(self):
        scr = (self.win.screen() or QGuiApplication.primaryScreen()).geometry()
        right = scr.x() + scr.width()
        if self.b.flush:             # 卡片右上角正好压住屏幕右上角
            return right - self.b.cardWidth - config.SHADOW, scr.y()
        return (right - config.GAP - self.b.cardWidth - config.SHADOW,
                scr.y() + config.GAP - config.SHADOW)

    def target_width(self):
        return self.b.cardWidth + config.SHADOW + (0 if self.b.flush else config.SHADOW)

    def place(self):
        """宽度和位置一次设好（分两步会有一帧卡片偏出屏幕）。高度由 QML 管理，配合折叠动画。"""
        x, y = self.target_pos()
        w = self.target_width()
        if (self.win.x(), self.win.y(), self.win.width()) != (x, y, w):
            self.win.setGeometry(x, y, w, self.win.height())

    # ---------------- 事件 ----------------
    def summon(self):
        """快捷键 / 再次启动：带到前面并聚焦输入框（不置顶）。"""
        if self.b.collapsed:
            self.b.toggleCollapsed()
        self.b.setTab("active")
        winapi.bring_to_front(self.hwnd())
        self.win.requestActivate()
        self.b.summoned.emit()

    def on_event(self, kind, value):
        if kind == "summon":
            self.summon()
        elif kind == "hotkey_label":
            self.b.set_hotkey(value)

    def tick(self):
        if not winapi.is_window(self.hwnd()):      # 资源管理器重启时窗口会被连带销毁
            self.app.quit()
            return
        day = time.strftime("%Y%m%d")
        if day != self._day:
            self._day = day
            storage.daily_backup()
        self.place()                                 # 分辨率变化或被意外挪动后归位
        self._ticks += 1
        if self._ticks % 50 == 0:                    # 每 5 秒确认一次仍挂在桌面上
            winapi.attach_to_desktop(self.hwnd())

    def quit(self):
        self.quitting = True
        self.b.save()
        self.app.quit()
