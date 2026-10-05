// 桌面目标 —— 界面
// 风格：Claude 的象牙白 / 珊瑚色 + 类苹果的圆角卡片、分段切换、柔和阴影与动效
import QtQuick
import QtQuick.Window
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Effects

Window {
    id: win
    visible: false                       // 由 Python 定位后再显示
    flags: Qt.FramelessWindowHint | Qt.Tool | Qt.NoDropShadowWindowHint
    color: "transparent"
    title: "目标"

    readonly property int sh: backend.shadow
    readonly property bool flush: backend.flush
    readonly property real cardH: backend.collapsed ? header.height : backend.cardHeight
    // 卡片实际显示的高度：折叠 / 展开时平滑过渡
    property real animH: cardH
    Behavior on animH {
        enabled: !resizer.pressed
        NumberAnimation { id: heightAnim; duration: 220; easing.type: Easing.OutCubic }
    }
    // 宽度和位置由 Python 一次性设置（先改尺寸再挪位置会有一帧卡片偏出屏幕）。
    // 高度：动画进行中保持展开高度，结束后再收窗口，否则折叠时卡片会被窗口切掉。
    // 菜单打开期间给它留出空间：折叠时窗口只有标题栏高，菜单会被挤出去裁掉
    property bool menuRoom: false
    readonly property real menuNeed: menuRoom ? 52 + moreMenu.implicitHeight + 16 : 0
    height: Math.max(cardH, heightAnim.running ? backend.cardHeight : 0, menuNeed) + sh + (flush ? 0 : sh)
    // 点到桌面别处（窗口失焦）时关掉菜单；弹出菜单只在本窗口内检测「点到外面」
    onActiveChanged: if (!active) { moreMenu.close(); rowMenu.close() }
    onClosing: backend.quit()             // Alt+F4 等主动关闭，按正常退出处理

    // ---------- 设计令牌 ----------
    QtObject {
        id: c
        readonly property color bg: "#FAF9F5"
        readonly property color fill: "#F0EEE6"
        readonly property color fill2: "#E8E6DC"
        readonly property color ink: "#1F1E1D"
        readonly property color ink2: "#3D3D3A"
        readonly property color muted: "#87867F"
        readonly property color faint: "#B0AEA5"
        readonly property color ring: "#C9C7BD"
        readonly property color line: "#E8E6DC"
        readonly property color coral: "#D97757"
        readonly property color coralDark: "#C6613F"
        readonly property color coralSoft: "#FBEEE8"
        readonly property color toastText: "#F5F4EE"
        readonly property color toastAccent: "#F0A98C"
    }
    readonly property string sans: "Noto Sans SC"
    readonly property string serif: "Noto Serif SC"
    readonly property string icons: "Segoe Fluent Icons"
    readonly property int r: 18

    // ---------- 小组件 ----------
    component IconButton: Rectangle {
        id: ib
        property string glyph
        property bool danger: false
        property int size: 13
        // 行内按钮由所在行按鼠标坐标给出 hot，不信任自己的 HoverHandler：
        // 按钮随行隐藏时收不到「离开」事件，悬停状态会卡住
        property bool external: false
        property bool hot: false
        property bool active: false          // 例如：对应的菜单正打开着
        readonly property bool lit: active || (external ? hot : ibHover.hovered)
        signal clicked()
        width: 28; height: 28; radius: 8
        // 即时切换，不做颜色动画：从 "transparent"（透明黑）过渡会闪过一层暗灰，像阴影
        color: lit ? (danger ? c.coralSoft : c.fill2) : Qt.rgba(1, 1, 1, 0)
        Text {
            anchors.centerIn: parent
            text: ib.glyph
            font.family: win.icons; font.pixelSize: ib.size
            color: ib.lit ? (ib.danger ? c.coralDark : c.ink2) : c.muted
        }
        HoverHandler { id: ibHover; enabled: !ib.external; cursorShape: Qt.PointingHandCursor }
        TapHandler { onTapped: ib.clicked() }
    }

    component AppMenu: Menu {
        id: am
        padding: 6
        background: Rectangle {
            implicitWidth: 188
            radius: 12
            color: "#FFFFFF"
            border.color: Qt.rgba(0, 0, 0, 0.08)
            layer.enabled: true
            layer.effect: MultiEffect {
                shadowEnabled: true; shadowBlur: 0.8; shadowOpacity: 0.16
                shadowVerticalOffset: 4; shadowColor: "#000000"
            }
        }
        property bool hasCheckable: false
        // 比默认更快的出现 / 消失
        enter: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 80 } }
        exit: Transition { NumberAnimation { property: "opacity"; to: 0; duration: 60 } }
    }

    // 菜单项必须显式用这个组件：直接写在 Menu 里的 MenuItem 不走 delegate，会变回默认样式
    component AppMenuItem: MenuItem {
        id: mi
        property bool danger: false
        implicitHeight: visible ? 32 : 0
        leftPadding: 10; rightPadding: 10
        indicator: null
        arrow: null
        contentItem: RowLayout {
            spacing: 8
            Text {
                text: mi.checked ? "\uE73E" : ""
                font.family: win.icons; font.pixelSize: 11
                color: c.coral
                Layout.preferredWidth: 14
                visible: mi.menu !== null && mi.menu.hasCheckable
            }
            Text {
                text: mi.text
                font.family: win.sans; font.pixelSize: 13
                color: !mi.enabled ? c.faint : (mi.danger && mi.highlighted ? c.coralDark : c.ink)
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
        }
        background: Rectangle {
            radius: 7
            color: mi.highlighted && mi.enabled ? (mi.danger ? c.coralSoft : c.fill) : "transparent"
        }
    }

    component MenuSep: MenuSeparator {
        topPadding: 4; bottomPadding: 4
        contentItem: Rectangle { implicitHeight: 1; color: c.line }
    }

    // ---------- 卡片 ----------
    RectangularShadow {
        anchors.fill: card
        radius: win.r
        blur: 26
        offset.y: 6
        color: Qt.rgba(0.12, 0.10, 0.08, 0.16)
    }

    Rectangle {
        id: card
        x: win.sh
        y: win.flush ? 0 : win.sh
        width: backend.cardWidth
        height: win.animH
        color: c.bg
        // 贴角模式：碰到屏幕边的角保持直角，只圆外露的左下角
        topLeftRadius: win.flush ? 0 : win.r
        topRightRadius: win.flush ? 0 : win.r
        bottomRightRadius: win.flush ? 0 : win.r
        bottomLeftRadius: win.r
        border.width: 1
        border.color: Qt.rgba(0, 0, 0, 0.07)
        clip: true

        // 点空白处：输入框失焦
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onPressed: (m) => { card.forceActiveFocus(); if (m.button === Qt.RightButton) win.openMore() }
        }

        // ---------- 标题栏 ----------
        Item {
            id: header
            width: parent.width
            height: 60
            // 双击折叠只认标题区域：「⋯」上连点两下是开 / 关菜单，不能被当成双击折叠
            TapHandler {
                onDoubleTapped: (point) => {
                    if (point.position.x < moreBtn.x - 6) backend.toggleCollapsed()
                }
            }

            Row {
                anchors.left: parent.left; anchors.leftMargin: 20
                anchors.verticalCenter: parent.verticalCenter
                spacing: 9
                Text {
                    text: "目标"
                    font.family: win.serif; font.pixelSize: 22; font.weight: Font.DemiBold
                    color: c.ink
                }
                Rectangle {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.verticalCenterOffset: 1
                    visible: backend.active.count > 0
                    height: 20; radius: 10
                    width: Math.max(20, cnt.implicitWidth + 12)
                    color: c.coralSoft
                    Text {
                        id: cnt
                        anchors.centerIn: parent
                        text: backend.active.count
                        font.family: win.sans; font.pixelSize: 12; font.weight: Font.DemiBold
                        color: c.coralDark
                    }
                }
            }
            IconButton {
                id: moreBtn
                anchors.right: parent.right; anchors.rightMargin: 14
                anchors.verticalCenter: parent.verticalCenter
                glyph: ""
                active: moreMenu.visible
                onClicked: win.toggleMore()
            }
        }

        // ---------- 主体 ----------
        ColumnLayout {
            id: content
            anchors.top: header.bottom
            anchors.left: parent.left; anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: 14; anchors.rightMargin: 14; anchors.bottomMargin: 10
            spacing: 10
            visible: opacity > 0
            opacity: backend.collapsed ? 0 : 1
            Behavior on opacity { NumberAnimation { duration: 150 } }

            // 分段切换：进行中 / 存档
            Rectangle {
                id: seg
                Layout.fillWidth: true
                height: 32; radius: 9
                color: c.fill
                Rectangle {
                    id: pill
                    y: 2; height: parent.height - 4
                    width: (parent.width - 4) / 2
                    x: backend.tab === "active" ? 2 : 2 + width
                    radius: 7
                    color: "#FFFFFF"
                    Behavior on x { NumberAnimation { duration: 240; easing.type: Easing.OutCubic } }
                    layer.enabled: true
                    layer.effect: MultiEffect {
                        shadowEnabled: true; shadowBlur: 0.3; shadowOpacity: 0.14
                        shadowVerticalOffset: 1; shadowColor: "#000000"
                    }
                }
                Row {
                    anchors.fill: parent
                    Repeater {
                        model: [
                            { key: "active", label: "进行中", n: backend.active.count },
                            { key: "archived", label: "存档", n: backend.archived.count }
                        ]
                        delegate: Item {
                            required property var modelData
                            width: seg.width / 2; height: seg.height
                            readonly property bool on: backend.tab === modelData.key
                            Row {
                                anchors.centerIn: parent
                                spacing: 5
                                Text {
                                    text: modelData.label
                                    font.family: win.sans; font.pixelSize: 13
                                    font.weight: parent.parent.on ? Font.DemiBold : Font.Normal
                                    color: parent.parent.on ? c.ink : c.muted
                                }
                                Text {
                                    text: modelData.n
                                    visible: modelData.n > 0
                                    font.family: win.sans; font.pixelSize: 12
                                    color: c.faint
                                }
                            }
                            TapHandler { onTapped: backend.setTab(modelData.key) }
                            HoverHandler { cursorShape: Qt.PointingHandCursor }
                        }
                    }
                }
            }

            // 输入框
            Rectangle {
                id: inputBox
                Layout.fillWidth: true
                visible: backend.tab === "active"
                height: 42; radius: 12
                color: "#FFFFFF"
                border.width: 1
                // 聚焦要干脆：进入时边框立即变色、光环 90ms 快速弹出；离开时稍慢淡出，不生硬
                border.color: input.activeFocus ? c.coral : c.line
                Behavior on border.color {
                    ColorAnimation { duration: input.activeFocus ? 0 : 140; easing.type: Easing.OutQuad }
                }
                Rectangle {                      // 聚焦光环：从边框处向外弹开
                    id: ring
                    readonly property bool on: input.activeFocus
                    anchors.fill: parent
                    anchors.margins: on ? -3 : -1
                    radius: 12 - anchors.margins; color: "transparent"
                    border.width: 3; border.color: Qt.rgba(0.85, 0.47, 0.34, 0.18)
                    opacity: on ? 1 : 0
                    Behavior on opacity { NumberAnimation { duration: ring.on ? 90 : 140; easing.type: Easing.OutCubic } }
                    Behavior on anchors.margins { NumberAnimation { duration: 90; easing.type: Easing.OutCubic } }
                }
                MouseArea {                  // 点「+」或框内空白也能开始输入
                    anchors.fill: parent
                    cursorShape: Qt.IBeamCursor
                    onPressed: input.forceActiveFocus()
                }
                Text {
                    id: plus
                    anchors.left: parent.left; anchors.leftMargin: 14
                    anchors.verticalCenter: parent.verticalCenter
                    text: ""
                    font.family: win.icons; font.pixelSize: 13
                    color: c.coral
                }
                TextField {
                    id: input
                    objectName: "input"
                    anchors.left: plus.right; anchors.leftMargin: 8
                    anchors.right: keycap.visible ? keycap.left : parent.right
                    anchors.rightMargin: 8
                    anchors.verticalCenter: parent.verticalCenter
                    background: null
                    padding: 0
                    placeholderText: "添加目标"
                    placeholderTextColor: c.faint
                    font.family: win.sans; font.pixelSize: 14
                    color: c.ink
                    selectByMouse: true
                    selectionColor: "#F3C9B8"; selectedTextColor: c.ink
                    onAccepted: {
                        if (text.trim().length) { backend.add(text); text = "" }
                    }
                    Keys.onEscapePressed: { text = ""; card.forceActiveFocus() }
                }
                Rectangle {
                    id: keycap
                    visible: !input.activeFocus && input.text === "" && backend.hotkey !== ""
                    anchors.right: parent.right; anchors.rightMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    height: 20; radius: 5
                    width: kc.implicitWidth + 12
                    color: c.fill
                    Text {
                        id: kc
                        anchors.centerIn: parent
                        text: backend.hotkey
                        font.family: win.sans; font.pixelSize: 11
                        color: c.muted
                    }
                }
            }

            // 列表区
            Flickable {
                id: scroller
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentHeight: backend.tab === "active" ? activePage.height : archivePage.height
                boundsBehavior: Flickable.StopAtBounds
                interactive: !dragging
                property bool dragging: false
                ScrollBar.vertical: ScrollBar {
                    id: vbar
                    width: 6
                    policy: ScrollBar.AsNeeded
                    background: null
                    contentItem: Rectangle {          // 只在滚动时淡入，平时隐藏
                        implicitWidth: 4
                        radius: 2; color: c.faint
                        opacity: vbar.active ? 0.6 : 0
                        Behavior on opacity { NumberAnimation { duration: 250 } }
                    }
                }

                // 进行中 + 已完成
                Column {
                    id: activePage
                    width: scroller.width
                    visible: backend.tab === "active"
                    spacing: 0

                    ListView {
                        id: activeList
                        objectName: "activeList"
                        width: parent.width
                        height: contentHeight
                        interactive: false
                        model: backend.active
                        // 同一时刻只有一行算悬停
                        readonly property point hoverPos: activeHover.hovered
                            ? contentItem.mapFromItem(null, activeHover.point.scenePosition.x, activeHover.point.scenePosition.y)
                            : Qt.point(-1, -1)
                        property int hoverIndex: activeHover.hovered ? indexAt(hoverPos.x, hoverPos.y) : -1
                        HoverHandler { id: activeHover; cursorShape: win.rowCursor(activeList) }
                        delegate: GoalRow { kind: "active"; view: activeList }
                        add: Transition {
                            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 220 }
                            NumberAnimation { property: "scale"; from: 0.96; to: 1; duration: 220; easing.type: Easing.OutCubic }
                        }
                        remove: Transition {
                            NumberAnimation { property: "opacity"; to: 0; duration: 160 }
                        }
                        displaced: Transition {
                            NumberAnimation { properties: "y"; duration: 160; easing.type: Easing.OutCubic }
                        }
                        move: Transition {
                            NumberAnimation { properties: "y"; duration: 160; easing.type: Easing.OutCubic }
                        }
                    }

                    Column {                                  // 空状态
                        width: parent.width
                        visible: backend.active.count === 0
                        topPadding: 22; bottomPadding: 14
                        spacing: 4
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: backend.done.count > 0 ? "全部完成了" : "还没有目标"
                            font.family: win.sans; font.pixelSize: 14; font.weight: Font.Medium
                            color: c.ink2
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "在上面写下一个，按 Enter"
                            font.family: win.sans; font.pixelSize: 12
                            color: c.faint
                            visible: backend.done.count === 0
                        }
                    }

                    // 已完成分组
                    Item {
                        width: parent.width
                        height: 38
                        visible: backend.done.count > 0
                        Row {
                            anchors.left: parent.left; anchors.leftMargin: 10
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 6
                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: ""
                                font.family: win.icons; font.pixelSize: 10
                                color: c.muted
                                rotation: backend.showDone ? 90 : 0
                                Behavior on rotation { NumberAnimation { duration: 180 } }
                            }
                            Text {
                                text: "已完成"
                                font.family: win.sans; font.pixelSize: 13; font.weight: Font.Medium
                                color: c.muted
                            }
                            Text {
                                text: backend.done.count
                                font.family: win.sans; font.pixelSize: 13
                                color: c.faint
                            }
                        }
                        TapHandler { onTapped: backend.setShowDone(!backend.showDone) }
                        HoverHandler { cursorShape: Qt.PointingHandCursor }
                        Text {
                            anchors.right: parent.right; anchors.rightMargin: 10
                            anchors.verticalCenter: parent.verticalCenter
                            visible: backend.showDone
                            text: "清空"
                            font.family: win.sans; font.pixelSize: 13
                            color: clearHover.hovered ? c.coralDark : c.coral
                            HoverHandler { id: clearHover; cursorShape: Qt.PointingHandCursor }
                            TapHandler { onTapped: backend.clearDone() }
                        }
                    }

                    ListView {
                        id: doneList
                        width: parent.width
                        height: visible ? contentHeight : 0
                        visible: backend.showDone
                        interactive: false
                        model: backend.done
                        // 同一时刻只有一行算悬停
                        readonly property point hoverPos: doneHover.hovered
                            ? contentItem.mapFromItem(null, doneHover.point.scenePosition.x, doneHover.point.scenePosition.y)
                            : Qt.point(-1, -1)
                        property int hoverIndex: doneHover.hovered ? indexAt(hoverPos.x, hoverPos.y) : -1
                        HoverHandler { id: doneHover; cursorShape: win.rowCursor(doneList) }
                        delegate: GoalRow { kind: "done"; view: doneList }
                        add: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 200 } }
                        displaced: Transition { NumberAnimation { properties: "y"; duration: 160; easing.type: Easing.OutCubic } }
                    }
                    Item { width: 1; height: 8 }
                }

                // 存档
                Column {
                    id: archivePage
                    width: scroller.width
                    visible: backend.tab === "archived"

                    ListView {
                        id: archiveList
                        width: parent.width
                        height: contentHeight
                        interactive: false
                        model: backend.archived
                        // 同一时刻只有一行算悬停
                        readonly property point hoverPos: archiveHover.hovered
                            ? contentItem.mapFromItem(null, archiveHover.point.scenePosition.x, archiveHover.point.scenePosition.y)
                            : Qt.point(-1, -1)
                        property int hoverIndex: archiveHover.hovered ? indexAt(hoverPos.x, hoverPos.y) : -1
                        HoverHandler { id: archiveHover; cursorShape: win.rowCursor(archiveList) }
                        delegate: GoalRow { kind: "archived"; view: archiveList }
                        add: Transition { NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 200 } }
                        remove: Transition { NumberAnimation { property: "opacity"; to: 0; duration: 160 } }
                        displaced: Transition { NumberAnimation { properties: "y"; duration: 160; easing.type: Easing.OutCubic } }
                    }
                    Column {
                        width: parent.width
                        visible: backend.archived.count === 0
                        topPadding: 26; spacing: 6
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: ""
                            font.family: win.icons; font.pixelSize: 22
                            color: c.ring
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "没有存档的目标"
                            font.family: win.sans; font.pixelSize: 14; font.weight: Font.Medium
                            color: c.ink2
                        }
                        Text {
                            width: parent.width - 40
                            anchors.horizontalCenter: parent.horizontalCenter
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.Wrap
                            text: "现阶段不做的目标可以先存档，想做时再恢复"
                            font.family: win.sans; font.pixelSize: 12
                            color: c.faint
                        }
                    }
                }
            }
        }

        // ---------- 撤销提示 ----------
        Rectangle {
            id: toast
            objectName: "toast"
            property bool shown: false
            property string msg: ""
            anchors.horizontalCenter: parent.horizontalCenter
            y: shown ? card.height - height - 14 : card.height + 8
            opacity: shown ? 1 : 0
            width: Math.min(card.width - 28, toastRow.implicitWidth + 32)
            height: 40; radius: 12
            color: c.ink
            visible: !backend.collapsed
            Behavior on y { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
            Behavior on opacity { NumberAnimation { duration: 200 } }
            RowLayout {
                id: toastRow
                anchors.fill: parent
                anchors.leftMargin: 16; anchors.rightMargin: 16
                spacing: 14
                Text {
                    Layout.fillWidth: true
                    text: toast.msg
                    elide: Text.ElideRight
                    font.family: win.sans; font.pixelSize: 13
                    color: c.toastText
                }
                Text {
                    text: "撤销"
                    font.family: win.sans; font.pixelSize: 13; font.weight: Font.DemiBold
                    color: c.toastAccent
                    HoverHandler { cursorShape: Qt.PointingHandCursor }
                    TapHandler { onTapped: { backend.undo(); toast.shown = false } }
                }
            }
            Timer {
                id: toastTimer
                interval: 5000
                onTriggered: { toast.shown = false; backend.expireUndo() }
            }
            Connections {
                target: backend
                function onToast(m) { toast.msg = m; toast.shown = true; toastTimer.restart() }
            }
        }

        // ---------- 左下角缩放 ----------
        MouseArea {
            id: resizer
            width: 18; height: 18
            anchors.left: parent.left; anchors.bottom: parent.bottom
            visible: !backend.collapsed
            cursorShape: Qt.SizeBDiagCursor
            property point p0
            property size s0
            onPressed: (m) => {
                p0 = mapToGlobal(m.x, m.y)
                s0 = Qt.size(backend.cardWidth, backend.cardHeight)
                backend.setBusy(true)
            }
            onPositionChanged: (m) => {
                if (!pressed) return
                const p = mapToGlobal(m.x, m.y)
                backend.setCardSize(s0.width - (p.x - p0.x), s0.height + (p.y - p0.y))
            }
            onReleased: backend.setBusy(false)
        }
    }

    // ---------- 菜单 ----------
    AppMenu {
        id: moreMenu
        objectName: "moreMenu"
        hasCheckable: true
        property real closedAt: 0
        onClosed: { closedAt = Date.now(); win.menuRoom = false }
        AppMenuItem { text: "显示已完成"; checkable: true; checked: backend.showDone; onTriggered: backend.setShowDone(!backend.showDone) }
        AppMenuItem { text: "紧贴屏幕右上角"; checkable: true; checked: backend.flush; onTriggered: backend.setFlush(!backend.flush) }
        AppMenuItem { text: "开机自动启动"; checkable: true; checked: backend.autostart; onTriggered: backend.setAutostart(!backend.autostart) }
        MenuSep {}
        AppMenuItem { text: backend.collapsed ? "展开" : "折叠"; onTriggered: backend.toggleCollapsed() }
        AppMenuItem { text: backend.hotkey ? "呼出快捷键  " + backend.hotkey : "快捷键被占用"; enabled: false }
        AppMenuItem { text: "打开数据文件夹"; onTriggered: backend.openDataDir() }
        MenuSep {}
        AppMenuItem { text: "退出"; danger: true; onTriggered: backend.quit() }
    }

    AppMenu {
        id: rowMenu
        property string gid: ""
        property string kind: ""
        property var row: null
        AppMenuItem {
            text: rowMenu.kind === "done" ? "恢复为进行中" : "完成"
            visible: rowMenu.kind !== "archived"; height: visible ? implicitHeight : 0
            onTriggered: rowMenu.row && rowMenu.row.toggle()
        }
        AppMenuItem { text: "编辑"; onTriggered: rowMenu.row && rowMenu.row.startEdit() }
        AppMenuItem {
            text: "移到最前"
            visible: rowMenu.kind === "active"; height: visible ? implicitHeight : 0
            onTriggered: backend.moveToTop(rowMenu.gid)
        }
        AppMenuItem {
            text: rowMenu.kind === "archived" ? "恢复" : "存档"
            onTriggered: rowMenu.kind === "archived" ? backend.unarchive(rowMenu.gid) : backend.archive(rowMenu.gid)
        }
        MenuSep {}
        AppMenuItem { text: "删除"; danger: true; onTriggered: backend.remove(rowMenu.gid) }
    }

    // ---------- 单行 ----------
    component GoalRow: Item {
        id: row
        required property int index
        required property string gid
        required property string text
        property string kind: "active"          // active | done | archived
        property ListView view
        property bool checking: false            // 勾上后停留一下再移走
        property bool editing: false
        property bool dragging: false
        readonly property bool isDone: kind === "done" || checking
        readonly property bool hovered: view !== null && view.hoverIndex === index && !scroller.dragging
        // 鼠标在本行内的坐标（不在本行时为 -1）
        readonly property real hx: hovered ? view.hoverPos.x - x : -1
        readonly property real hy: hovered ? view.hoverPos.y - y : -1
        function over(b) {
            const p = b.mapToItem(row, 0, 0)
            return hx >= p.x && hx < p.x + b.width && hy >= p.y && hy < p.y + b.height
        }
        readonly property bool overClick: hovered && ((check.visible && over(check))
            || (actions.visible && (over(archBtn) || over(delBtn))))

        width: view ? view.width : 0
        height: Math.max(42, (editing ? editor.implicitHeight + 8 : label.implicitHeight) + 20)
        z: dragging || settleAnim.running ? 10 : 0

        // ---- 拖动排序 ----
        // 被拖的卡片始终贴着鼠标：位移 = 鼠标给出的卡片顶边 − 本行当前（可能在动画中的）位置，
        // 所以即使本行在数据里换了位置、正在播放移动动画，看上去也纹丝不动地跟着手。
        property real dragTop: 0            // 卡片顶边，列表内容坐标
        property real grabDy: 0             // 按下点距本行顶边
        property real settle: 0             // 松手后从当前位置落回 0
        readonly property real dragOffset: dragging ? dragTop - y : settle
        transform: Translate { y: row.dragOffset }
        NumberAnimation {
            id: settleAnim
            target: row; property: "settle"; to: 0
            duration: 160; easing.type: Easing.OutCubic
        }
        // 目标位置：被拖卡片的中线越过某行的中线就换到它另一侧。
        // 各行位置按高度累加出「停放位置」，不读正在动画中的 y —— 否则会来回抖、出现空隙；
        // 交换后邻居让到另一侧，中线也随之远离鼠标，所以不会反复横跳。
        function slotFor(centerY) {
            let acc = 0, slot = 0
            for (let i = 0; i < view.count; i++) {
                if (i === index) continue
                const it = view.itemAtIndex(i)
                if (!it) continue
                const top = acc + (i > index ? height : 0)     // 排在被拖行后面的，停放位置要让出它的高度
                if (centerY > top + it.height / 2) slot++
                acc += it.height
            }
            return slot
        }
        function beginDrag(pY) {
            grabDy = pY - y
            dragTop = y
            dragging = true
            scroller.dragging = true
            backend.setBusy(true)
        }
        function dragTo(pY) {
            const maxTop = Math.max(0, view.contentItem.height - height)
            dragTop = Math.max(0, Math.min(maxTop, pY - grabDy))
            const to = slotFor(dragTop + height / 2)
            if (to !== index) backend.moveActive(index, to)
        }
        function endDrag() {
            settle = dragTop - y
            dragging = false
            settleAnim.restart()
            scroller.dragging = false
            backend.setBusy(false)
        }

        function toggle() {
            if (kind === "active") { checking = true; completeTimer.start() }
            else if (kind === "done") backend.uncomplete(gid)
        }
        function startEdit() {
            editing = true
            editor.text = row.text
            editor.forceActiveFocus()
            editor.selectAll()
        }
        function finishEdit(save) {
            if (!editing) return
            editing = false
            if (save) backend.rename(gid, editor.text)
        }
        Timer { id: completeTimer; interval: 250; onTriggered: backend.complete(row.gid) }

        Rectangle {
            anchors.fill: parent
            anchors.topMargin: 1; anchors.bottomMargin: 1
            radius: 10
            color: row.dragging ? "#FFFFFF" : (row.hovered || row.editing ? c.fill : "transparent")
            border.width: row.dragging ? 1 : 0
            border.color: c.line
            layer.enabled: row.dragging
            layer.effect: MultiEffect {
                shadowEnabled: true; shadowBlur: 0.6; shadowOpacity: 0.18
                shadowVerticalOffset: 3; shadowColor: "#000000"
            }
        }

        // 勾选圆圈（存档里换成盒子图标）
        Item {
            id: check
            x: 10; y: 11
            width: 20; height: 20
            visible: row.kind !== "archived"
            Rectangle {
                anchors.fill: parent
                radius: width / 2
                color: row.isDone ? c.coral : Qt.rgba(0.85, 0.47, 0.34, 0)   // 同色透明，避免过渡时发暗
                border.width: row.isDone ? 0 : 1.5
                border.color: row.over(check) ? c.coral : c.ring
                scale: checkTap.pressed ? 0.88 : 1
                Behavior on color { ColorAnimation { duration: 160 } }
                Behavior on scale { NumberAnimation { duration: 120 } }
            }
            Text {
                anchors.centerIn: parent
                anchors.verticalCenterOffset: 1
                text: ""
                font.family: win.icons; font.pixelSize: 11; font.bold: true
                color: "#FFFFFF"
                opacity: row.isDone ? 1 : 0
                scale: row.isDone ? 1 : 0.3
                Behavior on scale { NumberAnimation { duration: 260; easing.type: Easing.OutBack } }
                Behavior on opacity { NumberAnimation { duration: 140 } }
            }
            TapHandler { id: checkTap; onTapped: row.toggle() }
        }
        Text {
            x: 12; y: 12
            visible: row.kind === "archived"
            text: ""
            font.family: win.icons; font.pixelSize: 15
            color: c.faint
        }

        Text {
            id: label
            x: 40; y: 10
            width: row.width - x - 70
            visible: !row.editing
            text: row.text
            wrapMode: Text.Wrap
            font.family: win.sans; font.pixelSize: 14
            font.strikeout: row.isDone
            lineHeight: 1.12
            color: row.isDone ? c.muted : (row.kind === "archived" ? c.ink2 : c.ink)
            Behavior on color { ColorAnimation { duration: 160 } }
        }
        TextField {
            id: editor
            x: 36; y: 6
            width: row.width - x - 66
            visible: row.editing
            padding: 4; leftPadding: 4
            font.family: win.sans; font.pixelSize: 14
            color: c.ink
            selectByMouse: true
            selectionColor: "#F3C9B8"; selectedTextColor: c.ink
            background: Rectangle { radius: 7; color: "#FFFFFF"; border.width: 1; border.color: c.coral }
            onAccepted: row.finishEdit(true)
            Keys.onEscapePressed: row.finishEdit(false)
            onActiveFocusChanged: if (!activeFocus) row.finishEdit(true)
        }

        // 文字区：双击编辑、按住拖动排序、右键菜单
        MouseArea {
            x: label.x; y: 0
            width: label.width; height: row.height
            visible: !row.editing
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            property real y0: 0
            onPressed: (m) => {
                card.forceActiveFocus()
                y0 = m.y
                if (m.button === Qt.RightButton) {
                    rowMenu.gid = row.gid; rowMenu.kind = row.kind; rowMenu.row = row
                    rowMenu.popup()
                }
            }
            onPositionChanged: (m) => {
                if (!pressed || row.kind !== "active") return
                const p = mapToItem(row.view.contentItem, m.x, m.y)
                if (!row.dragging) {
                    if (Math.abs(m.y - y0) < 6) return
                    // 按下点（未移动前）相对本行的位置
                    row.beginDrag(p.y - (m.y - y0))
                }
                row.dragTo(p.y)
            }
            onReleased: if (row.dragging) row.endDrag()
            onCanceled: if (row.dragging) row.endDrag()
            onDoubleClicked: (m) => { if (m.button === Qt.LeftButton) row.startEdit() }
        }

        // 悬停操作
        Row {
            id: actions
            anchors.right: parent.right; anchors.rightMargin: 6
            y: 7
            spacing: 2
            opacity: row.hovered && !row.editing && !row.dragging ? 1 : 0
            visible: opacity > 0
            IconButton {
                id: archBtn
                external: true; hot: row.over(archBtn)
                glyph: row.kind === "archived" ? "" : ""
                onClicked: row.kind === "archived" ? backend.unarchive(row.gid) : backend.archive(row.gid)
            }
            IconButton {
                id: delBtn
                external: true; hot: row.over(delBtn)
                glyph: ""; danger: true
                onClicked: backend.remove(row.gid)
            }
        }
    }

    // 行内光标：拖动中是抓手，在圆圈 / 按钮上是手形，其余是箭头
    function rowCursor(view) {
        const it = view.hoverIndex >= 0 ? view.itemAtIndex(view.hoverIndex) : null
        if (!it) return Qt.ArrowCursor
        if (it.dragging) return Qt.ClosedHandCursor
        return it.overClick ? Qt.PointingHandCursor : Qt.ArrowCursor
    }

    // 点到输入框以外：失焦（编辑中的条目会按「失焦即保存」提交）
    function dropFocus() { card.forceActiveFocus() }

    // 「⋯」菜单：点一下开，再点一下关
    function toggleMore() {
        if (moreMenu.visible) { moreMenu.close(); return }
        // 菜单开着时按下「⋯」，按下那一刻菜单已因「点到外面」自己关了；
        // 松开时这次点击的意图是「关」，不能再把它打开
        if (Date.now() - moreMenu.closedAt < 350) return
        openMore()
    }
    function openMore() {
        if (moreMenu.visible) return
        menuRoom = true
        // 展开时窗口本来就够高，立即弹出；只有折叠时要等窗口撑高一帧，否则会按旧尺寸被挤上去
        if (cardH >= menuNeed) popMore()
        else menuOpenTimer.restart()
    }
    function popMore() {
        moreMenu.popup(moreBtn, moreBtn.width - moreMenu.implicitWidth, moreBtn.height + 6)
    }
    Timer {
        id: menuOpenTimer
        interval: 16
        onTriggered: win.popMore()
    }

    // ---------- 键盘 ----------
    Shortcut { sequence: "Ctrl+Z"; enabled: backend.canUndo; onActivated: { backend.undo(); toast.shown = false } }
    Connections {
        target: backend
        function onSummoned() {
            input.forceActiveFocus()
        }
    }
}
