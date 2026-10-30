from __future__ import annotations

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMenu,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from models.plug import PlugView
from ui.themes import palette


class SummaryCard(QFrame):
    def __init__(self, icon: str, label: str, value: str):
        super().__init__()
        self.setObjectName("summaryCard")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 28))
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)

        icon_label = QLabel(icon)
        icon_label.setObjectName("summaryIcon")
        layout.addWidget(icon_label)

        texts = QVBoxLayout()
        texts.setSpacing(1)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("summaryValue")
        self.label_label = QLabel(label)
        self.label_label.setObjectName("summaryLabel")

        texts.addWidget(self.value_label)
        texts.addWidget(self.label_label)
        layout.addLayout(texts)
        layout.addStretch()

    def set_value(self, value: str) -> None:
        if self.value_label.text() != value:
            self.value_label.setText(value)


class AnimatedSwitch(QWidget):
    toggled = Signal(bool)

    def __init__(self, checked: bool = False):
        super().__init__()
        self._checked = checked
        self._offset = 26.0 if checked else 4.0
        self._dark_mode = True
        self.setFixedSize(54, 30)
        self.setCursor(Qt.PointingHandCursor)

        self.animation = QPropertyAnimation(self, b"offset", self)
        self.animation.setDuration(160)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

    def set_dark_mode(self, dark_mode: bool) -> None:
        self._dark_mode = dark_mode
        self.update()

    def setChecked(self, checked: bool, animate: bool = False) -> None:
        if self._checked == checked and not animate:
            return

        self._checked = checked
        target = 26.0 if checked else 4.0

        if animate:
            self.animation.stop()
            self.animation.setStartValue(self._offset)
            self.animation.setEndValue(target)
            self.animation.start()
        else:
            self._offset = target
            self.update()

    def mousePressEvent(self, event) -> None:
        if self.isEnabled() and event.button() == Qt.LeftButton:
            self.setChecked(not self._checked, animate=True)
            self.toggled.emit(self._checked)
        super().mousePressEvent(event)

    def paintEvent(self, _event) -> None:
        colors = palette(self._dark_mode)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(
            QColor(
                colors["accent"]
                if self._checked
                else colors["border"]
            )
        )
        painter.drawRoundedRect(self.rect(), 15, 15)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(int(self._offset), 4, 22, 22)

    def get_offset(self) -> float:
        return self._offset

    def set_offset(self, value: float) -> None:
        self._offset = value
        self.update()

    offset = Property(float, get_offset, set_offset)


class StatBlock(QWidget):
    def __init__(self, label: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.label = QLabel(label)
        self.label.setObjectName("statLabel")
        self.value = QLabel("—")
        self.value.setObjectName("statValue")

        layout.addWidget(self.label)
        layout.addWidget(self.value)

    def set_value(self, value: str) -> None:
        if self.value.text() != value:
            self.value.setText(value)


class PlugCard(QFrame):
    toggle_requested = Signal(str, bool)
    rename_requested = Signal(str)
    copy_ip_requested = Signal(str)
    forget_requested = Signal(str)

    def __init__(self, plug: PlugView, dark_mode: bool):
        super().__init__()
        self.plug = plug
        self.dark_mode = dark_mode
        self.setObjectName("plugCard")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 32))
        self.setGraphicsEffect(shadow)

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 15, 16, 15)
        root.setSpacing(14)

        self.indicator = QLabel()
        self.indicator.setFixedSize(11, 11)
        root.addWidget(self.indicator, 0, Qt.AlignTop)

        content = QVBoxLayout()
        content.setSpacing(10)

        title_row = QHBoxLayout()
        self.title = QLabel()
        self.title.setObjectName("plugTitle")
        title_row.addWidget(self.title)

        self.badge = QLabel()
        self.badge.setObjectName("badge")
        title_row.addWidget(self.badge)
        title_row.addStretch()

        self.status_text = QLabel()
        self.status_text.setObjectName("deviceStatus")
        title_row.addWidget(self.status_text)
        content.addLayout(title_row)

        stats = QHBoxLayout()
        stats.setSpacing(34)

        self.power = StatBlock("Puissance")
        self.energy = StatBlock("Aujourd’hui")
        stats.addWidget(self.power, 1)
        stats.addWidget(self.energy, 1)
        stats.addStretch(1)

        content.addLayout(stats)
        root.addLayout(content, 1)

        self.switch = AnimatedSwitch()
        self.switch.set_dark_mode(dark_mode)
        self.switch.toggled.connect(self._toggle)
        root.addWidget(self.switch, 0, Qt.AlignVCenter)

        self.more = QToolButton()
        self.more.setText("⋯")
        self.more.setObjectName("moreButton")
        self.more.setPopupMode(QToolButton.InstantPopup)
        self.more.setMenu(self._build_menu())
        root.addWidget(self.more, 0, Qt.AlignVCenter)

        self.update_view(plug)

    def _build_menu(self) -> QMenu:
        menu = QMenu(self)

        rename_action = menu.addAction("Renommer")
        rename_action.triggered.connect(
            lambda: self.rename_requested.emit(self.plug.host)
        )

        menu.addSeparator()

        copy_action = menu.addAction("Copier l’adresse IP")
        copy_action.triggered.connect(
            lambda: self.copy_ip_requested.emit(self.plug.host)
        )

        forget_action = menu.addAction("Oublier cette prise")
        forget_action.triggered.connect(
            lambda: self.forget_requested.emit(self.plug.host)
        )

        return menu

    def update_view(self, plug: PlugView) -> None:
        self.plug = plug
        self.title.setText(plug.alias)
        self.badge.setText(plug.model)

        colors = palette(self.dark_mode)

        if plug.connecting:
            color = colors["accent"]
            self.power.set_value("Connexion…")
            self.energy.set_value("Connexion…")
            self.status_text.setText("Connexion…")
            self.status_text.setStyleSheet(f"color: {color};")
            self.switch.setEnabled(False)
            self.switch.setChecked(False)
        elif not plug.online:
            color = colors["muted"]
            self.power.set_value("—")
            self.energy.set_value("—")
            self.status_text.setText("Hors ligne")
            self.status_text.setStyleSheet(
                f"color: {colors['muted']};"
            )
            self.switch.setEnabled(False)
            self.switch.setChecked(False)
        else:
            color = (
                colors["success"]
                if plug.is_on
                else colors["danger"]
            )
            state_text = "Allumée" if plug.is_on else "Éteinte"

            self.power.set_value(
                f"{plug.power_w:.1f} W"
                if plug.power_w is not None
                else "Non disponible"
            )
            self.energy.set_value(
                f"{plug.energy_today_kwh:.3f} kWh"
                if plug.energy_today_kwh is not None
                else "Non disponible"
            )
            self.status_text.setText(state_text)
            self.status_text.setStyleSheet(f"color: {color};")
            self.switch.setEnabled(True)
            self.switch.setChecked(plug.is_on)

        self.indicator.setStyleSheet(
            f"background:{color}; border-radius:6px;"
        )

    def set_dark_mode(self, dark_mode: bool) -> None:
        self.dark_mode = dark_mode
        self.switch.set_dark_mode(dark_mode)
        self.update_view(self.plug)

    def _toggle(self, target_on: bool) -> None:
        if self.plug.online:
            self.switch.setEnabled(False)
            self.toggle_requested.emit(
                self.plug.host,
                target_on,
            )
