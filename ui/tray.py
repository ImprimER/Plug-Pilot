from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


def create_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#4c8dff"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(6, 6, 52, 52, 13, 13)
    painter.setBrush(QColor("white"))
    painter.drawEllipse(20, 18, 7, 7)
    painter.drawEllipse(37, 18, 7, 7)
    painter.drawRoundedRect(19, 32, 26, 6, 3, 3)
    painter.drawRoundedRect(29, 34, 6, 15, 3, 3)
    painter.end()

    return QIcon(pixmap)


class TrayController:
    def __init__(self, window):
        self.window = window
        self.tray = QSystemTrayIcon(create_icon(), window)
        self.tray.setToolTip("PlugPilot")
        self.tray.activated.connect(self._activated)
        self._last_signature = None
        self.menu = QMenu()
        self.tray.setContextMenu(self.menu)
        self.tray.show()
        self.rebuild(force=True)

    def rebuild(self, force: bool = False) -> None:
        signature = tuple(
            sorted(
                (
                    plug.host,
                    plug.alias,
                    plug.online,
                    plug.is_on,
                )
                for plug in self.window.plugs.values()
            )
        )

        if not force and signature == self._last_signature:
            return

        self._last_signature = signature
        menu = QMenu()

        open_action = QAction("Ouvrir PlugPilot", self.window)
        open_action.triggered.connect(self.window.show_window)
        menu.addAction(open_action)
        menu.addSeparator()

        for plug in sorted(
            self.window.plugs.values(),
            key=lambda item: item.alias.lower(),
        ):
            state = (
                "Connexion…"
                if plug.connecting
                else "ON"
                if plug.online and plug.is_on
                else "OFF"
                if plug.online
                else "Hors ligne"
            )
            action = QAction(
                f"{plug.alias} — {state}",
                self.window,
            )
            action.setEnabled(plug.online and not plug.connecting)
            action.triggered.connect(
                lambda _checked=False,
                host=plug.host,
                current=plug.is_on:
                self.window.set_device_state(host, not current)
            )
            menu.addAction(action)

        menu.addSeparator()

        quit_action = QAction("Quitter", self.window)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.menu = menu

    def _activated(self, reason) -> None:
        if reason in (
            QSystemTrayIcon.Trigger,
            QSystemTrayIcon.DoubleClick,
        ):
            self.window.show_window()
