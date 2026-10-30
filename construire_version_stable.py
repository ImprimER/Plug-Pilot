"""Build a fresh Windows installer. Does not publish or install it."""
from pathlib import Path
import os
import re
import subprocess
import sys

from services.version import APP_VERSION


def main() -> int:
    root = Path(__file__).resolve().parent
    if not re.fullmatch(r"\d+\.\d+\.\d+", APP_VERSION):
        print(f"Version de développement : {APP_VERSION}")
        print("Après validation, définir une version stable (ex. 1.1.0) dans services/version.py.")
        return 1
    compilers = [
        Path(os.environ.get(key, "C:/Program Files")) / "Inno Setup 6/ISCC.exe"
        for key in ("ProgramFiles(x86)", "ProgramFiles")
    ]
    compiler = next((path for path in compilers if path.is_file()), None)
    if compiler is None:
        print("Inno Setup 6 est nécessaire pour construire l’installateur.")
        return 1
    (root / "VERSION.txt").write_text(APP_VERSION + "\n", encoding="utf-8")
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "PlugPilot.spec"],
        cwd=root, check=True,
    )
    subprocess.run(
        [str(compiler), f"/DMyAppVersion={APP_VERSION}",
         f"/FPlugPilot-Setup-{APP_VERSION}", "PlugPilot.iss"],
        cwd=root, check=True,
    )
    print(f"Installateur prêt : {root / 'installer' / f'PlugPilot-Setup-{APP_VERSION}.exe'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
