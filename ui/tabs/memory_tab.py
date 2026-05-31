import math
import random
import time

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ui.colors import C, qcol
from memory.local_vectordb import get_all_memories

CATEGORY_COLORS: dict[str, str] = {
    "identity":      "#00d4ff",
    "preferences":   "#00ff88",
    "projects":      "#ff6b00",
    "relationships": "#ff3366",
    "wishes":        "#cc88ff",
    "notes":         "#ffcc00",
    "Learned":       "#aa44ff",
}

NODE_RADIUS = 9
REPULSION = 4800.0
ATTRACTION = 0.012
DAMPING = 0.82
TICK_MS = 30


class _Node:
    def __init__(self, memory: dict, x: float, y: float):
        self.memory_id = memory["id"]
        self.key = memory["key"]
        self.category = memory["category"]
        self.access_count = memory["access_count"]
        self.x = x
        self.y = y
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)
        self.color = CATEGORY_COLORS.get(memory["category"], C.TEXT_MED)


class MemoryGraphCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C.BG};")
        self._nodes: list[_Node] = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(TICK_MS)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.reload)
        self._refresh_timer.start(5000)
        self.reload()

    def reload(self):
        memories = get_all_memories()
        existing_ids = {n.memory_id for n in self._nodes}
        new_ids = {m["id"] for m in memories}

        for node in self._nodes:
            for m in memories:
                if m["id"] == node.memory_id:
                    node.access_count = m["access_count"]

        for m in memories:
            if m["id"] not in existing_ids:
                cx, cy = self.width() / 2 or 300, self.height() / 2 or 200
                x = cx + random.uniform(-120, 120)
                y = cy + random.uniform(-80, 80)
                self._nodes.append(_Node(m, x, y))

        self._nodes = [n for n in self._nodes if n.memory_id in new_ids]

    def _tick(self):
        nodes = self._nodes
        count = len(nodes)
        if count == 0:
            return

        W, H = max(self.width(), 100), max(self.height(), 100)

        for i in range(count):
            fx, fy = 0.0, 0.0
            a = nodes[i]
            for j in range(count):
                if i == j:
                    continue
                b = nodes[j]
                dx, dy = a.x - b.x, a.y - b.y
                dist = math.sqrt(dx * dx + dy * dy) + 0.01
                force = REPULSION / (dist * dist)
                fx += (dx / dist) * force
                fy += (dy / dist) * force

            same_cat = [n for n in nodes if n.category == a.category and n is not a]
            for b in same_cat:
                dx, dy = b.x - a.x, b.y - a.y
                dist = math.sqrt(dx * dx + dy * dy) + 0.01
                fx += dx * ATTRACTION * dist
                fy += dy * ATTRACTION * dist

            a.vx = (a.vx + fx * 0.001) * DAMPING
            a.vy = (a.vy + fy * 0.001) * DAMPING
            a.x = max(NODE_RADIUS + 4, min(W - NODE_RADIUS - 4, a.x + a.vx))
            a.y = max(NODE_RADIUS + 4, min(H - NODE_RADIUS - 4, a.y + a.vy))

        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), qcol(C.BG))

        W, H = self.width(), self.height()
        p.setPen(QPen(qcol(C.PRI_GHO), 1))
        for x in range(0, W, 48):
            for y in range(0, H, 48):
                p.drawPoint(x, y)

        nodes = self._nodes
        same_cat_pairs: list[tuple[_Node, _Node]] = []
        for i, a in enumerate(nodes):
            for b in nodes[i + 1:]:
                if a.category == b.category:
                    same_cat_pairs.append((a, b))

        for a, b in same_cat_pairs:
            max_count = max(a.access_count + b.access_count, 1)
            thickness = 0.8 + min(3.5, max_count * 0.35)
            col = QColor(a.color)
            col.setAlpha(60 + min(130, max_count * 12))
            p.setPen(QPen(col, thickness))
            p.drawLine(QPointF(a.x, a.y), QPointF(b.x, b.y))

        for node in nodes:
            col = QColor(node.color)
            for ring in range(5, 0, -1):
                glow_col = QColor(col)
                glow_col.setAlpha(int(30 * (ring / 5)))
                p.setBrush(QBrush(glow_col))
                p.setPen(Qt.PenStyle.NoPen)
                r = NODE_RADIUS + ring * 2.5
                p.drawEllipse(QPointF(node.x, node.y), r, r)

            p.setBrush(QBrush(col))
            p.setPen(QPen(QColor(node.color).lighter(160), 1))
            p.drawEllipse(QPointF(node.x, node.y), NODE_RADIUS, NODE_RADIUS)

            p.setFont(QFont("Courier New", 6))
            label = node.key if len(node.key) <= 16 else node.key[:13] + "..."
            p.setPen(QPen(qcol(C.TEXT_MED), 1))
            p.drawText(
                QRectF(node.x - 40, node.y + NODE_RADIUS + 2, 80, 14),
                Qt.AlignmentFlag.AlignCenter, label,
            )

        if not nodes:
            p.setFont(QFont("Courier New", 11))
            p.setPen(QPen(qcol(C.TEXT_DIM), 1))
            p.drawText(
                QRectF(0, 0, W, H),
                Qt.AlignmentFlag.AlignCenter,
                "No memories stored yet.\nJARVIS will populate this graph as you interact.",
            )


class MemoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C.BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(44)
        header.setStyleSheet(f"background: {C.DARK}; border-bottom: 1px solid {C.BORDER};")
        from PyQt6.QtWidgets import QHBoxLayout
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 0, 16, 0)

        title = QLabel("◈  MEMORY NETWORK")
        title.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        h_lay.addWidget(title)
        h_lay.addStretch()

        legend_items = [
            ("Identity", "#00d4ff"), ("Preferences", "#00ff88"), ("Projects", "#ff6b00"),
            ("Relationships", "#ff3366"), ("Wishes", "#cc88ff"), ("Notes", "#ffcc00"), ("Learned", "#aa44ff"),
        ]
        for name, color in legend_items:
            dot = QLabel(f"● {name}")
            dot.setFont(QFont("Courier New", 7))
            dot.setStyleSheet(f"color: {color}; background: transparent; margin-left: 8px;")
            h_lay.addWidget(dot)

        layout.addWidget(header)
        self._canvas = MemoryGraphCanvas()
        layout.addWidget(self._canvas, stretch=1)
