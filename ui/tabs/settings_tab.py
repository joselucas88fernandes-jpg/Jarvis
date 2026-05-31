import json
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSlider, QSpinBox,
    QVBoxLayout, QWidget,
)

from ui.colors import C, qcol

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent

BASE_DIR = get_base_dir()
API_FILE = BASE_DIR / "config" / "api_keys.json"
SETTINGS_FILE = BASE_DIR / "config" / "settings.json"

DEFAULTS: dict = {
    "autogpt_max_cycles": 10,
    "autogpt_until_complete": False,
    "vad_threshold_multiplier": 1.6,
    "mic_gain_boost": 1.8,
    "wake_word": "jarvis",
}


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return {**DEFAULTS, **json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))}
        except Exception:
            pass
    return dict(DEFAULTS)


def save_settings(settings: dict):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")


def _section_label(text: str) -> QLabel:
    lbl = QLabel(f"▸ {text}")
    lbl.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
    lbl.setStyleSheet(f"color: {C.PRI}; background: transparent; border-bottom: 1px solid {C.BORDER}; padding-bottom: 4px;")
    return lbl


def _field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Courier New", 8))
    lbl.setStyleSheet(f"color: {C.TEXT_MED}; background: transparent;")
    return lbl


def _separator() -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setStyleSheet(f"color: {C.BORDER}; margin: 6px 0;")
    return sep


