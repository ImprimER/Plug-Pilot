from __future__ import annotations

import ipaddress

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
        app_layout = QVBoxLayout(app_group)

        app_help = QLabel(
            "Définis le comportement de PlugPilot au démarrage et "
            "lorsque tu fermes sa fenêtre."
        )
        app_help.setObjectName("muted")
        app_help.setWordWrap(True)
        app_layout.addWidget(app_help)

        app_form = QFormLayout()

        self.refresh_interval = QSpinBox()
        self.refresh_interval.setRange(5, 60)
        self.refresh_interval.setSuffix(" secondes")
        self.refresh_interval.setValue(config.refresh_interval_seconds)
        app_form.addRow("Actualisation", self.refresh_interval)

        self.close_action = QComboBox()
        self.close_action.addItem(
            "Continuer près de l’horloge",
            "tray",
        )
        self.close_action.addItem(
            "Quitter complètement",
            "quit",
        )
        self.close_action.addItem(
            "Me demander à chaque fois",
            "ask",
        )
        close_index = self.close_action.findData(config.close_action)
        self.close_action.setCurrentIndex(max(0, close_index))
        app_form.addRow(
            "À la fermeture",
            self.close_action,
        )

        self.tray_notification = QComboBox()
        self.tray_notification.addItem(
            "Toujours afficher le message",
            "always",
        )
        self.tray_notification.addItem(
            "Une seule fois par session",
            "once",
        )
        self.tray_notification.addItem(
            "Ne jamais afficher le message",
            "never",
        )
        notification_index = self.tray_notification.findData(
            config.tray_notification
        )
        self.tray_notification.setCurrentIndex(
            max(0, notification_index)
        )
        app_form.addRow(
            "Message de confirmation",
            self.tray_notification,
        )

        app_layout.addLayout(app_form)

        self.start_minimized = QCheckBox(
            "Démarrer directement près de l’horloge"
        )
        self.start_minimized.setChecked(config.start_minimized)
        app_layout.addWidget(self.start_minimized)

        root.addWidget(app_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Save).setText("Enregistrer")
        buttons.button(QDialogButtonBox.Cancel).setText("Annuler")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def values(self) -> dict:
        return {
            "kwh_price": self.kwh_price.value(),
            "close_action": self.close_action.currentData(),
            "tray_notification": self.tray_notification.currentData(),
            "start_minimized": self.start_minimized.isChecked(),
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
