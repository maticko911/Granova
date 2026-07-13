"""Google OAuth (namizni tok) + predpomnjenje žetona.

Prvič odpre brskalnik za prijavo; žeton se shrani v APP_DIR/token.json (mapa
`data/` znotraj aplikacije) in se nato tiho osvežuje. Zahteva client_secret.json
(OAuth Desktop credentials iz Google Cloud Console) v isti mapi.
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
    """Vrne veljavne Google poverilnice; po potrebi sproži prijavo v brskalniku.

    Žeton in client_secret sta na disku šifrirana (glej secrets_store) in se
    odšifrirata le v pomnilnik — nešifrirana nikoli ne pristaneta na disku.
    """
    import json

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    from granova.secrets_store import read_secret_text, write_secret_text

    creds = None
    token_text = read_secret_text(TOKEN_PATH)
    if token_text:
        creds = Credentials.from_authorized_user_info(json.loads(token_text), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            logger.warning("Osvežitev žetona ni uspela — potrebna bo nova prijava")
            creds = None

    if not creds or not creds.valid:
        secret_text = read_secret_text(CLIENT_SECRET_PATH)
        if not secret_text:
            raise RuntimeError(
                f"Manjka {CLIENT_SECRET_PATH}. V Google Cloud Console ustvari OAuth "
                "Desktop credentials in shrani JSON na to pot."
            )
        flow = InstalledAppFlow.from_client_config(json.loads(secret_text), SCOPES)
        creds = flow.run_local_server(port=0)
        write_secret_text(TOKEN_PATH, creds.to_json())

    return creds
