import os
from pathlib import Path

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPen, QBrush,
)
from PyQt6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QSizePolicy,
    QTextEdit, QVBoxLayout, QWidget,
)

from ui.colors import C, qcol

PROJECTS_ROOT = Path(__file__).resolve().parent.parent.parent / "projects"

SYNTAX_RULES: dict[str, list[tuple[str, str]]] = {
    ".py": [
        ("keyword", r"\b(def|class|import|from|return|if|elif|else|for|while|try|except|with|as|pass|break|continue|and|or|not|in|is|lambda|yield|global|nonlocal|raise|del|assert|True|False|None)\b"),
        ("builtin", r"\b(print|len|range|type|str|int|float|list|dict|set|tuple|bool|open|input|super|self)\b"),
        ("string_d", r'"[^"\\]*(?:\\.[^"\\]*)*"'),
        ("string_s", r"'[^'\\]*(?:\\.[^'\\]*)*'"),
        ("comment", r"#.*"),
        ("number", r"\b\d+\.?\d*\b"),
    ],
    ".js": [
        ("keyword", r"\b(function|const|let|var|return|if|else|for|while|class|import|export|default|new|this|typeof|instanceof|try|catch|finally|async|await|of|in)\b"),
        ("string_d", r'"[^"\\]*(?:\\.[^"\\]*)*"'),
        ("string_s", r"'[^'\\]*(?:\\.[^'\\]*)*'"),
        ("comment", r"//.*"),
        ("number", r"\b\d+\.?\d*\b"),
    ],
    ".json": [
        ("string_d", r'"[^"\\]*(?:\\.[^"\\]*)*"'),
        ("number", r"\b\d+\.?\d*\b"),
        ("keyword", r"\b(true|false|null)\b"),
    ],
    ".html": [
        ("tag", r"</?[a-zA-Z][^>]*>"),
        ("string_d", r'"[^"]*"'),
        ("comment", r"<!--.*?-->"),
    ],
    ".css": [
        ("selector", r"[.#]?[a-zA-Z][a-zA-Z0-9_-]*\s*\{"),
        ("property", r"[a-zA-Z-]+\s*:"),
        ("string_d", r'"[^"]*"'),
        ("comment", r"/\*.*?\*/"),
        ("number", r"\b\d+\.?\d*(px|em|rem|%|vh|vw)?\b"),
    ],
}

SYNTAX_COLORS: dict[str, str] = {
    "keyword": "#569CD6",
    "builtin": "#DCDCAA",
    "string_d": "#CE9178",
    "string_s": "#CE9178",
    "comment": "#6A9955",
    "number": "#B5CEA8",
    "tag": "#569CD6",
    "selector": "#D7BA7D",
    "property": "#9CDCFE",
    "builtin_fn": "#DCDCAA",
}

CARD_W = 220
CARD_H = 160
CARD_GAP = 28
PREVIEW_FILES = 3


def _item_icon(path: Path) -> str:
    if path.is_dir():
        return "📁"
    suffix = path.suffix.lower()
    return {
        ".py": "🐍", ".js": "🟨", ".ts": "💙", ".html": "🌐",
        ".css": "🎨", ".json": "📋", ".md": "📝", ".txt": "📄",
        ".pdf": "📕", ".png": "🖼", ".jpg": "🖼", ".jpeg": "🖼",
        ".mp4": "🎬", ".mp3": "🎵", ".zip": "📦", ".csv": "📊",
    }.get(suffix, "📄")


class SyntaxHighlightEditor(QTextEdit):
    def __init__(self, extension: str, parent=None):
        super().__init__(parent)
        self._extension = extension
        self.setFont(QFont("Courier New", 10))
        self.setStyleSheet(f"""
            QTextEdit {{
                background: #1e1e1e;
                color: #d4d4d4;
                border: none;
                selection-background-color: #264f78;
            }}
            QScrollBar:vertical {{
                background: #1e1e1e; width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: #3c3c3c; border-radius: 4px;
            }}
        """)

    def set_content(self, text: str):
        self.setPlainText(text)


