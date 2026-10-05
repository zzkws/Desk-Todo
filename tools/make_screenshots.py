"""生成 README 用的截图（示例数据，离屏渲染，不读写真实数据）。

    python tools/make_screenshots.py
"""

import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "_vendor"))
sys.path.insert(0, ROOT)
# 用正常平台渲染（离屏平台找不到系统字体），窗口放在屏幕外，不会闪现
os.environ.setdefault("QT_SCALE_FACTOR", "2")
_TMP = tempfile.mkdtemp(prefix="desktodo_shot_")
os.environ["DESKTODO_DATA_DIR"] = _TMP

from PySide6.QtCore import QPointF, QRectF, Qt, QUrl  # noqa: E402
from PySide6.QtGui import (  # noqa: E402
    QColor,
    QGuiApplication,
    QImage,
    QLinearGradient,
    QPainter,
    QRadialGradient,
)
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402
from PySide6.QtQuick import QQuickWindow  # noqa: E402,F401  注册类型，根窗口才有 grabWindow()

from desktodo import config, storage  # noqa: E402
from desktodo.backend import Backend  # noqa: E402

config.LEGACY_FILE = os.path.join(_TMP, "no-legacy.json")   # 不读任何真实数据
OUT = os.path.join(ROOT, "docs")
SAMPLE = [
    ("读完《深度学习》第 5 章，整理笔记", "active"),
    ("Ship v1.0 of the side project", "active"),
    ("整理本周实验记录", "active"),
    ("回复导师的邮件", "done"),
    ("订下周的高铁票", "done"),
    ("学日语", "archived"),
    ("搭一个个人博客", "archived"),
]


def pump(app, ms):
    t0 = time.perf_counter()
    while (time.perf_counter() - t0) * 1000 < ms:
        app.processEvents()


def render(app, tab, toast=None):
    st = storage.load_state()
    st["goals"] = [{"id": storage.new_id(), "text": t, "status": s} for t, s in SAMPLE]
    st.update(tab=tab, show_done=True, flush=False, collapsed=False,
              geometry={"w": 340, "h": 525})
    b = Backend(st)
    b.set_hotkey("Ctrl+Alt+T")
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", b)
    engine.load(QUrl.fromLocalFile(config.QML_FILE))
    win = engine.rootObjects()[0]
    win.setGeometry(-6000, -6000, b.cardWidth + 2 * b.shadow, win.height())
    win.show()
    pump(app, 300)
    if toast:
        b.toast.emit(toast)
        pump(app, 500)
    img = win.grabWindow()
    win.close()
    return img


def backdrop(w, h):
    """暖色渐变底，模拟桌面壁纸。"""
    img = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
    p = QPainter(img)
    g = QLinearGradient(0, 0, w, h)
    g.setColorAt(0, QColor("#E9C9A8"))
    g.setColorAt(0.55, QColor("#C98E6A"))
    g.setColorAt(1, QColor("#6E5446"))
    p.fillRect(img.rect(), g)
    glow = QRadialGradient(QPointF(w * 0.2, h * 0.25), w * 0.6)
    glow.setColorAt(0, QColor(255, 244, 228, 150))
    glow.setColorAt(1, QColor(255, 244, 228, 0))
    p.fillRect(img.rect(), glow)
    p.end()
    return img


def compose(cards, path, pad=56, gap=40):
    w = sum(c.width() for c in cards) + gap * (len(cards) - 1) + 2 * pad
    h = max(c.height() for c in cards) + 2 * pad
    img = backdrop(w, h)
    p = QPainter(img)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    x = pad
    for c in cards:
        p.drawImage(QRectF(x, pad, c.width(), c.height()), c)
        x += c.width() + gap
    p.end()
    # 输出 1x（高分屏渲染后缩小，边缘更干净）
    img = img.scaled(w // 2, h // 2, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    img.save(path)
    print("saved", path, img.width(), "x", img.height())


def main():
    app = QGuiApplication(sys.argv)
    os.makedirs(OUT, exist_ok=True)
    active = render(app, "active", toast="已存档「搭一个个人博客」")
    archived = render(app, "archived")
    compose([active, archived], os.path.join(OUT, "screenshot.png"))


if __name__ == "__main__":
    main()
