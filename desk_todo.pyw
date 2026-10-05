"""Desk Todo 启动入口（用 pythonw 运行，不弹控制台）。

依赖优先从本目录的 ``_vendor/`` 加载（``pip install -r requirements.txt --target _vendor``），
没有的话使用当前 Python 环境里安装的 PySide6。
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(HERE, "_vendor")
if os.path.isdir(VENDOR):
    sys.path.insert(0, VENDOR)
sys.path.insert(0, HERE)

from desktodo.app import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
