# Changelog

## 3.1.0 — 2026-10-05

First public release.

- Split the single script into the `desktodo` package (storage / models / backend / desk / system / winapi).
- Pytest suite (storage & migration, backend operations, QML load, drag-to-reorder, focus) running headless; GitHub Actions CI on Windows.
- Launcher `launch.vbs` with no hard-coded paths.
- Drag-to-reorder: the dragged card follows the cursor exactly; target slot is computed from settled positions, so rows no longer jitter or leave gaps.
- Crisper input focus animation; menu fade fixed.

## 3.0.0

- Rewritten in PySide6 + Qt Quick: rounded cards, segmented control, undo toasts, animations.
- Goals with three states (in progress / done / archived); no timestamps.
- Data moved from `%APPDATA%` to `data/` next to the program; daily backups; corrupt files are set aside.

## 2.x and earlier

- Tkinter prototypes.
