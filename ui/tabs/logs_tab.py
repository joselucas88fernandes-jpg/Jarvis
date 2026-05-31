import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget,
)

from ui.colors import C, qcol

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent

LOG_FILE = get_base_dir() / "logs" / "autogpt_audit.log"
SYS_LOG_FILE = get_base_dir() / "logs" / "system.log"

LEVEL_COLORS: dict[str, str] = {
    "SYS":    C.PRI,
    "JARVIS": C.GREEN,
    "You":    C.WHITE,
    "ERR":    C.RED,
    "WARN":   C.ACC,
    "FILE":   C.ACC2,
    "STEP":   C.TEXT_MED,
    "Cycle":  "#cc88ff",
}


def _colorize(line: str) -> str:
    for prefix, color in LEVEL_COLORS.items():
        if line.startswith(f"[") and f"] {prefix}" in line[:30]:
            return f'<span style="color:{color}">{line}</span>'
        if line.startswith(f"{prefix}:"):
            return f'<span style="color:{color}">{line}</span>'
    return f'<span style="color:{C.TEXT_MED}">{line}</span>'


class LogsTab(QWidget):
    append_log_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C.BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(44)
        header.setStyleSheet(f"background: {C.DARK}; border-bottom: 1px solid {C.BORDER};")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 0, 16, 0)
        h_lay.setSpacing(8)

        title = QLabel("◈  AUDIT LOGS")
        title.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        h_lay.addWidget(title)
        h_lay.addStretch()

        self._auto_scroll = True

        scroll_btn = QPushButton("⬇ Auto-Scroll ON")
        scroll_btn.setCheckable(True)
        scroll_btn.setChecked(True)
        scroll_btn.setFixedHeight(26)
        scroll_btn.setFont(QFont("Courier New", 7))
        scroll_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        scroll_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PRI_GHO}; color: {C.PRI};
                border: 1px solid {C.PRI_DIM}; border-radius: 3px; padding: 0 8px;
            }}
            QPushButton:checked {{ background: {C.PANEL}; color: {C.TEXT_DIM}; border-color: {C.BORDER}; }}
        """)
        scroll_btn.toggled.connect(self._toggle_scroll)
        h_lay.addWidget(scroll_btn)

        clear_btn = QPushButton("⊘ Clear View")
        clear_btn.setFixedHeight(26)
        clear_btn.setFont(QFont("Courier New", 7))
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C.TEXT_DIM};
                border: 1px solid {C.BORDER}; border-radius: 3px; padding: 0 8px;
            }}
            QPushButton:hover {{ color: {C.RED}; border-color: {C.RED}; }}
        """)
        clear_btn.clicked.connect(self._clear_view)
        h_lay.addWidget(clear_btn)
        layout.addWidget(header)

        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setFont(QFont("Courier New", 8))
        self._log_view.setStyleSheet(f"""
            QTextEdit {{
                background: {C.BG}; color: {C.TEXT_MED};
                border: none; padding: 8px;
            }}
            QScrollBar:vertical {{
                background: {C.PANEL}; width: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {C.BORDER_B}; border-radius: 3px;
            }}
        """)
        layout.addWidget(self._log_view, stretch=1)

        self.append_log_signal.connect(self.append)
        self._last_size = 0
        self._file_poll = QTimer(self)
        self._file_poll.timeout.connect(self._poll_file)
        self._file_poll.start(1500)

    def _toggle_scroll(self, checked: bool):
        self._auto_scroll = checked

    def _clear_view(self):
        self._log_view.clear()

    def append(self, text: str):
        for line in text.splitlines():
            if line.strip():
                self._log_view.append(_colorize(line))
        if self._auto_scroll:
            self._log_view.moveCursor(QTextCursor.MoveOperation.End)

    def _poll_file(self):
        for log_path in (LOG_FILE, SYS_LOG_FILE):
            if not log_path.exists():
                continue
            try:
                size = log_path.stat().st_size
                if size <= self._last_size:
                    continue
                with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
                    fh.seek(self._last_size)
                    new_text = fh.read()
                self._last_size = size
                for line in new_text.splitlines():
                    if line.strip():
                        self._log_view.append(_colorize(line))
                if self._auto_scroll:
                    self._log_view.moveCursor(QTextCursor.MoveOperation.End)
            except Exception:
                pass
