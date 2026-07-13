"""Šifriranje skrivnosti na mirovanju (API ključ, Google token, client_secret).

Skrivnosti ostanejo v mapi `data/` (da jih izbris aplikacije odstrani skupaj z
njo), a so zašifrirane, tako da so za druge uporabnike, za kopijo mape ali za
drug računalnik neuporabne. Šifrirni ključ varuje operacijski sistem na
uporabnika:

- **Windows**: DPAPI — ključ (`data/secret.key`) odklene samo tvoj Windows
  račun na tem računalniku. Ob izbrisu mape izgine skupaj s šifriranimi datotekami.
- **macOS**: naključni ključ v login Keychain (storitev »Granova«).
- **drugje (razvoj/Linux)**: ključ v datoteki `data/secret.key` (brez OS zaščite,
  z opozorilom) — dovolj za razvoj, ni za produkcijo.

Aplikacija odklene sama, brez gesla, da lahko med Meet klicem deluje v ozadju.
Datoteke se berejo/pišejo prek `read_secret_text` / `write_secret_text`; stare
nešifrirane datoteke se ob branju prepoznajo in ob prvem zapisu prešifrirajo.
"""
from __future__ import annotations

import base64
import getpass
import logging
import subprocess
import sys
from pathlib import Path

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

_MARKER = b"GRANOVA-ENC1:"
_KEYCHAIN_SERVICE = "Granova"
_key_cache: bytes | None = None


def _key_file() -> Path:
    from granova.config import APP_DIR

    return APP_DIR / "secret.key"


# ---------- Windows DPAPI (šifriranje na uporabnika) ----------

def _dpapi(data: bytes, *, encrypt: bool) -> bytes:
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    buf = ctypes.create_string_buffer(data, len(data))  # ostane živ do klica
    blob_in = DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    blob_out = DATA_BLOB()
    func = ctypes.windll.crypt32.CryptProtectData if encrypt else ctypes.windll.crypt32.CryptUnprotectData
    CRYPTPROTECT_UI_FORBIDDEN = 0x01
    if not func(ctypes.byref(blob_in), None, None, None, None, CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(blob_out)):
        raise ctypes.WinError()
    try:
        out = ctypes.create_string_buffer(blob_out.cbData)
        ctypes.memmove(out, blob_out.pbData, blob_out.cbData)
        return out.raw
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def _win_key() -> bytes:
    path = _key_file()
    if path.exists():
        return _dpapi(base64.b64decode(path.read_text(encoding="ascii")), encrypt=False)
    key = Fernet.generate_key()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(base64.b64encode(_dpapi(key, encrypt=True)).decode("ascii"), encoding="ascii")
    return key


# ---------- macOS login Keychain ----------

def _mac_key() -> bytes:
    account = getpass.getuser()
    found = subprocess.run(
        ["security", "find-generic-password", "-a", account, "-s", _KEYCHAIN_SERVICE, "-w"],
        capture_output=True, text=True,
    )
    if found.returncode == 0 and found.stdout.strip():
        return found.stdout.strip().encode("ascii")
    key = Fernet.generate_key()
    subprocess.run(
        ["security", "add-generic-password", "-U", "-a", account, "-s", _KEYCHAIN_SERVICE,
         "-w", key.decode("ascii")],
        check=True, capture_output=True, text=True,
    )
    return key


# ---------- rezerva (razvoj/Linux, brez OS zaščite) ----------

def _fallback_key() -> bytes:
    path = _key_file()
    if path.exists():
        return path.read_text(encoding="ascii").encode("ascii")
    logger.warning(
        "Šifrirni ključ ni zaščiten z OS (platforma %s) — skrivnosti so šifrirane, "
        "a ključ leži poleg njih. Za produkcijo uporabi Windows ali macOS.", sys.platform
    )
    key = Fernet.generate_key()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(key.decode("ascii"), encoding="ascii")
    return key


def _get_key() -> bytes:
    global _key_cache
    if _key_cache is None:
        if sys.platform == "win32":
            _key_cache = _win_key()
        elif sys.platform == "darwin":
            _key_cache = _mac_key()
        else:
            _key_cache = _fallback_key()
    return _key_cache


# ---------- javni API ----------

def protect(text: str) -> str:
    """Vrne šifrirano besedilo (z oznako), primerno za zapis v datoteko."""
    token = Fernet(_get_key()).encrypt(text.encode("utf-8"))
    return (_MARKER + token).decode("ascii")


def unprotect(blob: str) -> str:
    """Odšifrira besedilo; nešifrirano (staro) besedilo vrne nespremenjeno."""
    raw = blob.encode("utf-8") if isinstance(blob, str) else blob
    if not raw.startswith(_MARKER):
        return raw.decode("utf-8")  # stara, še nešifrirana datoteka
    return Fernet(_get_key()).decrypt(raw[len(_MARKER):]).decode("utf-8")


def read_secret_text(path: Path) -> str | None:
    """Prebere in odšifrira datoteko; None, če ne obstaja."""
    if not path.exists():
        return None
    return unprotect(path.read_text(encoding="utf-8"))


def write_secret_text(path: Path, text: str) -> None:
    """Šifrirano zapiše besedilo v datoteko (ustvari mapo, če je treba)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(protect(text), encoding="utf-8")
