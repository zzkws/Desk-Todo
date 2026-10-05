import queue

from desktodo import config, system


def test_single_instance_lock_and_summon(monkeypatch):
    monkeypatch.setattr(config, "LOCK_PORT", 50991)
    lock = system.acquire_lock()
    assert lock is not None
    try:
        assert system.acquire_lock() is None                 # 第二个实例被拒
        events = queue.Queue()
        system.start_lock_listener(lock, events)
        assert system.notify_existing()
        assert events.get(timeout=2) == ("summon", None)     # 原实例收到呼出
    finally:
        lock.close()


def test_startup_script_quotes_paths():
    script = system.startup_script()
    assert script.startswith('Set WshShell = CreateObject("WScript.Shell")')
    assert '""' + config.ENTRY_SCRIPT + '""' in script
    assert script.rstrip().endswith(", 0, False")
