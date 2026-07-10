"""Google OAuth (namizni tok) + predpomnjenje žetona.

Prvič odpre brskalnik za prijavo; žeton se shrani v %APPDATA%\\Granola\\token.json
in se nato tiho osvežuje. Zahteva client_secret.json (OAuth Desktop credentials
iz Google Cloud Console) v isti mapi.
"""
from __future__ import annotations

import logging

from granova.config import APP_DIR

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]

TOKEN_PATH = APP_DIR / "token.json"
CLIENT_SECRET_PATH = APP_DIR / "client_secret.json"


def get_credentials():
    """Vrne veljavne Google poverilnice; po potrebi sproži prijavo v brskalniku."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            logger.warning("Osvežitev žetona ni uspela — potrebna bo nova prijava")
            creds = None

    if not creds or not creds.valid:
        if not CLIENT_SECRET_PATH.exists():
            raise RuntimeError(
                f"Manjka {CLIENT_SECRET_PATH}. V Google Cloud Console ustvari OAuth "
                "Desktop credentials in shrani JSON na to pot."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), SCOPES)
        creds = flow.run_local_server(port=0)
        APP_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return creds