class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C.BG};")
        self._settings = load_settings()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(44)
        header.setStyleSheet(f"background: {C.DARK}; border-bottom: 1px solid {C.BORDER};")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 0, 16, 0)
        title = QLabel("◈  SETTINGS")
        title.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        h_lay.addWidget(title)
        h_lay.addStretch()

        save_btn = QPushButton("▸  Save All")
        save_btn.setFixedHeight(28)
        save_btn.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PRI_GHO}; color: {C.PRI};
                border: 1px solid {C.PRI_DIM}; border-radius: 3px; padding: 0 12px;
            }}
            QPushButton:hover {{ background: {C.BORDER_A}; border-color: {C.PRI}; }}
        """)
        save_btn.clicked.connect(self._save_all)
        h_lay.addWidget(save_btn)
        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {C.BG}; }}")

        content = QWidget()
        content.setStyleSheet(f"background: {C.BG};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 24, 32, 32)
        layout.setSpacing(10)

        layout.addWidget(_section_label("API CONFIGURATION"))
        layout.addWidget(_field_label("Gemini API Key"))
        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_input.setFont(QFont("Courier New", 9))
        self._api_key_input.setFixedHeight(30)
        self._api_key_input.setStyleSheet(f"""
            QLineEdit {{
                background: {C.PANEL}; color: {C.WHITE};
                border: 1px solid {C.BORDER}; border-radius: 3px; padding: 3px 8px;
            }}
            QLineEdit:focus {{ border-color: {C.PRI}; }}
        """)
        try:
            d = json.loads(API_FILE.read_text(encoding="utf-8"))
            self._api_key_input.setText(d.get("gemini_api_key", ""))
        except Exception:
            pass
        layout.addWidget(self._api_key_input)

        layout.addSpacing(4)
        layout.addWidget(_separator())
        layout.addWidget(_section_label("WAKE-WORD"))
        layout.addWidget(_field_label("Activation Keyword"))
        self._wake_word_input = QLineEdit(self._settings.get("wake_word", "jarvis"))
        self._wake_word_input.setFont(QFont("Courier New", 9))
        self._wake_word_input.setFixedHeight(30)
        self._wake_word_input.setStyleSheet(f"""
            QLineEdit {{
                background: {C.PANEL}; color: {C.WHITE};
                border: 1px solid {C.BORDER}; border-radius: 3px; padding: 3px 8px;
            }}
            QLineEdit:focus {{ border-color: {C.PRI}; }}
        """)
        layout.addWidget(self._wake_word_input)

        layout.addSpacing(4)
        layout.addWidget(_separator())
        layout.addWidget(_section_label("AUDIO PROCESSING"))

        layout.addWidget(_field_label(f"Microphone Gain Boost  (×{self._settings['mic_gain_boost']:.1f})"))
        self._gain_label = layout.itemAt(layout.count() - 1).widget()
        self._gain_slider = QSlider(Qt.Orientation.Horizontal)
        self._gain_slider.setRange(10, 40)
        self._gain_slider.setValue(int(self._settings["mic_gain_boost"] * 10))
        self._gain_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ background: {C.BORDER}; height: 4px; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: {C.PRI}; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }}
            QSlider::sub-page:horizontal {{ background: {C.PRI_DIM}; height: 4px; border-radius: 2px; }}
        """)
        self._gain_slider.valueChanged.connect(
            lambda v: self._gain_label.setText(f"Microphone Gain Boost  (×{v / 10:.1f})")
        )
        layout.addWidget(self._gain_slider)

        layout.addSpacing(4)
        layout.addWidget(_field_label(f"VAD Noise Gate Multiplier  ({self._settings['vad_threshold_multiplier']:.1f}×)"))
        self._vad_label = layout.itemAt(layout.count() - 1).widget()
        self._vad_slider = QSlider(Qt.Orientation.Horizontal)
        self._vad_slider.setRange(10, 40)
        self._vad_slider.setValue(int(self._settings["vad_threshold_multiplier"] * 10))
        self._vad_slider.setStyleSheet(self._gain_slider.styleSheet())
        self._vad_slider.valueChanged.connect(
            lambda v: self._vad_label.setText(f"VAD Noise Gate Multiplier  ({v / 10:.1f}×)")
        )
        layout.addWidget(self._vad_slider)

        layout.addSpacing(4)
        layout.addWidget(_separator())
        layout.addWidget(_section_label("AUTOGPT AUTONOMOUS ENGINE"))

        layout.addWidget(_field_label("Maximum Execution Cycles"))
        self._cycles_spin = QSpinBox()
        self._cycles_spin.setRange(1, 500)
        self._cycles_spin.setValue(self._settings["autogpt_max_cycles"])
        self._cycles_spin.setFixedHeight(30)
        self._cycles_spin.setFont(QFont("Courier New", 9))
        self._cycles_spin.setStyleSheet(f"""
            QSpinBox {{
                background: {C.PANEL}; color: {C.WHITE};
                border: 1px solid {C.BORDER}; border-radius: 3px; padding: 3px 8px;
            }}
            QSpinBox:focus {{ border-color: {C.PRI}; }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background: {C.PANEL2}; border: none; width: 18px;
            }}
        """)
        layout.addWidget(self._cycles_spin)

        self._until_complete_chk = QCheckBox("Run until task is fully completed (ignores cycle limit)")
        self._until_complete_chk.setChecked(self._settings["autogpt_until_complete"])
        self._until_complete_chk.setFont(QFont("Courier New", 8))
        self._until_complete_chk.setStyleSheet(f"""
            QCheckBox {{ color: {C.TEXT_MED}; background: transparent; }}
            QCheckBox::indicator {{ width: 14px; height: 14px; border: 1px solid {C.BORDER_B}; border-radius: 2px; background: {C.PANEL}; }}
            QCheckBox::indicator:checked {{ background: {C.PRI}; border-color: {C.PRI}; }}
        """)
        layout.addWidget(self._until_complete_chk)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, stretch=1)

    def _save_all(self):
        self._settings["wake_word"] = self._wake_word_input.text().strip().lower() or "jarvis"
        self._settings["mic_gain_boost"] = self._gain_slider.value() / 10.0
        self._settings["vad_threshold_multiplier"] = self._vad_slider.value() / 10.0
        self._settings["autogpt_max_cycles"] = self._cycles_spin.value()
        self._settings["autogpt_until_complete"] = self._until_complete_chk.isChecked()
        save_settings(self._settings)

        api_key = self._api_key_input.text().strip()
        if api_key:
            try:
                existing = json.loads(API_FILE.read_text(encoding="utf-8")) if API_FILE.exists() else {}
            except Exception:
                existing = {}
            existing["gemini_api_key"] = api_key
            API_FILE.parent.mkdir(parents=True, exist_ok=True)
            API_FILE.write_text(json.dumps(existing, indent=4), encoding="utf-8")

    def get_settings(self) -> dict:
        return self._settings
