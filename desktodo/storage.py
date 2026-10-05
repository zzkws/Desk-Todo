"""数据读写：原子写入、每日备份、坏文件留档、旧版本迁移。

只用标准库，不依赖 Qt，便于单独测试。路径默认取自 :mod:`desktodo.config`，
各函数也接受显式路径参数。
"""

import glob
import json
import os
import shutil
import time
import uuid

from . import config

STATUSES = ("active", "done", "archived")
TABS = ("active", "archived")
VERSION = 3

DEFAULTS = {
    "version": VERSION,
    "goals": [],
    "geometry": {"w": config.DEF_W, "h": config.DEF_H},
    "collapsed": False,
    "show_done": False,
    "tab": "active",
    "flush": True,
}

SEED = [
    {"text": "点左边的圆圈，完成一个目标", "status": "active"},
    {"text": "暂时不做的目标，悬停后点右侧的盒子存档", "status": "active"},
]


def new_id():
    return uuid.uuid4().hex[:12]


def normalize_text(text):
    """去掉首尾空白，把连续空白压成一个空格。"""
    return " ".join((text or "").split())


def clean_goal(goal):
    """把任意版本的条目规整为 ``{id, text, status}``；无效条目返回 None。"""
    if not isinstance(goal, dict) or not isinstance(goal.get("text"), str):
        return None
    text = normalize_text(goal["text"])
    if not text:
        return None
    status = goal.get("status")
    if status not in STATUSES:                        # v1/v2 只有 done 字段
        status = "done" if goal.get("done") else "active"
    return {"id": str(goal.get("id") or new_id()), "text": text, "status": status}


def backup_corrupt(path=None):
    """数据文件读不出来时改名留档，绝不静默丢掉用户的条目。返回留档路径。"""
    path = path or config.DATA_FILE
    try:
        bak = "%s.corrupt-%s" % (path, time.strftime("%Y%m%d-%H%M%S"))
        os.replace(path, bak)
        return bak
    except OSError:
        return None


def adopt_legacy(path=None, legacy=None):
    """新位置还没有数据时，从旧位置复制一份过来（旧文件保留不动）。"""
    path = path or config.DATA_FILE
    legacy = legacy or config.LEGACY_FILE
    try:
        if not os.path.exists(path) and os.path.exists(legacy):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            shutil.copy2(legacy, path)
            return True
    except OSError:
        pass
    return False


def load_state(path=None, legacy=None):
    """读取状态并迁移到当前版本。

    - 文件不存在（真正的首次运行）：放两条示例
    - 文件损坏：改名留档后以空清单启动
    - v1/v2：``items`` + ``done`` 迁移为 ``goals`` + ``status``
    """
    path = path or config.DATA_FILE
    st = json.loads(json.dumps(DEFAULTS))
    raw = None
    adopt_legacy(path, legacy)
    if not os.path.exists(path):
        st["goals"] = json.loads(json.dumps(SEED))
    else:
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, ValueError):
            backup_corrupt(path)
    if isinstance(raw, dict):
        st["goals"] = raw.get("goals", raw.get("items")) or []
        for k in ("collapsed", "show_done", "tab", "flush"):
            if k in raw:
                st[k] = raw[k]
        # 旧版存的是物理像素，不沿用
        if raw.get("version") == VERSION and isinstance(raw.get("geometry"), dict):
            st["geometry"] = raw["geometry"]
    st["goals"] = [c for c in (clean_goal(g) for g in st["goals"]) if c]
    g = st["geometry"]
    st["geometry"] = {"w": max(config.MIN_W, int(g.get("w") or config.DEF_W)),
                      "h": max(config.MIN_H, int(g.get("h") or config.DEF_H))}
    st["collapsed"] = bool(st["collapsed"])
    st["show_done"] = bool(st["show_done"])
    st["flush"] = bool(st["flush"])
    st["tab"] = st["tab"] if st["tab"] in TABS else "active"
    st["version"] = VERSION
    return st


def save_state(state, path=None):
    """原子写入：先写临时文件再整体替换，写到一半断电也不会留下半个文件。"""
    path = path or config.DATA_FILE
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def daily_backup(path=None, backup_dir=None, keep=None):
    """每天第一次运行时复制一份，只保留最近 ``keep`` 份。返回当天备份路径。"""
    path = path or config.DATA_FILE
    backup_dir = backup_dir or config.BACKUP_DIR
    keep = keep or config.KEEP_BACKUPS
    try:
        if not os.path.exists(path):
            return None
        os.makedirs(backup_dir, exist_ok=True)
        dst = os.path.join(backup_dir, "todos-%s.json" % time.strftime("%Y%m%d"))
        if not os.path.exists(dst):
            shutil.copy2(path, dst)
        for old in sorted(glob.glob(os.path.join(backup_dir, "todos-*.json")))[:-keep]:
            os.remove(old)
        return dst
    except OSError:
        return None
