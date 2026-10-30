from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QLockFile, QStandardPaths
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from services.config import APP_DIR, LOG_FILE
from services.version import APP_VERSION
from ui.dashboard import MainWindow
from ui.themes import apply_theme


def install_exception_handler() -> None:
    def handle_exception(exc_type, exc_value, exc_traceback):
        APP_DIR.mkdir(parents=True, exist_ok=True)

        with LOG_FILE.open("a", encoding="utf-8") as log:
            log.write(
                "\n\n"
                f"--- {datetime.now().isoformat(timespec='seconds')} ---\n"
            )
            traceback.print_exception(
                exc_type,
                exc_value,
                exc_traceback,
                file=log,
            )

        QMessageBox.critical(
            None,
            "PlugPilot a rencontré une erreur",
            (
                "Une erreur inattendue s’est produite.\n\n"
                f"Le détail a été enregistré dans :\n{LOG_FILE}"
            ),
        )

    sys.excepthook = handle_exception


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PlugPilot")
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("PlugPilot")
    app.setQuitOnLastWindowClosed(False)

    install_exception_handler()

    lock_path = Path(
        QStandardPaths.writableLocation(
            QStandardPaths.TempLocation
        )
    ) / "PlugPilot.lock"

    instance_lock = QLockFile(str(lock_path))
    instance_lock.setStaleLockTime(0)

    if not instance_lock.tryLock(100):
        QMessageBox.information(
            None,
            "PlugPilot est déjà ouvert",
            (
                "Une instance de PlugPilot fonctionne déjà.\n"
                "Regarde près de l’horloge Windows."
            ),
        )
        return 0

    icon_path = (
        Path(__file__).resolve().parent
        / "assets"
        / "plugpilot.ico"
    )
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    apply_theme(app, window.config.dark_mode)
    app.aboutToQuit.connect(window.shutdown)
    if window.config.start_minimized:
        window.hide()
    else:
        window.show()

    exit_code = app.exec()
    instance_lock.unlock()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
