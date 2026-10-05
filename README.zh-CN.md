<div align="center">

# Desk Todo

**住在 Windows 桌面右上角的一张安静的目标清单。**

简体中文 · [English](README.md)

[![CI](https://github.com/zzkws/Desk-Todo/actions/workflows/ci.yml/badge.svg)](https://github.com/zzkws/Desk-Todo/actions/workflows/ci.yml)
![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078D4)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)

<img src="docs/screenshot.png" alt="Desk Todo —— 进行中与存档" width="760">

</div>

Desk Todo 是一张一直在那儿的小卡片，用来记下你在电脑上真正想完成的事。它紧贴屏幕右上角，「显示桌面」也不会把它收起，层级和普通窗口一样，不打扰你。**现阶段不做**的目标放进**存档**，不再挤在清单里；**真正不做**的再删除。

外观借鉴了 Claude 的暖色调——象牙白的底、珊瑚色的强调——配上类苹果的圆角卡片、分段切换和干脆利落的动效。

## 特性

- **目标，而不是待办**：三种状态——进行中、已完成（划掉，可折叠）、存档（暂时不做）。删除留给「真正不做」。
- **钉在右上角**：紧贴屏幕上边和右边（也可以切换成离边 14px 的悬浮卡片），分辨率变化后自动归位，不能被拖走。
- **「显示桌面」不收起**：<kbd>Win</kbd>+<kbd>D</kbd>、触摸板三指下滑会收起其他窗口，它留在桌面上。
- **普通窗口层级**：点它就到前面，点别的窗口它就被盖住，不和系统规则较劲。
- **全局快捷键**：<kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>T</kbd> 把它带到前面，光标直接在输入框里（被占用时自动顺延为 <kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>Y</kbd> / <kbd>J</kbd>）。
- **可撤销**：存档、删除、清空已完成后，底部出现「撤销」，5 秒内有效，也可以按 <kbd>Ctrl</kbd>+<kbd>Z</kbd>。
- **拖动排序**：被拖的卡片紧贴鼠标，其他条目顺滑让位。
- **数据在你手里**：程序目录下的一个普通 JSON 文件；原子写入，每天自动备份（保留 30 天）；文件损坏时改名留档，绝不静默覆盖。
- **开机自启**：<kbd>⋯</kbd> 菜单里一键开关。

## 环境要求

- Windows 10 / 11
- Python 3.10+（64 位）
- [PySide6](https://pypi.org/project/PySide6-Essentials/) 6.9+

## 用 Claude Code 安装

如果你在用 [Claude Code](https://claude.com/claude-code)，点代码块右上角复制下面这段 prompt，原样粘贴给它即可。它会先审查源码再运行任何东西，把依赖装在项目目录里（不动你的全局 Python），跑一遍测试，然后启动程序并给你讲解怎么用。

```text
请帮我在这台 Windows 电脑上安装 Desk Todo（https://github.com/zzkws/Desk-Todo）。它是一个贴在桌面
右上角的目标清单小卡片（Python + PySide6）。请按下面的步骤审查、安装、验证并启动它，过程中把你的
发现告诉我。

1. 检查环境
   - Windows 10 或 11、git、64 位 Python 3.10 及以上（`py -3 --version` 或 `python --version`）。
     如果没有 Python 或版本太旧，停下来告诉我怎么安装，不要自己装。

2. 获取代码
   - 克隆到 %USERPROFILE%\Desk-Todo，除非我指定了别的目录。程序把数据存在自身目录下的 `data\` 里，
     所以要放在固定的位置（不要放在下载目录或临时目录）。

3. 运行任何东西之前，先审查代码
   - 读完 `desktodo\` 下的所有文件（包括 `qml\Main.qml`），以及 `desk_todo.pyw` 和 `launch.vbs`，
     总共约 1,900 行。
   - 核对它的行为是否和下面的清单一致；清单之外的任何行为，先报告给我再继续：
     * 网络：只有 127.0.0.1:50573 上的本地 socket（单实例锁和「带到前面」）。
     * 文件：只在 `data\` 里读写；如果存在 %APPDATA%\DeskTodo\todos.json，会读取一次（从旧版本迁移）；
       只有在程序里切换开机自启时，才会写入或删除
       %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\DeskTodo.vbs。
     * Win32：一个全局快捷键（Ctrl+Alt+T，被占用时依次换成 Ctrl+Alt+Y / J）；把窗口的所有者设为
       桌面（Progman），让「显示桌面」不会收起它；把窗口带到前面。
     * 进程：资源管理器重启后会重新启动自己；用户要求时在资源管理器里打开数据文件夹。

4. 安装依赖，不要动我的全局 Python
   - 用第 1 步的 Python 运行 `pip install -r requirements.txt --target _vendor`。
     `desk_todo.pyw` 会自动从 `_vendor\` 加载依赖。

5. 运行测试
   - 建一个临时 venv：`python -m venv .venv`，`.venv\Scripts\pip install -r requirements-dev.txt`，
     然后 `.venv\Scripts\python -m pytest -q`。测试在无界面模式下运行，不会碰真实数据、鼠标和键盘。
     应该全部通过；如果有失败，把输出给我看，然后停下。测试完可以删掉 `.venv`。

6. 启动
   - 用 `wscript` 运行 `launch.vbs`。如果你运行在打包应用里（比如 Claude 桌面版），要从应用容器外面
     启动，否则之后开机自启等设置会写进一份被重定向的 %APPDATA% 副本，悄无声息地失效：
     Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = 'wscript.exe "<安装目录>\launch.vbs"' }
   - 验证：有一个 pythonw.exe 进程在运行 desk_todo.pyw，`data\todos.json` 已生成，
     `data\desk_todo.log` 是空的。不要移动我的鼠标或按键来测试，请我自己看一眼屏幕右上角。

7. 交接
   - 给我讲解怎么用：按 Ctrl+Alt+T 或点输入框添加；点圆圈完成；鼠标悬停在目标上，会出现存档
     （盒子图标）和删除（垃圾桶图标）；双击修改；拖动排序；「⋯」是设置（开机自动启动、退出）。
   - 问我要不要开机自启。要的话，告诉我在「⋯」菜单里打开，不要自己创建启动项。
   - 告诉我怎么卸载：先关掉开机自启，在「⋯」菜单里退出，再删除整个文件夹。

不要修改项目代码；开机自启和任何全局安装，都要先问过我。
```

## 手动安装

```powershell
git clone https://github.com/zzkws/Desk-Todo.git
cd Desk-Todo
pip install -r requirements.txt
```

然后双击 **`launch.vbs`**（不弹控制台），或运行 `pythonw desk_todo.pyw`。

<details>
<summary>自包含安装（不把 PySide6 装进全局 Python）</summary>

```powershell
pip install -r requirements.txt --target _vendor
```

`_vendor/` 存在时，`desk_todo.pyw` 会自动从这里加载依赖。
</details>

已经在运行时再启动一次，只会把现有的卡片带到前面——始终只有一个实例。

## 使用

| 想做的事 | 怎么做 |
| --- | --- |
| 添加目标 | <kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>T</kbd>（或点输入框），输入，按 <kbd>Enter</kbd>；可以连续添加 |
| 完成 / 恢复 | 点左边的圆圈 |
| 存档（暂时不做） | 鼠标悬停，点盒子图标 |
| 从存档恢复 | 切到「存档」→ 悬停 → 点返回箭头 |
| 删除（真正不做） | 鼠标悬停，点垃圾桶 |
| 修改 | 双击文字；<kbd>Enter</kbd> 保存，<kbd>Esc</kbd> 取消 |
| 排序 | 按住文字上下拖 |
| 改大小 | 拖卡片左下角 |
| 折叠成一条 | 双击标题 |
| 设置 | <kbd>⋯</kbd>：显示已完成、紧贴屏幕右上角、开机自启、打开数据文件夹、退出 |

## 数据

都在程序目录下的 `data/` 里：

```
data/
├─ todos.json           # 目标和界面状态
├─ backups/             # 每天一份，保留最近 30 份
└─ desk_todo.log        # Qt/QML 消息，界面出问题时看这里
```

想放到别处，设置环境变量 `DESKTODO_DATA_DIR` 即可。

> **为什么不放 `%APPDATA%`？** 从 MSIX 打包应用里启动的进程，看到的 `%APPDATA%` 是一份被重定向的私有副本。如果卡片是从这类应用里启动的，它读写的文件和开机自启时不是同一个，你的清单会悄悄分叉成两份。放在程序旁边的文件夹就没有这个问题。

## 开发

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\ruff check .
.venv\Scripts\python -m pytest
```

测试在无界面模式下运行（`QT_QPA_PLATFORM=offscreen`），不会碰你的真实数据、鼠标和键盘。覆盖存储与迁移、后端的每个操作、QML 干净加载、拖动排序和焦点处理。

```
desktodo/
├─ app.py        # 入口：单实例、组装、资源管理器重启后自动拉起
├─ backend.py    # 暴露给 QML 的 QObject：三个列表模型 + 所有用户操作
├─ models.py     # 单个分区的 QAbstractListModel
├─ storage.py    # JSON 读写、迁移、备份（不依赖 Qt）
├─ desk.py       # 窗口定位、快捷键呼出、点框外失焦
├─ system.py     # 单实例锁、全局快捷键、开机自启
├─ winapi.py     # 用到的少量 Win32 调用（ctypes）
└─ qml/Main.qml  # 全部界面
```

`tools/make_screenshots.py` 用示例数据重新生成 `docs/screenshot.png`。

## 许可证

[MIT](LICENSE)
