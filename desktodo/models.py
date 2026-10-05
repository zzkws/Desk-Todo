"""供 QML ListView 使用的列表模型。"""

from PySide6.QtCore import Property, QAbstractListModel, QByteArray, QModelIndex, Qt, Signal


class GoalList(QAbstractListModel):
    """一个分区（进行中 / 已完成 / 存档）的有序目标列表。"""

    countChanged = Signal()
    IdRole = Qt.UserRole + 1
    TextRole = Qt.UserRole + 2

    def __init__(self, goals=None, parent=None):
        super().__init__(parent)
        self._g = list(goals or [])

    # ----- QAbstractListModel -----
    def rowCount(self, parent=None):
        return 0 if parent is not None and parent.isValid() else len(self._g)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._g):
            return None
        g = self._g[index.row()]
        if role == self.IdRole:
            return g["id"]
        if role in (self.TextRole, Qt.DisplayRole):
            return g["text"]
        return None

    def roleNames(self):
        return {self.IdRole: QByteArray(b"gid"), self.TextRole: QByteArray(b"text")}

    def _count(self):
        return len(self._g)

    count = Property(int, _count, notify=countChanged)

    # ----- 操作 -----
    def goals(self):
        return list(self._g)

    def row_of(self, gid):
        return next((i for i, g in enumerate(self._g) if g["id"] == gid), -1)

    def insert(self, row, goal):
        row = max(0, min(row, len(self._g)))
        self.beginInsertRows(QModelIndex(), row, row)
        self._g.insert(row, goal)
        self.endInsertRows()
        self.countChanged.emit()

    def take(self, row):
        self.beginRemoveRows(QModelIndex(), row, row)
        g = self._g.pop(row)
        self.endRemoveRows()
        self.countChanged.emit()
        return g

    def move(self, src, dst):
        """把第 src 行移到第 dst 行；无效或原地移动返回 False。"""
        n = len(self._g)
        if src == dst or not (0 <= src < n and 0 <= dst < n):
            return False
        if not self.beginMoveRows(QModelIndex(), src, src, QModelIndex(),
                                  dst + 1 if dst > src else dst):
            return False
        self._g.insert(dst, self._g.pop(src))
        self.endMoveRows()
        return True

    def set_text(self, row, text):
        self._g[row]["text"] = text
        idx = self.index(row)
        self.dataChanged.emit(idx, idx, [self.TextRole])

    def reset(self, goals):
        self.beginResetModel()
        self._g = list(goals)
        self.endResetModel()
        self.countChanged.emit()
