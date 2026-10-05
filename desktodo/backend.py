"""暴露给 QML 的后端：三个分区的列表模型、界面状态、所有用户操作。"""

import os

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from . import config, storage, system
from .models import GoalList
from .storage import STATUSES, TABS, new_id, normalize_text


def shorten(text, n=12):
    return text if len(text) <= n else text[:n] + "…"


class Backend(QObject):
    toast = Signal(str)              # 带「撤销」的提示
    summoned = Signal()              # 快捷键呼出：QML 把焦点交给输入框
    geometryRequest = Signal()       # 尺寸 / 模式变了，窗口需要重新贴角
    quitRequested = Signal()

    collapsedChanged = Signal()
    showDoneChanged = Signal()
    tabChanged = Signal()
    flushChanged = Signal()
    cardSizeChanged = Signal()
    hotkeyChanged = Signal()
    canUndoChanged = Signal()
    autostartChanged = Signal()

    def __init__(self, state=None, parent=None):
        super().__init__(parent)
        self.state = state or storage.load_state()
        by = {s: [g for g in self.state["goals"] if g["status"] == s] for s in STATUSES}
        self.lists = {s: GoalList(by[s], self) for s in STATUSES}
        self._undo = None
        self._hotkey = ""
        self.busy = False            # 拖动 / 缩放中
        # 拖动排序、缩放会连续触发修改，合并成一次写盘
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self.save)

    # ---------------- 属性 ----------------
    active = Property(QObject, lambda self: self.lists["active"], constant=True)
    done = Property(QObject, lambda self: self.lists["done"], constant=True)
    archived = Property(QObject, lambda self: self.lists["archived"], constant=True)

    collapsed = Property(bool, lambda self: self.state["collapsed"], notify=collapsedChanged)
    showDone = Property(bool, lambda self: self.state["show_done"], notify=showDoneChanged)
    tab = Property(str, lambda self: self.state["tab"], notify=tabChanged)
    flush = Property(bool, lambda self: self.state["flush"], notify=flushChanged)
    cardWidth = Property(int, lambda self: self.state["geometry"]["w"], notify=cardSizeChanged)
    cardHeight = Property(int, lambda self: self.state["geometry"]["h"], notify=cardSizeChanged)
    shadow = Property(int, lambda self: config.SHADOW, constant=True)
    hotkey = Property(str, lambda self: self._hotkey, notify=hotkeyChanged)
    canUndo = Property(bool, lambda self: self._undo is not None, notify=canUndoChanged)
    autostart = Property(bool, lambda self: system.autostart_enabled(), notify=autostartChanged)

    def set_hotkey(self, label):
        self._hotkey = label or ""
        self.hotkeyChanged.emit()

    # ---------------- 内部 ----------------
    def find(self, gid):
        """返回 (分区名, 列表, 行号)；找不到时为 (None, None, -1)。"""
        for name, lst in self.lists.items():
            r = lst.row_of(gid)
            if r >= 0:
                return name, lst, r
        return None, None, -1

    def save(self):
        goals = []
        for s in STATUSES:
            for g in self.lists[s].goals():
                g["status"] = s
                goals.append(g)
        self.state["goals"] = goals
        return storage.save_state(self.state)

    def _snapshot(self):
        return {s: [dict(g) for g in self.lists[s].goals()] for s in STATUSES}

    def _offer_undo(self, snap, msg):
        self._undo = snap
        self.canUndoChanged.emit()
        self.toast.emit(msg)

    def _transfer(self, gid, dest, row=0):
        name, lst, r = self.find(gid)
        if lst is None or name == dest:
            return None
        g = lst.take(r)
        self.lists[dest].insert(row, g)
        self.save()
        return g

    # ---------------- 目标操作 ----------------
    @Slot(str)
    def add(self, text):
        text = normalize_text(text)
        if text:
            self.lists["active"].insert(0, {"id": new_id(), "text": text, "status": "active"})
            self.save()

    @Slot(str)
    def complete(self, gid):
        self._transfer(gid, "done")

    @Slot(str)
    def uncomplete(self, gid):
        self._transfer(gid, "active")

    @Slot(str)
    def archive(self, gid):
        snap = self._snapshot()
        g = self._transfer(gid, "archived")
        if g:
            self._offer_undo(snap, "已存档「%s」" % shorten(g["text"]))

    @Slot(str)
    def unarchive(self, gid):
        self._transfer(gid, "active")

    @Slot(str)
    def remove(self, gid):
        _name, lst, r = self.find(gid)
        if lst is None:
            return
        snap = self._snapshot()
        g = lst.take(r)
        self.save()
        self._offer_undo(snap, "已删除「%s」" % shorten(g["text"]))

    @Slot(str, str)
    def rename(self, gid, text):
        """改名；改成空白等于删除（可撤销）。"""
        text = normalize_text(text)
        _name, lst, r = self.find(gid)
        if lst is None:
            return
        if not text:
            self.remove(gid)
        elif text != lst.goals()[r]["text"]:
            lst.set_text(r, text)
            self.save()

    @Slot(int, int)
    def moveActive(self, src, dst):
        if self.lists["active"].move(src, dst):
            self._save_timer.start()

    @Slot(str)
    def moveToTop(self, gid):
        _name, lst, r = self.find(gid)
        if lst is not None and lst.move(r, 0):
            self.save()

    @Slot()
    def clearDone(self):
        n = self.lists["done"].count
        if not n:
            return
        snap = self._snapshot()
        self.lists["done"].reset([])
        self.save()
        self._offer_undo(snap, "已清空 %d 个已完成" % n)

    @Slot()
    def undo(self):
        if not self._undo:
            return
        for s in STATUSES:
            self.lists[s].reset(self._undo[s])
        self._undo = None
        self.canUndoChanged.emit()
        self.save()

    @Slot()
    def expireUndo(self):
        if self._undo is not None:
            self._undo = None
            self.canUndoChanged.emit()

    # ---------------- 界面状态 ----------------
    @Slot()
    def toggleCollapsed(self):
        self.state["collapsed"] = not self.state["collapsed"]
        self.collapsedChanged.emit()
        self.geometryRequest.emit()
        self.save()

    @Slot(bool)
    def setShowDone(self, on):
        self.state["show_done"] = bool(on)
        self.showDoneChanged.emit()
        self.save()

    @Slot(str)
    def setTab(self, tab):
        if tab in TABS and tab != self.state["tab"]:
            self.state["tab"] = tab
            self.tabChanged.emit()
            self.save()

    @Slot(bool)
    def setFlush(self, on):
        self.state["flush"] = bool(on)
        self.flushChanged.emit()
        self.geometryRequest.emit()
        self.save()

    @Slot(float, float)
    def setCardSize(self, w, h):
        g = self.state["geometry"]
        w, h = max(config.MIN_W, int(round(w))), max(config.MIN_H, int(round(h)))
        if (w, h) != (g["w"], g["h"]):
            g["w"], g["h"] = w, h
            self.cardSizeChanged.emit()
            self.geometryRequest.emit()
            self._save_timer.start()

    @Slot(bool)
    def setBusy(self, on):
        self.busy = bool(on)

    # ---------------- 系统 ----------------
    @Slot(bool)
    def setAutostart(self, on):
        system.set_autostart(on)
        self.autostartChanged.emit()

    @Slot()
    def openDataDir(self):
        try:
            os.makedirs(config.DATA_DIR, exist_ok=True)
            os.startfile(config.DATA_DIR)
        except OSError:
            pass

    @Slot()
    def quit(self):
        self.quitRequested.emit()
