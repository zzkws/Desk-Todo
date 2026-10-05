"""界面层测试：QML 能干净加载、拖动排序跟手、点框外失焦。全部是合成事件，不动真实鼠标。"""

import time

import pytest
from PySide6.QtCore import QEvent, QPointF, Qt, QUrl, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem

from desktodo import config, storage


@pytest.fixture
def ui(qapp):
    from desktodo.backend import Backend
    from desktodo.desk import FocusDropper
    msgs = []
    qInstallMessageHandler(lambda _m, _c, s: msgs.append(s))
    st = storage.load_state()
    st["goals"] = [{"id": "a", "text": "交付 前景物体表面 segmentation 方法", "status": "active"},
                   {"id": "b", "text": "尝试 GPT decisions api 实现缺陷检测", "status": "active"},
                   {"id": "c", "text": "交付 prompt 大模型 api 判断缺陷方案", "status": "active"},
                   {"id": "d", "text": "第四条目标", "status": "active"},
                   {"id": "e", "text": "已经做完的", "status": "done"}]
    b = Backend(st)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", b)
    engine.load(QUrl.fromLocalFile(config.QML_FILE))
    assert engine.rootObjects(), "QML 加载失败：%s" % msgs
    win = engine.rootObjects()[0]
    win.installEventFilter(FocusDropper(win))
    win.setWidth(b.cardWidth + b.shadow)       # 正式运行时由 Desk.place() 设置
    win.show()
    pump(qapp, 150)
    yield qapp, b, win, msgs
    qInstallMessageHandler(None)
    win.close()
    engine.deleteLater()


def pump(app, ms):
    t0 = time.perf_counter()
    while (time.perf_counter() - t0) * 1000 < ms:
        app.processEvents()


def send(win, kind, x, y):
    p = QPointF(x, y)
    buttons = Qt.NoButton if kind == QEvent.MouseButtonRelease else Qt.LeftButton
    QGuiApplication.sendEvent(win, QMouseEvent(kind, p, p, Qt.LeftButton, buttons, Qt.NoModifier))


def active_rows(win):
    lv = win.findChild(QQuickItem, "activeList")
    rows = [it for it in lv.property("contentItem").childItems() if it.property("gid")]
    return sorted(rows, key=lambda it: it.property("index"))


def test_qml_loads_without_warnings(ui):
    _app, b, win, msgs = ui
    noisy = [m for m in msgs if "qml" in m.lower() or "error" in m.lower()]
    assert not noisy
    assert win.findChild(QQuickItem, "activeList").property("count") == b.active.count


def test_drag_reorder_follows_cursor_without_jitter(ui):
    app, b, win, _ = ui
    moves = []
    orig = b.lists["active"].move
    b.lists["active"].move = lambda s, d: (moves.append((s, d)), orig(s, d))[1]

    rows = active_rows(win)
    first = rows[0]
    start = first.mapToScene(QPointF(80, first.height() / 2))
    grab = start.y() - first.mapToScene(QPointF(0, 0)).y()
    third = rows[2]
    end_y = third.mapToScene(QPointF(0, 0)).y() + third.height() * 0.85

    send(win, QEvent.MouseButtonPress, start.x(), start.y())
    errors = []
    for k in range(1, 41):
        y = start.y() + (end_y - start.y()) * k / 40
        send(win, QEvent.MouseMove, start.x(), y)
        pump(app, 8)
        if k > 2:
            dragged = next(r for r in active_rows(win) if r.property("gid") == "a")
            errors.append(abs(dragged.mapToScene(QPointF(0, 0)).y() - (y - grab)))
    send(win, QEvent.MouseButtonRelease, start.x(), end_y)
    pump(app, 400)

    assert max(errors) <= 2                                    # 卡片紧贴鼠标
    assert moves == [(0, 1), (1, 2)]                           # 跨两行只换两次，不来回抖
    assert [g["id"] for g in b.lists["active"].goals()] == ["b", "c", "a", "d"]
    rows = active_rows(win)
    for upper, lower in zip(rows, rows[1:], strict=False):     # 松手后首尾相接
        assert round(lower.property("y")) == round(upper.property("y") + upper.height())
    assert all(abs(r.property("dragOffset") or 0) < 0.5 for r in rows)


def test_clicking_outside_input_drops_focus(ui):
    app, b, win, _ = ui
    inp = win.findChild(QQuickItem, "input")
    header_point = (b.shadow + b.cardWidth * 0.55, 30)
    for x, y in [header_point, (b.shadow + b.cardWidth / 2, b.cardHeight - 15)]:
        inp.forceActiveFocus()
        pump(app, 20)
        assert inp.property("activeFocus")
        send(win, QEvent.MouseButtonPress, x, y)
        send(win, QEvent.MouseButtonRelease, x, y)
        pump(app, 50)
        assert not inp.property("activeFocus")


def test_click_on_tab_still_switches_while_typing(ui):
    app, b, win, _ = ui
    inp = win.findChild(QQuickItem, "input")
    inp.forceActiveFocus()
    pump(app, 20)
    x, y = b.shadow + b.cardWidth * 0.75, 60 + 16
    send(win, QEvent.MouseButtonPress, x, y)
    send(win, QEvent.MouseButtonRelease, x, y)
    pump(app, 50)
    assert b.tab == "archived" and not inp.property("activeFocus")
