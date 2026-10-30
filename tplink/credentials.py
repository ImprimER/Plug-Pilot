from __future__ import annotations

import keyring
from kasa import Credentials


SERVICE = "TapoPCControl"
EMAIL_KEY = "tplink-email"
PASSWORD_KEY = "tplink-password"


def load_credentials() -> Credentials | None:
    try:
        email = keyring.get_password(SERVICE, EMAIL_KEY)
        password = keyring.get_password(SERVICE, PASSWORD_KEY)
    except Exception:
        return None

    return Credentials(email, password) if email and password else None


def load_email() -> str:
    try:
        return keyring.get_password(SERVICE, EMAIL_KEY) or ""
    except Exception:
        return ""


def save_credentials(email: str, password: str) -> None:
    keyring.set_password(SERVICE, EMAIL_KEY, email.strip())
    keyring.set_password(SERVICE, PASSWORD_KEY, password)
