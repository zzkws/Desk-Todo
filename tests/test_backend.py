import json

import pytest

from desktodo import config, storage


@pytest.fixture
def b(qapp):
    from desktodo.backend import Backend
    st = storage.load_state()
    st["goals"] = [{"id": "a", "text": "甲", "status": "active"},
                   {"id": "b", "text": "乙", "status": "active"},
                   {"id": "c", "text": "丙", "status": "active"},
                   {"id": "d", "text": "丁", "status": "done"}]
    return Backend(st)


def texts(b, section):
    return [g["text"] for g in b.lists[section].goals()]


def test_add_puts_new_goal_on_top(b):
    b.add("  新   目标 ")
    b.add("   ")
    assert texts(b, "active") == ["新 目标", "甲", "乙", "丙"]


def test_complete_and_uncomplete(b):
    b.complete("b")
    assert texts(b, "active") == ["甲", "丙"] and texts(b, "done") == ["乙", "丁"]
    b.uncomplete("b")
    assert texts(b, "active")[0] == "乙"


def test_archive_offers_undo(b):
    toasts = []
    b.toast.connect(toasts.append)
    b.archive("a")
    assert texts(b, "archived") == ["甲"] and b.canUndo
    assert toasts == ["已存档「甲」"]
    b.undo()
    assert texts(b, "active") == ["甲", "乙", "丙"] and texts(b, "archived") == []
    assert not b.canUndo


def test_unarchive_returns_to_top(b):
    b.archive("c")
    b.unarchive("c")
    assert texts(b, "active")[0] == "丙"


def test_remove_and_undo_restores_position(b):
    b.remove("b")
    assert "乙" not in texts(b, "active")
    b.undo()
    assert texts(b, "active") == ["甲", "乙", "丙"]


def test_rename_and_blank_rename_deletes(b):
    b.rename("a", "  改  名 ")
    assert texts(b, "active")[0] == "改 名"
    b.rename("a", "   ")
    assert "改 名" not in texts(b, "active") and b.canUndo


def test_move_and_move_to_top(b):
    b.moveActive(0, 2)
    assert texts(b, "active") == ["乙", "丙", "甲"]
    b.moveActive(5, 0)                          # 越界忽略
    b.moveToTop("a")
    assert texts(b, "active") == ["甲", "乙", "丙"]


def test_clear_done_is_undoable(b):
    b.clearDone()
    assert texts(b, "done") == []
    b.undo()
    assert texts(b, "done") == ["丁"]


def test_expire_undo(b):
    b.remove("a")
    b.expireUndo()
    assert not b.canUndo
    b.undo()
    assert "甲" not in texts(b, "active")


def test_save_writes_sections_in_order(b):
    b.archive("a")
    b.save()
    saved = json.load(open(config.DATA_FILE, encoding="utf-8"))
    assert [g["status"] for g in saved["goals"]] == ["active", "active", "done", "archived"]


def test_ui_state_setters(b):
    b.setTab("archived")
    assert b.tab == "archived"
    b.setTab("nonsense")
    assert b.tab == "archived"
    b.setCardSize(10, 10)
    assert (b.cardWidth, b.cardHeight) == (config.MIN_W, config.MIN_H)
    collapsed = b.collapsed
    b.toggleCollapsed()
    assert b.collapsed != collapsed


def test_autostart_toggle_uses_isolated_folder(b):
    b.setAutostart(True)
    assert b.autostart
    script = open(config.STARTUP_VBS, encoding="mbcs").read()
    assert "desk_todo.pyw" in script and '""' in script
    b.setAutostart(False)
    assert not b.autostart
