"""Public GitHub releases, bounded downloads and integrity verification. No credentials."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import tempfile
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from services.version import APP_VERSION, UPDATE_REPOSITORY


class UpdateError(Exception):
    pass


class DownloadCancelled(UpdateError):
    pass


def version_key(value: str) -> tuple[int, int, int, int]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(\.dev\d+)?", value)
    if not match:
        raise UpdateError("Numéro de version non reconnu.")
    return (*map(int, match.group(1, 2, 3)), 0 if match.group(4) else 1)


@dataclass(frozen=True)
class Update:
    version: str
    notes: str
    url: str
    size: int
    sha256: str


def parse_release(data: dict, current: str = APP_VERSION) -> Update | None:
    if data.get("draft") or data.get("prerelease"):
        return None
    version = str(data.get("tag_name", "")).removeprefix("v")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise UpdateError("La version publiée n’est pas une version stable valide.")
    if version_key(version) <= version_key(current):
        return None
    filename = f"PlugPilot-Setup-{version}.exe"
    asset = next((a for a in data.get("assets", []) if a.get("name") == filename), None)
    if asset is None:
        raise UpdateError("L’installateur de cette version n’est pas encore disponible.")
    url = str(asset.get("browser_download_url", ""))
    expected = f"https://github.com/{UPDATE_REPOSITORY}/releases/download/"
    if not url.startswith(expected) or urlsplit(url).netloc != "github.com":
        raise UpdateError("Adresse de téléchargement non autorisée.")
    digest = str(asset.get("digest", ""))
    if not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest):
        raise UpdateError("L’empreinte de vérification de l’installateur est indisponible.")
    size = asset.get("size")
    if not isinstance(size, int) or not 0 < size <= 600 * 1024 * 1024:
        raise UpdateError("Taille d’installateur non valide.")
    return Update(version, str(data.get("body") or "Améliorations et corrections.")[:12000],
                  url, size, digest[7:].lower())


def check_for_update() -> Update | None:
    request = Request(
        f"https://api.github.com/repos/{UPDATE_REPOSITORY}/releases/latest",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "PlugPilot-updater"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise UpdateError("Réponse du service de mises à jour trop volumineuse.")
        return parse_release(json.loads(raw))
    except HTTPError as error:
        if error.code == 404:
            raise UpdateError("Aucune version stable n’est encore disponible sur le service de mises à jour.") from error
        if error.code in (403, 429):
            raise UpdateError("Le service de mises à jour est temporairement limité. Réessaie plus tard.") from error
        raise UpdateError("Le service de mises à jour est indisponible.") from error
    except UpdateError:
        raise
    except Exception as error:
        raise UpdateError("Impossible de rechercher les mises à jour. Vérifie ta connexion Internet.") from error


def download_update(update: Update, progress, cancelled) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="PlugPilot-update-"))
    destination = directory / f"PlugPilot-Setup-{update.version}.exe"
    partial = destination.with_suffix(".part")
    digest = hashlib.sha256()
    received = 0
    started = time.monotonic()
    try:
        request = Request(update.url, headers={"User-Agent": "PlugPilot-updater"})
        with urlopen(request, timeout=15) as response, partial.open("wb") as output:
            final = urlsplit(response.geturl())
            if final.scheme != "https" or final.hostname not in {
                "github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"
            }:
                raise UpdateError("Destination de téléchargement non autorisée.")
            while True:
                if cancelled():
                    raise DownloadCancelled("Téléchargement annulé.")
                if time.monotonic() - started > 600:
                    raise UpdateError("Le téléchargement a pris trop de temps. Réessaie.")
                chunk = response.read(128 * 1024)
                if not chunk:
                    break
                received += len(chunk)
                if received > update.size:
                    raise UpdateError("La taille du téléchargement ne correspond pas à la version publiée.")
                output.write(chunk)
                digest.update(chunk)
                progress(int(received * 100 / update.size))
        if received != update.size or digest.hexdigest() != update.sha256:
            raise UpdateError("La vérification du téléchargement a échoué. L’installateur ne sera pas lancé.")
        partial.replace(destination)
        return destination
    except Exception:
        partial.unlink(missing_ok=True)
        directory.rmdir()
        raise
