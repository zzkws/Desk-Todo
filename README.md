<div align="center">

# Desk Todo

**A quiet goal list that lives in the top-right corner of your Windows desktop.**

[简体中文](README.zh-CN.md) · English

[![CI](https://github.com/zzkws/Desk-Todo/actions/workflows/ci.yml/badge.svg)](https://github.com/zzkws/Desk-Todo/actions/workflows/ci.yml)
![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078D4)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)

<img src="docs/screenshot.png" alt="Desk Todo — active goals and archive" width="760">

</div>

Desk Todo is a small always-there card for the things you actually intend to do on your computer. It sits flush against the top-right corner of the screen, survives *Show desktop*, and stays out of the way like any normal window. Goals you are not doing *right now* go to the **archive** instead of cluttering the list; goals you will never do get deleted.

The look borrows Claude's warm palette — ivory surfaces and a coral accent — with Apple-style rounded cards, a segmented control and quick, physical animations.

## Features

- **Goals, not tasks** — three states: *In progress*, *Done* (struck through, collapsible), *Archived* (not now). Delete is for "never".
- **Pinned to the corner** — flush with the top-right edge (or a floating card, 14 px in), re-anchors after resolution changes, cannot be dragged away.
- **Survives *Show desktop*** — <kbd>Win</kbd>+<kbd>D</kbd> and the three-finger swipe minimise everything else; the card stays.
- **Normal window layering** — click it and it comes forward, click elsewhere and it goes behind. No fighting with the window manager.
- **Global hotkey** — <kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>T</kbd> brings it forward with the cursor in the input box (falls back to <kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>Y</kbd> / <kbd>J</kbd> if taken).
- **Undo** — archive, delete and "clear done" show an undo toast for 5 s (<kbd>Ctrl</kbd>+<kbd>Z</kbd> works too).
- **Drag to reorder** — the dragged card sticks to the cursor; neighbours slide out of the way.
- **Your data stays yours** — a plain JSON file next to the program, written atomically, backed up daily (30 days kept); a corrupt file is set aside, never silently overwritten.
- **Starts with Windows** — one toggle in the <kbd>⋯</kbd> menu.

## Requirements

- Windows 10 or 11
- Python 3.10+ (64-bit)
- [PySide6](https://pypi.org/project/PySide6-Essentials/) 6.9+

## Install with Claude Code

Using [Claude Code](https://claude.com/claude-code)? Paste the prompt below into it. It will review the source before running anything, install the dependencies without touching your global Python, run the test suite, start the app and walk you through the controls. The interface is in Chinese, so it also explains the controls in your language.

```text
Please install Desk Todo (https://github.com/zzkws/Desk-Todo) on this Windows PC. It is a small
goal-list card pinned to the top-right corner of the desktop (Python + PySide6). Review it, install
it, verify it and start it, step by step, and tell me what you find along the way.

1. Check the environment
   - Windows 10 or 11, git, and a 64-bit Python 3.10+ (`py -3 --version` or `python --version`).
     If Python is missing or too old, stop and tell me how to install it. Don't install it yourself.

2. Get the code
   - Clone the repo into %USERPROFILE%\Desk-Todo unless I name another folder. The app keeps its data
     in `data\` next to the program, so use a permanent location (not Downloads or a temp folder).

3. Review before running anything
   - Read every file in `desktodo\` (including `qml\Main.qml`), plus `desk_todo.pyw` and `launch.vbs`,
     about 1,900 lines in total.
   - Check that its behaviour matches this list, and report anything outside it before continuing:
     * Network: only a local socket on 127.0.0.1:50573 (single-instance lock and "bring to front").
     * Files: reads and writes only inside `data\`; reads %APPDATA%\DeskTodo\todos.json once if it
       exists (migration from older versions); writes or deletes
       %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\DeskTodo.vbs only when autostart is
       toggled in the app.
     * Win32: a global hotkey (Ctrl+Alt+T, falling back to Ctrl+Alt+Y / J), making the desktop
       (Progman) the window's owner so "Show desktop" doesn't hide it, bringing the window forward.
     * Processes: it relaunches itself if Explorer restarts; it opens the data folder in Explorer
       when the user asks.

4. Install dependencies without touching my global Python
   - Run `pip install -r requirements.txt --target _vendor` with the Python from step 1.
     `desk_todo.pyw` loads `_vendor\` automatically.

5. Run the tests
   - Create a throwaway venv: `python -m venv .venv`, `.venv\Scripts\pip install -r requirements-dev.txt`,
     then `.venv\Scripts\python -m pytest -q`. The tests run headless and never touch real data, the
     mouse or the keyboard. All of them should pass; if any fail, show me the output and stop.
     You may delete `.venv` afterwards.

6. Start it
   - Run `launch.vbs` with `wscript`. If you are running inside a packaged app (for example the Claude
     desktop app), start it from outside the app's container instead, otherwise later settings such as
     autostart are written to a redirected copy of %APPDATA% and silently don't work:
     Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = 'wscript.exe "<install folder>\launch.vbs"' }
   - Verify: a pythonw.exe process is running desk_todo.pyw, `data\todos.json` exists and
     `data\desk_todo.log` is empty. Don't move my mouse or press keys to test it; ask me to look at
     the top-right corner of my screen instead.

7. Hand over
   - The interface is in Chinese. Explain the controls in my language: add with Ctrl+Alt+T or the input
     box; click the circle to complete; hover a goal for archive (box icon) and delete (bin icon);
     double-click to edit; drag to reorder; "⋯" for settings (开机自动启动 = start with Windows,
     退出 = quit).
   - Ask whether I want it to start with Windows. If so, tell me to switch it on from the "⋯" menu;
     don't create the startup entry yourself.
   - Tell me how to uninstall: turn off autostart, quit from the "⋯" menu, then delete the folder.

Don't change the project's code, and don't enable autostart or install anything globally without
asking me first.
```

## Install manually

```powershell
git clone https://github.com/zzkws/Desk-Todo.git
cd Desk-Todo
pip install -r requirements.txt
```

Then double-click **`launch.vbs`** (no console window), or run `pythonw desk_todo.pyw`.

<details>
<summary>Self-contained install (keep PySide6 out of your global Python)</summary>

```powershell
pip install -r requirements.txt --target _vendor
```

`desk_todo.pyw` loads `_vendor/` automatically when it exists.
</details>

Launching it again while it is running just brings the existing card forward — there is only ever one instance.

## Usage

| To | Do |
| --- | --- |
| Add a goal | <kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>T</kbd> (or click the input), type, <kbd>Enter</kbd>. Keep typing to add more. |
| Complete / reopen | Click the circle |
| Archive (not now) | Hover, click the box icon |
| Restore from archive | *Archive* tab → hover → arrow icon |
| Delete (never) | Hover, click the bin |
| Edit | Double-click the text; <kbd>Enter</kbd> saves, <kbd>Esc</kbd> cancels |
| Reorder | Press and drag the text |
| Resize | Drag the bottom-left corner |
| Collapse to a title bar | Double-click the title |
| Settings | <kbd>⋯</kbd> — show done, flush to corner, start with Windows, open data folder, quit |

## Data

Everything lives in `data/` next to the program:

```
data/
├─ todos.json           # your goals and UI state
├─ backups/             # one copy per day, last 30 kept
└─ desk_todo.log        # Qt/QML messages, useful when something looks wrong
```

Set `DESKTODO_DATA_DIR` to keep it somewhere else.

> **Why not `%APPDATA%`?** Processes started from MSIX-packaged apps get a private, redirected view of `%APPDATA%`. Started from such an app, the card would read and write a different file than when it is started at login — and your list would silently fork. A folder next to the program avoids that.

## Development

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\ruff check .
.venv\Scripts\python -m pytest
```

Tests run headless (`QT_QPA_PLATFORM=offscreen`) and never touch your real data, mouse or keyboard. They cover storage and migration, every backend operation, a clean QML load, drag-to-reorder and focus handling.

```
desktodo/
├─ app.py        # entry point: single instance, wiring, restart after Explorer crashes
├─ backend.py    # QObject exposed to QML: three list models + every user action
├─ models.py     # QAbstractListModel for one section
├─ storage.py    # JSON load/save, migration, backups (no Qt)
├─ desk.py       # window placement, hotkey summon, click-outside-to-blur
├─ system.py     # single-instance lock, global hotkey, autostart
├─ winapi.py     # the few Win32 calls we need (ctypes)
└─ qml/Main.qml  # the whole UI
```

`tools/make_screenshots.py` regenerates `docs/screenshot.png` from sample data.

## License

[MIT](LICENSE)
