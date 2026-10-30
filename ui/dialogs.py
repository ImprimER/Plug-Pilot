from __future__ import annotations

import ipaddress

from PySide6.QtCore import Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from services.config import AppConfig
from services.version import APP_VERSION, RELEASES_URL


class AddDeviceDialog(QDialog):
    """Assistant simple pour rechercher ou ajouter une prise par IP."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Ajouter une prise")
        self.setMinimumWidth(560)
        self.action: str | None = None
        self.host: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(16)

        title = QLabel("Ajouter une prise")
        title.setObjectName("dialogTitle")
        root.addWidget(title)

        intro = QLabel(
            "Commence par la recherche automatique. Utilise l’adresse IP "
            "seulement si la prise n’est pas trouvée."
        )
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        root.addWidget(intro)

        automatic = QGroupBox("Méthode recommandée")
        automatic_layout = QVBoxLayout(automatic)
        automatic_text = QLabel(
            "PlugPilot analyse le réseau local et ajoute toutes les prises compatibles."
        )
        automatic_text.setObjectName("muted")
        automatic_text.setWordWrap(True)
        automatic_layout.addWidget(automatic_text)

        automatic_button = QPushButton("Rechercher automatiquement")
        automatic_button.clicked.connect(self._choose_automatic)
        automatic_layout.addWidget(automatic_button)
        root.addWidget(automatic)

        manual = QGroupBox("La prise n’apparaît pas ?")
        manual_layout = QVBoxLayout(manual)

        manual_text = QLabel(
            "Dans l’application Tapo, ouvre la prise puis ses informations pour "
            "retrouver son adresse IP. Exemple : 192.168.1.39"
        )
        manual_text.setObjectName("muted")
        manual_text.setWordWrap(True)
        manual_layout.addWidget(manual_text)

        row = QHBoxLayout()
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.39")
        self.ip_input.returnPressed.connect(self._choose_manual)
        row.addWidget(self.ip_input, 1)

        manual_button = QPushButton("Ajouter cette adresse")
        manual_button.setObjectName("secondary")
        manual_button.clicked.connect(self._choose_manual)
        row.addWidget(manual_button)
        manual_layout.addLayout(row)

        self.error = QLabel("")
        self.error.setObjectName("errorText")
        self.error.setWordWrap(True)
        manual_layout.addWidget(self.error)

        compatibility = QLabel(
            "Pour une P110, active aussi « Compatibilité avec les services tiers » "
            "dans l’application Tapo."
        )
        compatibility.setObjectName("infoBox")
        compatibility.setWordWrap(True)
        manual_layout.addWidget(compatibility)
        root.addWidget(manual)

        cancel = QDialogButtonBox(QDialogButtonBox.Cancel)
        cancel.button(QDialogButtonBox.Cancel).setText("Annuler")
        cancel.rejected.connect(self.reject)
        root.addWidget(cancel)

    def _choose_automatic(self) -> None:
        self.action = "automatic"
        self.accept()

    def _choose_manual(self) -> None:
        value = self.ip_input.text().strip()
        try:
            parsed = ipaddress.ip_address(value)
            if parsed.version != 4 or not parsed.is_private:
                raise ValueError
        except ValueError:
            self.error.setText(
                "Saisis une adresse IPv4 locale valide, par exemple 192.168.1.39."
            )
            self.ip_input.setFocus()
            return

        self.host = value
        self.action = "manual"
        self.accept()


class SettingsDialog(QDialog):
    change_account_requested = Signal()

    def __init__(self, parent, config: AppConfig, account_email: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Réglages de PlugPilot")
        self.setMinimumWidth(580)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        title = QLabel("Réglages")
        title.setObjectName("dialogTitle")
        root.addWidget(title)

        intro = QLabel(
            "Les options techniques d’ajout ont été déplacées dans le bouton "
            "« Ajouter une prise » pour garder cet écran simple."
        )
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        root.addWidget(intro)

        account_group = QGroupBox("Compte Tapo")
        account_layout = QHBoxLayout(account_group)
        texts = QVBoxLayout()
        label = QLabel("Compte utilisé")
        label.setObjectName("settingLabel")
        self.account_value = QLabel(account_email or "Aucun compte enregistré")
        self.account_value.setObjectName("muted")
        texts.addWidget(label)
        texts.addWidget(self.account_value)
        account_layout.addLayout(texts, 1)

        change_account = QPushButton("Modifier")
        change_account.setObjectName("secondary")
        change_account.clicked.connect(self.change_account_requested.emit)
        account_layout.addWidget(change_account)
        root.addWidget(account_group)

        energy_group = QGroupBox("Électricité")
        energy_form = QFormLayout(energy_group)
        self.kwh_price = QDoubleSpinBox()
        self.kwh_price.setRange(0, 10)
        self.kwh_price.setDecimals(4)
        self.kwh_price.setSingleStep(0.01)
        self.kwh_price.setSuffix(" €/kWh")
        self.kwh_price.setValue(config.kwh_price)
        energy_form.addRow("Prix du kWh", self.kwh_price)
        root.addWidget(energy_group)

        app_group = QGroupBox("Application")
        app_form = QFormLayout(app_group)
        self.refresh_interval = QSpinBox()
        self.refresh_interval.setRange(5, 60)
        self.refresh_interval.setSuffix(" secondes")
        self.refresh_interval.setValue(config.refresh_interval_seconds)
        app_form.addRow("Actualisation", self.refresh_interval)

        self.close_to_tray = QCheckBox(
            "Continuer à fonctionner près de l’horloge après fermeture"
        )
        self.close_to_tray.setChecked(config.close_action == "tray")
        self._tray_notification = config.tray_notification
        self._start_minimized = config.start_minimized
        app_form.addRow("", self.close_to_tray)
        root.addWidget(app_group)

        update_row = QHBoxLayout()
        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setObjectName("muted")
        update_row.addWidget(version_label)
        update_row.addStretch()
        updates_button = QPushButton("Mises à jour")
        updates_button.setObjectName("secondary")
        updates_button.clicked.connect(self.open_updates)
        update_row.addWidget(updates_button)
        root.addLayout(update_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def open_updates(self) -> None:
        from PySide6.QtWidgets import QMessageBox

        dialog = QMessageBox(self)
        dialog.setWindowTitle("Mises à jour de PlugPilot")
        dialog.setText(f"Version actuelle : {APP_VERSION}")
        dialog.setInformativeText(
            "Consulte les versions stables sur GitHub, puis télécharge "
            "l’installateur de la version souhaitée.\n\n"
            "Connecte-toi à ton compte GitHub si nécessaire. "
            "Quitte complètement PlugPilot avant de lancer l’installateur. "
            "Tes prises et réglages sont conservés."
        )
        open_button = dialog.addButton("Voir les versions", QMessageBox.AcceptRole)
        dialog.addButton("Fermer", QMessageBox.RejectRole)
        dialog.exec()
        if dialog.clickedButton() is open_button:
            if not QDesktopServices.openUrl(QUrl(RELEASES_URL)):
                QMessageBox.warning(
                    self, "Navigateur indisponible",
                    f"Ouvre cette adresse dans ton navigateur :\n{RELEASES_URL}",
                )

    def values(self) -> dict:
        return {
            "kwh_price": self.kwh_price.value(),
            "close_action": "tray" if self.close_to_tray.isChecked() else "quit",
            "tray_notification": self._tray_notification,
            "start_minimized": self._start_minimized,
            "refresh_interval_seconds": self.refresh_interval.value(),
        }


class CredentialsDialog(QDialog):
    def __init__(self, parent, email: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Compte TP-Link / Tapo")
        self.setMinimumWidth(460)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(12)

        title = QLabel("Connexion au compte Tapo")
        title.setObjectName("dialogTitle")
        root.addWidget(title)

        text = QLabel(
            "Ces identifiants servent uniquement à authentifier les prises Tapo. "
            "Ils sont enregistrés dans le gestionnaire sécurisé de Windows."
        )
        text.setObjectName("muted")
        text.setWordWrap(True)
        root.addWidget(text)

        form = QFormLayout()
        self.email = QLineEdit(email)
        self.email.setPlaceholderText("adresse@exemple.fr")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Mot de passe TP-Link / Tapo")
        form.addRow("Adresse e-mail", self.email)
        form.addRow("Mot de passe", self.password)
        root.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
