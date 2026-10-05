import os
import sys

import pytest

# 无界面运行：本地和 CI 都不弹窗口、不动鼠标键盘
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "_vendor")
if os.path.isdir(VENDOR):
    sys.path.insert(0, VENDOR)
sys.path.insert(0, ROOT)

from desktodo import config  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_paths(tmp_path, monkeypatch):
    """每个测试用独立的临时数据目录，绝不碰真实数据和「启动」文件夹。"""
    data = tmp_path / "data"
    monkeypatch.setattr(config, "DATA_DIR", str(data))
    monkeypatch.setattr(config, "DATA_FILE", str(data / "todos.json"))
    monkeypatch.setattr(config, "BACKUP_DIR", str(data / "backups"))
    monkeypatch.setattr(config, "LOG_FILE", str(data / "desk_todo.log"))
    monkeypatch.setattr(config, "LEGACY_FILE", str(tmp_path / "legacy" / "todos.json"))
    monkeypatch.setattr(config, "STARTUP_DIR", str(tmp_path / "Startup"))
    monkeypatch.setattr(config, "STARTUP_VBS", str(tmp_path / "Startup" / "DeskTodo.vbs"))
    return tmp_path


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtGui import QGuiApplication
    app = QGuiApplication.instance() or QGuiApplication([])
    yield app
