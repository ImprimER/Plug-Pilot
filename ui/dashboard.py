from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from models.plug import PlugView
from services.async_worker import AsyncWorker
from services.config import AppConfig, ConfigService
from services.plug_manager import PlugManager
from tplink.credentials import (
    load_credentials,
    load_email,
    save_credentials,
)
from ui.dialogs import AddDeviceDialog, CredentialsDialog, SettingsDialog
from ui.themes import apply_theme
from ui.tray import TrayController
from ui.widgets import PlugCard, SummaryCard


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.config_service = ConfigService()
        self.config: AppConfig = self.config_service.load()
        self.manager = PlugManager(self.config_service, self.config)
        self.worker = AsyncWorker()

        self.devices = {}
        self.plugs: dict[str, PlugView] = {}
        self.cards: dict[str, PlugCard] = {}

        self.startup_pending = set()
        self.refresh_running = False
        self.discovery_running = False
        self.user_action_running = False

        self.setWindowTitle("PlugPilot")
        self.resize(
            self.config.window_width,
            self.config.window_height,
        )
        self.setMinimumSize(820, 560)

        self.build_ui()
        self.tray = TrayController(self)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_known_devices)
        self.apply_refresh_interval()

        self.load_cached_devices()
        QTimer.singleShot(150, self.connect_known_devices)

    def apply_refresh_interval(self) -> None:
        base_seconds = self.config.refresh_interval_seconds
        interval_seconds = (
            base_seconds
            if self.isVisible()
            else max(15, base_seconds * 3)
        )
        self.refresh_timer.setInterval(interval_seconds * 1000)

    def build_ui(self) -> None:
        root_widget = QWidget()
        root_widget.setObjectName("root")
        self.setCentralWidget(root_widget)

        root = QVBoxLayout(root_widget)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(15)

        header = QHBoxLayout()

        titles = QVBoxLayout()
        title = QLabel("Mes prises")
        title.setObjectName("title")
        subtitle = QLabel("Pilotez vos prises TP-Link depuis Windows")
        subtitle.setObjectName("subtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)

        header.addLayout(titles)
        header.addStretch()

        self.theme_button = QPushButton(
            "Thème clair"
            if self.config.dark_mode
            else "Thème sombre"
        )
        self.theme_button.setObjectName("secondary")
        self.theme_button.clicked.connect(self.toggle_theme)
        header.addWidget(self.theme_button)

        settings_button = QPushButton("Réglages")
        settings_button.setObjectName("secondary")
        settings_button.clicked.connect(self.open_settings)
        header.addWidget(settings_button)

        add_button = QPushButton("Ajouter une prise")
        add_button.clicked.connect(self.open_add_device)
        header.addWidget(add_button)

        root.addLayout(header)

        summary = QHBoxLayout()
        summary.setSpacing(12)

        self.online_card = SummaryCard("●", "Disponibles", "0")
        self.power_card = SummaryCard("⚡", "Puissance totale", "0 W")
        self.cost_card = SummaryCard("€", "Coût du jour", "0 €")

        for card in (
            self.online_card,
            self.power_card,
            self.cost_card,
        ):
            summary.addWidget(card, 1)

        root.addLayout(summary)

        controls = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher une prise")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.rebuild_card_list)
        controls.addWidget(self.search, 1)

        self.counter = QLabel("Aucune prise chargée")
        self.counter.setObjectName("muted")
        controls.addWidget(self.counter)

        root.addLayout(controls)

        self.status = QLabel("Connexion aux prises…")
        self.status.setObjectName("muted")
        root.addWidget(self.status)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.card_container = QWidget()
        self.card_container.setObjectName("root")

        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(12)
        self.card_layout.addStretch()

        self.scroll.setWidget(self.card_container)
        root.addWidget(self.scroll, 1)

    def open_add_device(self) -> None:
        dialog = AddDeviceDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        if dialog.action == "automatic":
            self.discover_devices()
            return

        if dialog.action == "manual" and dialog.host:
            self.config_service.add_manual_ip(
                self.config,
                dialog.host,
            )
            self.status.setText(
                f"Connexion à {dialog.host}…"
            )
            self.connect_known_devices()

    def toggle_theme(self) -> None:
        self.config.dark_mode = not self.config.dark_mode
        self.config_service.save(self.config)
        apply_theme(
            QApplication.instance(),
            self.config.dark_mode,
        )
        self.theme_button.setText(
            "Thème clair"
            if self.config.dark_mode
            else "Thème sombre"
        )

        for card in self.cards.values():
            card.set_dark_mode(self.config.dark_mode)

    def open_settings(self) -> None:
        dialog = SettingsDialog(
            self,
            self.config,
            load_email(),
        )
        dialog.change_account_requested.connect(
            lambda: self.change_account(dialog)
        )

        if dialog.exec() != QDialog.Accepted:
            return

        values = dialog.values()
        self.config.kwh_price = values["kwh_price"]
        self.config.close_action = values["close_action"]
        self.config.tray_notification = values["tray_notification"]
        self.config.start_minimized = values["start_minimized"]
        self.config.refresh_interval_seconds = values[
            "refresh_interval_seconds"
        ]
        self.config_service.save(self.config)
        self.apply_refresh_interval()
        self.update_summary()

    def change_account(
        self,
        settings_dialog: QDialog | None = None,
    ) -> None:
        credentials = self.request_credentials()
        if credentials and settings_dialog:
            settings_dialog.account_value.setText(load_email())

    def request_credentials(self):
        dialog = CredentialsDialog(self, load_email())
        if dialog.exec() != QDialog.Accepted:
            return None

        email = dialog.email.text().strip()
        password = dialog.password.text()

        if not email or not password:
            QMessageBox.warning(
                self,
                "Informations manquantes",
                "L’adresse e-mail et le mot de passe sont obligatoires.",
            )
            return None

        save_credentials(email, password)
        return load_credentials()

    def load_cached_devices(self) -> None:
        cached = self.manager.cached_views()
        self.plugs = {plug.host: plug for plug in cached}

        if cached:
            self.status.setText(
                "Prises mémorisées chargées · connexion en cours…"
            )
            self.rebuild_card_list()
            self.tray.rebuild(force=True)

    def connect_known_devices(self) -> None:
        if self.startup_pending or self.refresh_running or self.discovery_running:
            return

        credentials = load_credentials() or self.request_credentials()
        if credentials is None:
            return

        if (
            not self.config.known_devices
            and not self.config.manual_ips
        ):
            self.discover_devices()
            return

        hosts = list(dict.fromkeys(
            [item["host"] for item in self.config.known_devices if item.get("host")]
            + self.config.manual_ips
        ))
        self.startup_pending = set(hosts)
        self.status.setText("Connexion aux prises mémorisées…")
        for host in hosts:
            self.worker.submit(
                self.manager.connect_one(host, credentials),
                self.startup_device_connected,
                lambda error, host=host: self.startup_device_failed(host, error),
            )

    def startup_device_failed(self, host: str, error: Exception) -> None:
        plug = self.plugs.get(host)
        if plug is not None:
            plug.connecting = False
            plug.online = False
            self.startup_device_connected(plug)
        else:
            self.startup_pending.discard(host)

    def startup_device_connected(self, plug: PlugView) -> None:
        self.startup_pending.discard(plug.host)
        self.plugs[plug.host] = plug
        self.devices = dict(self.manager.devices)
        self.config_service.remember_devices(self.config, [plug])
        self.rebuild_card_list()
        self.tray.rebuild()
        online = sum(item.online for item in self.plugs.values())
        pending = len(self.startup_pending)
        self.status.setText(
            f"{online} prise(s) connectée(s) · {pending} connexion(s) en cours"
            if pending else f"{online} prise(s) connectée(s)"
        )
        if not pending:
            self.refresh_timer.start()
            QTimer.singleShot(3000, self.discover_devices_silently)

    def known_devices_connected(
        self,
        plugs: list[PlugView],
    ) -> None:
        self.config_service.apply_custom_aliases(
            self.config,
            plugs,
        )
        self.plugs = {plug.host: plug for plug in plugs}
        self.devices = dict(self.manager.devices)
        self.refresh_running = False

        online = sum(1 for plug in plugs if plug.online)
        self.status.setText(
            f"{online} prise(s) connectée(s)"
        )

        self.config_service.remember_devices(
            self.config,
            plugs,
        )
        self.rebuild_card_list()
        self.tray.rebuild()
        self.refresh_timer.start()

        # La découverte complète reste en arrière-plan et n'empêche pas
        # l'utilisation immédiate des prises déjà connues.
        QTimer.singleShot(3000, self.discover_devices_silently)

    def discover_devices_silently(self) -> None:
        if self.discovery_running:
            return

        credentials = load_credentials()
        if credentials is None:
            return

        self.discovery_running = True
        self.worker.submit(
            self.manager.discover(credentials),
            self.background_discovery_finished,
            self.background_discovery_failed,
        )

    def background_discovery_finished(
        self,
        plugs: list[PlugView],
    ) -> None:
        self.discovery_running = False
        self.config_service.apply_custom_aliases(
            self.config,
            plugs,
        )

        merged = dict(self.plugs)
        changed_hosts: set[str] = set()

        for plug in plugs:
            previous = merged.get(plug.host)
            merged[plug.host] = plug
            if previous != plug:
                changed_hosts.add(plug.host)

        self.plugs = merged
        self.devices = dict(self.manager.devices)

        self.config_service.remember_devices(
            self.config,
            plugs,
        )
        self.status.setText(
            f"Synchronisé à {datetime.now().strftime('%H:%M:%S')}"
        )

        if changed_hosts or set(self.cards) != set(self.plugs):
            self.rebuild_card_list()
        else:
            self.update_existing_cards()

        self.tray.rebuild()

    def background_discovery_failed(
        self,
        _error: Exception,
    ) -> None:
        self.discovery_running = False
        self.status.setText(
            f"Synchronisé à {datetime.now().strftime('%H:%M:%S')}"
        )

    def discover_devices(self) -> None:
        if self.startup_pending or self.discovery_running:
            return

        credentials = load_credentials() or self.request_credentials()
        if credentials is None:
            return

        self.refresh_timer.stop()
        self.discovery_running = True
        self.status.setText(
            "Recherche des prises sur le réseau…"
        )

        self.worker.submit(
            self.manager.discover(credentials),
            self.discovery_finished,
            self.operation_failed_visible,
        )

    def discovery_finished(
        self,
        plugs: list[PlugView],
    ) -> None:
        self.config_service.apply_custom_aliases(
            self.config,
            plugs,
        )
        self.plugs = {plug.host: plug for plug in plugs}
        self.devices = dict(self.manager.devices)
        self.discovery_running = False
        self.refresh_running = False

        self.config_service.remember_devices(
            self.config,
            plugs,
        )

        self.status.setText(
            (
                f"{len(plugs)} prise(s) trouvée(s) · "
                f"{datetime.now().strftime('%H:%M:%S')}"
            )
            if plugs
            else (
                "Aucune prise trouvée. "
                "Essaie l’ajout par adresse IP."
            )
        )

        self.rebuild_card_list()
        self.refresh_timer.start()
        self.tray.rebuild()

    def refresh_known_devices(self) -> None:
        if self.startup_pending or self.refresh_running:
            return

        self.refresh_running = True
        self.worker.submit(
            self.manager.refresh_next(),
            self.refresh_one_finished,
            self.operation_failed_silent,
        )

    def refresh_one_finished(
        self,
        plug: PlugView | None,
    ) -> None:
        self.refresh_running = False
        if plug is None:
            return

        self.plugs[plug.host] = plug
        card = self.cards.get(plug.host)
        if card is not None:
            card.update_view(plug)

        self.status.setText(
            f"Synchronisé à {datetime.now().strftime('%H:%M:%S')}"
        )
        self.update_summary()
        self.tray.rebuild()

    def set_device_state(
        self,
        host: str,
        target_on: bool,
    ) -> None:
        plug = self.plugs.get(host)

        if (
            not plug
            or not plug.online
            or self.user_action_running
        ):
            return

        self.refresh_timer.stop()
        self.user_action_running = True
        self.status.setText(
            f"{'Allumage' if target_on else 'Extinction'} "
            f"de {plug.alias}…"
        )

        self.worker.submit(
            self.manager.set_state(host, target_on),
            self.state_changed,
            self.operation_failed_visible,
        )

    def state_changed(self, plug: PlugView) -> None:
        self.user_action_running = False
        self.refresh_timer.start()
        self.plugs[plug.host] = plug
        card = self.cards.get(plug.host)
        if card is not None:
            card.update_view(plug)
        self.update_summary()
        self.tray.rebuild()

    def rename_device(self, host: str) -> None:
        plug = self.plugs.get(host)
        if plug is None:
            return

        new_name, accepted = QInputDialog.getText(
            self,
            "Renommer la prise",
            "Nom affiché dans PlugPilot :",
            text=plug.alias,
        )

        new_name = new_name.strip()
        if not accepted or not new_name:
            return

        self.manager.rename(host, new_name)
        plug.alias = new_name

        self.status.setText(
            f"Prise renommée en « {new_name} »"
        )
        self.rebuild_card_list()
        self.tray.rebuild(force=True)

    def forget_device(self, host: str) -> None:
        plug = self.plugs.get(host)
        name = plug.alias if plug else host

        answer = QMessageBox.question(
            self,
            "Oublier cette prise",
            (
                f"Retirer « {name} » de PlugPilot ?\n\n"
                "La prise ne sera pas réinitialisée."
            ),
        )

        if answer != QMessageBox.Yes:
            return

        self.manager.forget(host)
        self.plugs.pop(host, None)
        self.devices.pop(host, None)
        self.rebuild_card_list()
        self.tray.rebuild(force=True)

    def copy_ip(self, host: str) -> None:
        QApplication.clipboard().setText(host)
        self.status.setText("Adresse IP copiée")

    def operation_failed_visible(
        self,
        error: Exception,
    ) -> None:
        self.refresh_running = False
        self.discovery_running = False
        self.user_action_running = False
        self.refresh_timer.start()
        self.status.setText(
            "Communication impossible avec la prise."
        )

        QMessageBox.critical(
            self,
            "Erreur de communication",
            f"{type(error).__name__} : {error}",
        )

        self.update_existing_cards()

    def operation_failed_silent(
        self,
        _error: Exception,
    ) -> None:
        self.refresh_running = False
        self.discovery_running = False
        self.user_action_running = False
        self.refresh_timer.start()
        self.status.setText(
            "Certaines prises ne répondent pas."
        )
        self.update_existing_cards()

    def clear_cards(self) -> None:
        while self.card_layout.count() > 1:
            item = self.card_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.cards.clear()

    def visible_plugs(self) -> list[PlugView]:
        query = self.search.text().strip().lower()

        return sorted(
            (
                plug
                for plug in self.plugs.values()
                if (
                    not query
                    or query in plug.alias.lower()
                    or query in plug.model.lower()
                    or query in plug.host.lower()
                )
            ),
            key=lambda plug: plug.alias.lower(),
        )

    def rebuild_card_list(self) -> None:
        self.clear_cards()
        visible = self.visible_plugs()

        if not visible:
            empty = QLabel(
                (
                    "Aucun résultat."
                    if self.plugs
                    else (
                        "Aucune prise enregistrée. "
                        "Clique sur « Ajouter une prise »."
                    )
                )
            )
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignCenter)
            empty.setWordWrap(True)
            empty.setMinimumHeight(180)
            self.card_layout.insertWidget(0, empty)
            self.update_summary()
            return

        for plug in visible:
            card = PlugCard(
                plug,
                self.config.dark_mode,
            )
            card.toggle_requested.connect(
                self.set_device_state
            )
            card.rename_requested.connect(
                self.rename_device
            )
            card.copy_ip_requested.connect(
                self.copy_ip
            )
            card.forget_requested.connect(
                self.forget_device
            )
            self.cards[plug.host] = card
            self.card_layout.insertWidget(
                self.card_layout.count() - 1,
                card,
            )

        self.update_summary()

    def update_existing_cards(self) -> None:
        visible_hosts = {
            plug.host for plug in self.visible_plugs()
        }

        if visible_hosts != set(self.cards):
            self.rebuild_card_list()
            return

        for host, card in self.cards.items():
            plug = self.plugs.get(host)
            if plug:
                card.update_view(plug)

    def update_summary(self) -> None:
        online = sum(
            1 for plug in self.plugs.values() if plug.online
        )
        connecting = sum(
            1 for plug in self.plugs.values() if plug.connecting
        )
        offline = len(self.plugs) - online - connecting
        total_power = sum(
            plug.power_w or 0
            for plug in self.plugs.values()
            if plug.online
        )
        total_energy = sum(
            plug.energy_today_kwh or 0
            for plug in self.plugs.values()
            if plug.online
        )

        if not self.plugs:
            counter = "Aucune prise chargée"
        else:
            parts = []
            if online:
                parts.append(f"{online} disponible(s)")
            if connecting:
                parts.append(f"{connecting} en connexion")
            if offline:
                parts.append(f"{offline} hors ligne")
            counter = " · ".join(parts)

        self.counter.setText(counter)
        self.online_card.set_value(str(online))
        self.power_card.set_value(
            f"{total_power:.1f} W"
        )
        self.cost_card.set_value(
            f"{total_energy * self.config.kwh_price:.3f} €"
        )

    def show_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.apply_refresh_interval()

    def changeEvent(self, event) -> None:
        super().changeEvent(event)

        if event.type() == QEvent.WindowStateChange:
            self.apply_refresh_interval()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self.apply_refresh_interval()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.apply_refresh_interval()

    def closeEvent(self, event) -> None:
        self.config.window_width = self.width()
        self.config.window_height = self.height()
        self.config_service.save(self.config)

        action = self.config.close_action

        if action == "ask":
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Fermer PlugPilot")
            dialog.setText("Que doit faire PlugPilot ?")
            dialog.setInformativeText(
                "Ce choix peut être modifié dans les réglages."
            )

            tray_button = dialog.addButton(
                "Continuer près de l’horloge",
                QMessageBox.AcceptRole,
            )
            quit_button = dialog.addButton(
                "Quitter complètement",
                QMessageBox.DestructiveRole,
            )
            cancel_button = dialog.addButton(
                "Annuler",
                QMessageBox.RejectRole,
            )
            dialog.exec()

            clicked = dialog.clickedButton()
            if clicked is cancel_button:
                event.ignore()
                return

            action = "tray" if clicked is tray_button else "quit"

        if action == "tray":
            event.ignore()
            self.hide()
            return

        event.accept()

    def shutdown(self) -> None:
        self.refresh_timer.stop()
        self.worker.shutdown()
