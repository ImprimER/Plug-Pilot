from pathlib import Path
import subprocess
import sys
import threading

from PySide6.QtCore import QObject, Signal, Slot, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QLabel, QMessageBox, QProgressBar,
    QPushButton, QVBoxLayout,
)

from services.updater import check_for_update, download_update, Update, UpdateError
from services.version import APP_VERSION, RELEASES_URL


class UpdateJob(QObject):
    completed = Signal(object)
    failed = Signal(str)
    progress = Signal(int)
    finished = Signal()

    def __init__(self, update=None, parent=None):
        super().__init__(parent)
        self.update = update
        self.cancelled = threading.Event()
        self.running = False

    def start(self):
        self.running = True
        QApplication.instance().aboutToQuit.connect(self.requestInterruption)
        threading.Thread(target=self.run, daemon=True, name="PlugPilotUpdate").start()

    def requestInterruption(self):
        self.cancelled.set()

    def isRunning(self):
        return self.running

    def run(self):
        try:
            result = (download_update(self.update, self.progress.emit, self.cancelled.is_set)
                      if self.update else check_for_update())
            self.completed.emit(result)
        except Exception as error:
            try:
                self.failed.emit(str(error) if isinstance(error, UpdateError)
                                 else "Le téléchargement a échoué. Vérifie ta connexion puis réessaie.")
            except RuntimeError:
                pass  # Application closed while the background operation ended.
        finally:
            self.running = False
            try:
                self.finished.emit()
            except RuntimeError:
                pass


class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mises à jour de PlugPilot")
        self.setMinimumWidth(520)
        self.job = None
        self.update = None
        self.installer = None
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        title = QLabel("Mises à jour")
        title.setObjectName("dialogTitle")
        root.addWidget(title)
        root.addWidget(QLabel(f"Version actuelle : {APP_VERSION}"))
        self.status = QLabel("Recherche d’une nouvelle version…")
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.notes = QPushButton("Voir les notes de version")
        self.notes.setObjectName("secondary")
        self.notes.clicked.connect(self.open_release_notes)
        self.notes.hide()
        root.addWidget(self.notes)
        self.progress = QProgressBar()
        self.progress.hide()
        root.addWidget(self.progress)
        row = QHBoxLayout()
        row.addStretch()
        self.action = QPushButton("Réessayer")
        self.action.hide()
        self.action.clicked.connect(self.perform_action)
        row.addWidget(self.action)
        self.close_button = QPushButton("Fermer")
        self.close_button.setObjectName("secondary")
        self.close_button.clicked.connect(self.reject)
        row.addWidget(self.close_button)
        root.addLayout(row)
        self.start_check()

    def start_check(self):
        self.update = self.installer = None
        self.notes.hide()
        self.progress.hide()
        self.status.setText("Recherche d’une nouvelle version…")
        self.action.hide()
        self.start_job(UpdateJob(parent=self))

    def start_job(self, job):
        # Keep the thread alive until finished, even after a result is delivered.
        self.job = job
        self.close_button.setText("Annuler")
        job.completed.connect(self.completed, Qt.QueuedConnection)
        job.failed.connect(self.failed, Qt.QueuedConnection)
        job.progress.connect(self.progress.setValue, Qt.QueuedConnection)
        job.finished.connect(self.job_finished, Qt.QueuedConnection)
        job.start()

    @Slot()
    def job_finished(self):
        self.close_button.setText("Fermer")
        self.action.setEnabled(True)

    @Slot(object)
    def completed(self, result):
        self.action.setEnabled(False)
        if isinstance(result, Update):
            self.update = result
            self.status.setText(f"La version {result.version} est disponible.")
            self.notes.show()
            self.action.setText("Mettre à jour")
            self.action.show()
        elif isinstance(result, Path):
            self.installer = result
            self.status.setText("La mise à jour est prête. PlugPilot se fermera puis redémarrera après l’installation.")
            self.action.setText("Installer et redémarrer" if getattr(sys, "frozen", False)
                                else "Afficher l’installateur téléchargé")
            self.action.show()
        else:
            self.status.setText("Tu utilises la dernière version disponible.")

    @Slot(str)
    def failed(self, message):
        self.status.setText(message)
        self.progress.hide()
        self.action.setText("Réessayer")
        self.action.setEnabled(False)
        self.action.show()

    def perform_action(self):
        if self.job and self.job.isRunning():
            return
        if self.installer:
            if not getattr(sys, "frozen", False):
                QMessageBox.information(self, "Version de développement",
                    "Le téléchargement est prêt. La version de développement reste indépendante "
                    "de l’application installée.\n\nInstallateur :\n" + str(self.installer))
                return
            try:
                subprocess.Popen([str(self.installer), "/SILENT", "/NORESTART", "/CLOSEAPPLICATIONS"],
                                 cwd=str(self.installer.parent))
            except OSError:
                self.status.setText("Impossible de lancer l’installateur. Réessaie.")
                return
            QApplication.instance().quit()
        elif self.update and self.action.text() != "Réessayer":
            self.action.hide()
            self.status.setText("Téléchargement de la mise à jour…")
            self.progress.setValue(0)
            self.progress.show()
            self.start_job(UpdateJob(self.update, self))
        else:
            self.start_check()

    def open_release_notes(self):
        if self.update and not QDesktopServices.openUrl(
                QUrl(f"{RELEASES_URL}/tag/v{self.update.version}")):
            QMessageBox.warning(self, "Notes de version", "Impossible d’ouvrir le navigateur.")

    def reject(self):
        if self.job and self.job.isRunning():
            self.job.requestInterruption()
            self.status.setText("Annulation en cours…")
            self.close_button.setEnabled(False)
            self.job.finished.connect(super().reject)
            return
        super().reject()

    def closeEvent(self, event):
        if self.job and self.job.isRunning():
            event.ignore()
            self.reject()
        else:
            super().closeEvent(event)
