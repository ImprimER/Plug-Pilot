from __future__ import annotations

from PySide6.QtWidgets import QApplication


DARK = {
    "bg": "#12161b",
    "surface": "#1c2229",
    "surface_alt": "#252c34",
    "text": "#f5f7fa",
    "muted": "#96a0ab",
    "border": "#303843",
    "accent": "#4c8dff",
    "success": "#35c46a",
    "danger": "#ee5b6d",
    "info": "#192b45",
}

LIGHT = {
    "bg": "#f2f5f8",
    "surface": "#ffffff",
    "surface_alt": "#edf1f5",
    "text": "#20262d",
    "muted": "#6b7580",
    "border": "#d8dee6",
    "accent": "#2c6fda",
    "success": "#239b51",
    "danger": "#cf3f55",
    "info": "#e9f2ff",
}


def palette(dark_mode: bool) -> dict[str, str]:
    return DARK if dark_mode else LIGHT


def apply_theme(app: QApplication, dark_mode: bool) -> None:
    c = palette(dark_mode)
    app.setStyleSheet(
        f"""
        QWidget {{
            font-family: "Segoe UI";
            color: {c["text"]};
            font-size: 14px;
        }}

        QWidget#root,
        QDialog {{
            background: {c["bg"]};
        }}

        QLabel#title {{
            font-size: 30px;
            font-weight: 700;
        }}

        QLabel#dialogTitle {{
            font-size: 23px;
            font-weight: 700;
        }}

        QLabel#subtitle,
        QLabel#muted {{
            color: {c["muted"]};
        }}

        QLabel#settingLabel {{
            font-weight: 650;
        }}

        QLabel#infoBox {{
            background: {c["info"]};
            border: 1px solid {c["accent"]};
            border-radius: 9px;
            padding: 10px 12px;
        }}

        QGroupBox {{
            background: {c["surface"]};
            border: 1px solid {c["border"]};
            border-radius: 12px;
            margin-top: 10px;
            padding: 14px;
            font-weight: 650;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
        }}

        QFrame#summaryCard,
        QFrame#plugCard {{
            background: {c["surface"]};
            border: 1px solid {c["border"]};
            border-radius: 16px;
        }}

        QLabel#summaryIcon {{
            font-size: 23px;
        }}

        QLabel#summaryValue {{
            font-size: 22px;
            font-weight: 700;
        }}

        QLabel#summaryLabel {{
            color: {c["muted"]};
            font-size: 12px;
            font-weight: 600;
        }}

        QLabel#plugTitle {{
            font-size: 18px;
            font-weight: 700;
        }}

        QLabel#badge {{
            background: {c["surface_alt"]};
            color: {c["muted"]};
            border-radius: 9px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 600;
        }}

        QLabel#deviceStatus {{
            font-weight: 650;
        }}

        QLabel#statLabel {{
            color: {c["muted"]};
            font-size: 12px;
        }}

        QLabel#statValue {{
            font-size: 14px;
            font-weight: 600;
        }}

        QLineEdit,
        QDoubleSpinBox,
        QSpinBox {{
            background: {c["surface"]};
            border: 1px solid {c["border"]};
            border-radius: 10px;
            padding: 10px 12px;
            min-height: 20px;
        }}

        QCheckBox {{
            spacing: 9px;
        }}

        QPushButton {{
            background: {c["accent"]};
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 14px;
            font-weight: 700;
        }}

        QPushButton#secondary {{
            background: {c["surface_alt"]};
            color: {c["text"]};
            border: 1px solid {c["border"]};
        }}

        QLabel#errorText {{
            color: {c["danger"]};
        }}

        QToolButton#moreButton {{
            background: transparent;
            border: none;
            font-size: 22px;
            color: {c["muted"]};
            padding: 4px 8px;
        }}

        QToolButton#moreButton:hover {{
            background: {c["surface_alt"]};
            border-radius: 8px;
        }}

        QPushButton:disabled {{
            background: {c["surface_alt"]};
            color: {c["muted"]};
        }}

        QScrollArea {{
            background: transparent;
            border: none;
        }}

        QMenu {{
            background: {c["surface"]};
            color: {c["text"]};
            border: 1px solid {c["border"]};
        }}
        """
    )