class FileEditorModal(QDialog):
    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self._path = path
        self.setWindowTitle(f"Edit — {path.name}")
        self.setMinimumSize(820, 580)
        self.setStyleSheet(f"""
            QDialog {{
                background: #1e1e1e;
                border: 1px solid {C.BORDER_B};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(36)
        header.setStyleSheet(f"background: #252526; border-bottom: 1px solid {C.BORDER};")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(12, 0, 12, 0)
        icon_lbl = QLabel(f"{_item_icon(path)}  {path.name}")
        icon_lbl.setFont(QFont("Courier New", 9))
        icon_lbl.setStyleSheet(f"color: {C.WHITE}; background: transparent;")
        h_lay.addWidget(icon_lbl)
        h_lay.addStretch()
        ext_lbl = QLabel(path.suffix.upper() or "TEXT")
        ext_lbl.setFont(QFont("Courier New", 8))
        ext_lbl.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        h_lay.addWidget(ext_lbl)
        layout.addWidget(header)

        self._editor = SyntaxHighlightEditor(path.suffix)
        try:
            self._editor.set_content(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            self._editor.set_content("")
        layout.addWidget(self._editor, stretch=1)

        footer = QWidget()
        footer.setFixedHeight(44)
        footer.setStyleSheet(f"background: #252526; border-top: 1px solid {C.BORDER};")
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(12, 6, 12, 6)
        f_lay.setSpacing(8)
        f_lay.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(90, 28)
        cancel_btn.setFont(QFont("Courier New", 8))
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C.TEXT_MED};
                border: 1px solid {C.BORDER}; border-radius: 3px;
            }}
            QPushButton:hover {{ border-color: {C.BORDER_B}; color: {C.WHITE}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        f_lay.addWidget(cancel_btn)

        save_btn = QPushButton("▸  Save")
        save_btn.setFixedSize(90, 28)
        save_btn.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PRI_GHO}; color: {C.PRI};
                border: 1px solid {C.PRI_DIM}; border-radius: 3px;
            }}
            QPushButton:hover {{ background: {C.BORDER_A}; border-color: {C.PRI}; }}
        """)
        save_btn.clicked.connect(self._save)
        f_lay.addWidget(save_btn)
        layout.addWidget(footer)

    def _save(self):
        try:
            self._path.write_text(self._editor.toPlainText(), encoding="utf-8")
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", str(exc))


class FileCard(QWidget):
    clicked = pyqtSignal(Path)
    double_clicked = pyqtSignal(Path)

    def __init__(self, path: Path, is_creating: bool = False, parent=None):
        super().__init__(parent)
        self._path = path
        self._is_creating = is_creating
        self._hovered = False
        self.setFixedSize(CARD_W, CARD_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if is_creating:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(12, 40, 12, 12)
            self._name_input = QLineEdit()
            self._name_input.setPlaceholderText("name.ext")
            self._name_input.setFont(QFont("Courier New", 10))
            self._name_input.setStyleSheet(f"""
                QLineEdit {{
                    background: {C.BG}; color: {C.WHITE};
                    border: 1px solid {C.PRI}; border-radius: 3px;
                    padding: 4px 6px;
                }}
            """)
            self._name_input.setFocus()
            layout.addWidget(self._name_input)
        else:
            self._name_input = None

    def get_name_input(self) -> QLineEdit | None:
        return self._name_input

    def enterEvent(self, _):
        self._hovered = True
        self.update()

    def leaveEvent(self, _):
        self._hovered = False
        self.update()

    def mousePressEvent(self, _):
        if self._path:
            self.clicked.emit(self._path)

    def mouseDoubleClickEvent(self, _):
        if self._path:
            self.double_clicked.emit(self._path)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._is_creating:
            border_col = qcol(C.PRI)
            bg_col = qcol(C.PANEL)
        elif self._hovered:
            border_col = qcol(C.PRI)
            bg_col = qcol(C.PRI_GHO)
        else:
            border_col = qcol(C.BORDER_B)
            bg_col = qcol(C.PANEL)

        p.setBrush(QBrush(bg_col))
        p.setPen(QPen(border_col, 1.5))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)

        if self._is_creating:
            p.setFont(QFont("Courier New", 20))
            p.setPen(QPen(qcol(C.PRI), 1))
            p.drawText(QRect(0, 8, CARD_W, 36), Qt.AlignmentFlag.AlignCenter, "+")
            return

        icon = _item_icon(self._path)
        p.setFont(QFont("Courier New", 28))
        p.setPen(QPen(qcol(C.WHITE), 1))
        p.drawText(QRect(0, 16, CARD_W, 48), Qt.AlignmentFlag.AlignCenter, icon)

        name = self._path.name
        if len(name) > 22:
            name = name[:19] + "..."
        p.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        p.setPen(QPen(qcol(C.WHITE if self._hovered else C.TEXT), 1))
        p.drawText(QRect(8, 70, CARD_W - 16, 20), Qt.AlignmentFlag.AlignCenter, name)

        if self._path.is_dir():
            try:
                children = [c for c in self._path.iterdir()][:PREVIEW_FILES]
                y = 96
                for child in children:
                    ci = _item_icon(child)
                    cn = child.name
                    if len(cn) > 24:
                        cn = cn[:21] + "..."
                    p.setFont(QFont("Courier New", 7))
                    p.setPen(QPen(qcol(C.TEXT_DIM), 1))
                    p.drawText(QRect(12, y, CARD_W - 24, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"{ci} {cn}")
                    y += 16
            except Exception:
                pass
        else:
            try:
                size = self._path.stat().st_size
                size_str = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
            except Exception:
                size_str = "—"
            p.setFont(QFont("Courier New", 7))
            p.setPen(QPen(qcol(C.TEXT_DIM), 1))
            p.drawText(QRect(8, 96, CARD_W - 16, 16), Qt.AlignmentFlag.AlignCenter, size_str)


class BreadcrumbBar(QWidget):
    navigate = pyqtSignal(Path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setStyleSheet(f"background: {C.DARK}; border-bottom: 1px solid {C.BORDER};")
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 0, 12, 0)
        self._layout.setSpacing(2)

    def set_path(self, current: Path, root: Path):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        parts = []
        temp = current
        while temp != root.parent:
            parts.insert(0, temp)
            if temp == root:
                break
            temp = temp.parent

        for i, part in enumerate(parts):
            btn = QPushButton(part.name)
            btn.setFont(QFont("Courier New", 8))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {C.PRI if i == len(parts) - 1 else C.TEXT_MED};
                    border: none; padding: 0 4px;
                }}
                QPushButton:hover {{ color: {C.PRI}; }}
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            target = part
            btn.clicked.connect(lambda _, t=target: self.navigate.emit(t))
            self._layout.addWidget(btn)

            if i < len(parts) - 1:
                sep = QLabel("›")
                sep.setFont(QFont("Courier New", 9))
                sep.setStyleSheet(f"color: {C.BORDER_B}; background: transparent;")
                self._layout.addWidget(sep)

        self._layout.addStretch()


class ProjectsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = PROJECTS_ROOT
        self._creating_type: str | None = None
        PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)

        self.setStyleSheet(f"background: {C.BG};")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        toolbar = self._build_toolbar()
        main_layout.addWidget(toolbar)

        self._breadcrumb = BreadcrumbBar()
        self._breadcrumb.navigate.connect(self._navigate_to)
        main_layout.addWidget(self._breadcrumb)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {C.BG}; }}")

        self._cards_container = QWidget()
        self._cards_container.setStyleSheet(f"background: {C.BG};")
        self._cards_layout = QHBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(24, 24, 24, 24)
        self._cards_layout.setSpacing(CARD_GAP)
        self._cards_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        scroll.setWidget(self._cards_container)
        main_layout.addWidget(scroll, stretch=1)

        self._refresh()

    def _build_toolbar(self) -> QWidget:
        toolbar = QWidget()
        toolbar.setFixedHeight(44)
        toolbar.setStyleSheet(f"background: {C.DARK}; border-bottom: 1px solid {C.BORDER};")
        t_lay = QHBoxLayout(toolbar)
        t_lay.setContentsMargins(16, 0, 16, 0)
        t_lay.setSpacing(8)

        title = QLabel("◈  PROJECTS")
        title.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        t_lay.addWidget(title)
        t_lay.addStretch()

        for label, action in [("＋ New File", "file"), ("＋ New Folder", "folder"), ("✕ Delete", "delete")]:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.setFont(QFont("Courier New", 8))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            is_del = action == "delete"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {C.RED if is_del else C.TEXT_MED};
                    border: 1px solid {C.RED if is_del else C.BORDER};
                    border-radius: 3px; padding: 0 10px;
                }}
                QPushButton:hover {{
                    color: {C.RED if is_del else C.PRI};
                    border-color: {C.RED if is_del else C.PRI};
                }}
            """)
            act = action
            btn.clicked.connect(lambda _, a=act: self._toolbar_action(a))
            t_lay.addWidget(btn)

        return toolbar

    def _toolbar_action(self, action: str):
        if action in ("file", "folder"):
            self._creating_type = action
            self._refresh()
        elif action == "delete":
            self._delete_selected()

    def _delete_selected(self):
        selected = self._find_selected_card()
        if not selected:
            return
        reply = QMessageBox.question(
            self, "Confirm Delete", f"Delete '{selected.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import shutil
                if selected.is_dir():
                    shutil.rmtree(selected)
                else:
                    selected.unlink()
                self._refresh()
            except Exception as exc:
                QMessageBox.critical(self, "Error", str(exc))

    def _find_selected_card(self) -> Path | None:
        return self._selected_path if hasattr(self, "_selected_path") else None

    def _navigate_to(self, path: Path):
        self._current_path = path
        self._creating_type = None
        self._refresh()

    def _refresh(self):
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._breadcrumb.set_path(self._current_path, PROJECTS_ROOT)

        if self._creating_type:
            placeholder_path = self._current_path / ".new_item"
            creator_card = FileCard(placeholder_path, is_creating=True)
            inp = creator_card.get_name_input()
            if inp:
                inp.returnPressed.connect(lambda: self._commit_creation(inp.text()))
            self._cards_layout.addWidget(creator_card)

        try:
            items = sorted(self._current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except Exception:
            items = []

        for item_path in items:
            card = FileCard(item_path)
            card.clicked.connect(self._on_card_clicked)
            card.double_clicked.connect(self._on_card_double_clicked)
            self._cards_layout.addWidget(card)

        self._cards_layout.addStretch()

    def _commit_creation(self, name: str):
        name = name.strip()
        if not name:
            self._creating_type = None
            self._refresh()
            return
        target = self._current_path / name
        try:
            if self._creating_type == "folder":
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.touch(exist_ok=True)
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
        finally:
            self._creating_type = None
            self._refresh()

    def _on_card_clicked(self, path: Path):
        self._selected_path = path

    def _on_card_double_clicked(self, path: Path):
        if path.is_dir():
            self._navigate_to(path)
        else:
            modal = FileEditorModal(path, self)
            modal.exec()
