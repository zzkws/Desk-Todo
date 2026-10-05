import glob
import json
import os

from desktodo import config, storage


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False))


def test_first_run_seeds_examples():
    st = storage.load_state()
    assert len(st["goals"]) == len(storage.SEED)
    assert all(g["status"] == "active" for g in st["goals"])


def test_migrates_v1_items_and_drops_blank():
    write(config.DATA_FILE, {"items": [{"text": "甲", "done": False},
                                       {"text": "乙", "done": True},
                                       {"text": "   "}],
                             "geometry": {"x": 1, "y": 2, "w": 567, "h": 626},
                             "opacity": 0.9, "topmost": True})
    st = storage.load_state()
    assert [(g["text"], g["status"]) for g in st["goals"]] == [("甲", "active"), ("乙", "done")]
    assert all(set(g) == {"id", "text", "status"} for g in st["goals"])
    # 旧版存的是物理像素，不沿用
    assert st["geometry"] == {"w": config.DEF_W, "h": config.DEF_H}
    assert st["version"] == storage.VERSION


def test_migrates_v2_and_keeps_ids():
    write(config.DATA_FILE, {"version": 2, "items": [
        {"id": "keep-me", "text": " 多个   空格 ", "done": False, "created": "x"}]})
    g = storage.load_state()["goals"][0]
    assert g == {"id": "keep-me", "text": "多个 空格", "status": "active"}


def test_invalid_tab_and_geometry_are_sanitised():
    write(config.DATA_FILE, {"version": 3, "goals": [], "tab": "bogus",
                             "geometry": {"w": 10, "h": 10}})
    st = storage.load_state()
    assert st["tab"] == "active"
    assert st["geometry"] == {"w": config.MIN_W, "h": config.MIN_H}


def test_corrupt_file_is_kept_aside_not_overwritten():
    write(config.DATA_FILE, '{"goals": [{"text": "很重要"')
    st = storage.load_state()
    assert st["goals"] == []                       # 不静默塞回示例
    baks = glob.glob(config.DATA_FILE + ".corrupt-*")
    assert len(baks) == 1
    assert "很重要" in open(baks[0], encoding="utf-8").read()
    assert not os.path.exists(config.DATA_FILE)    # 下次保存不会覆盖留档


def test_save_is_atomic_and_round_trips():
    st = storage.load_state()
    st["goals"] = [{"id": "a", "text": "中文不转义", "status": "archived"}]
    assert storage.save_state(st)
    assert not os.path.exists(config.DATA_FILE + ".tmp")
    assert "中文不转义" in open(config.DATA_FILE, encoding="utf-8").read()
    assert storage.load_state()["goals"] == st["goals"]


def test_adopts_legacy_location_once():
    write(config.LEGACY_FILE, {"items": [{"text": "旧位置", "done": False}]})
    assert [g["text"] for g in storage.load_state()["goals"]] == ["旧位置"]
    assert os.path.exists(config.LEGACY_FILE)      # 旧文件保留
    write(config.DATA_FILE, {"version": 3, "goals": [{"text": "新位置", "status": "active"}]})
    assert [g["text"] for g in storage.load_state()["goals"]] == ["新位置"]


def test_daily_backup_rotation():
    storage.save_state(storage.load_state())
    for k in range(35):
        write(os.path.join(config.BACKUP_DIR, "todos-2000%04d.json" % k), "{}")
    today = storage.daily_backup()
    kept = glob.glob(os.path.join(config.BACKUP_DIR, "todos-*.json"))
    assert today in kept
    assert len(kept) == config.KEEP_BACKUPS


def test_daily_backup_without_data_is_noop():
    assert storage.daily_backup() is None
