"""Zapis rezultata v Google Doc s tremi sekcijami.

Dokument: "<Naslov> — YYYY-MM-DD", vedno shranjen v eno skupno Drive mapo
(privzeto "Granola zapiski"; ime nastavljivo z docs_folder_name, obstoječo mapo
pa lahko izbereš z drive_folder_id). Sekcije: (1) povzetek + ključne točke,
(2) objava + predlogi, (3) transkript.
`build_requests` je čista funkcija (testabilna brez API-ja).
"""
from __future__ import annotations

import logging
from datetime import date

from granova.config import get_setting
from granova.models import MeetingResult

logger = logging.getLogger(__name__)

DEFAULT_DOCS_FOLDER = "Granola zapiski"

# folder_id po imenu mape, da ne iščemo po Drive ob vsakem klicu
_folder_cache: dict[str, str] = {}


def _u16len(text: str) -> int:
    """Docs API šteje indekse v UTF-16 enotah."""
    return len(text.encode("utf-16-le")) // 2


def _compose(result: MeetingResult) -> list[tuple[str, str | None]]:
    """Vrne seznam (odstavek, slog) — slog je HEADING_1/HEADING_2 ali None."""
    n = result.notes
    parts: list[tuple[str, str | None]] = []

    parts.append(("Povzetek in ključne točke", "HEADING_1"))
    parts.append((n.povzetek, None))
    if n.kljucne_tocke:
        parts.append(("Ključne točke", "HEADING_2"))
        parts.extend((f"• {t}", None) for t in n.kljucne_tocke)
    if n.odlocitve:
        parts.append(("Odločitve", "HEADING_2"))
        parts.extend((f"• {o}", None) for o in n.odlocitve)
    if n.naloge:
        parts.append(("Naloge", "HEADING_2"))
        for naloga in n.naloge:
            extra = ", ".join(x for x in [naloga.nosilec, naloga.rok] if x)
            parts.append((f"• {naloga.naloga}" + (f" ({extra})" if extra else ""), None))
    if n.udelezenci:
        parts.append((f"Udeleženci: {', '.join(n.udelezenci)}", None))

    parts.append(("Objava (osnutek)", "HEADING_1"))
    parts.append((result.objava.besedilo, None))
    if result.objava.predlogi:
        parts.append(("Predlogi", "HEADING_2"))
        parts.extend((f"• {p}", None) for p in result.objava.predlogi)

    parts.append(("Transkript", "HEADING_1"))
    parts.append((result.transcript, None))
    return parts


def build_requests(result: MeetingResult) -> list[dict]:
    """Sestavi batchUpdate zahteve: en insertText + slogi naslovov."""
    parts = _compose(result)
    full_text = "\n".join(text for text, _ in parts) + "\n"
    requests = [{"insertText": {"location": {"index": 1}, "text": full_text}}]

    index = 1
    for text, style in parts:
        length = _u16len(text)
        if style:
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": index, "endIndex": index + length},
                    "paragraphStyle": {"namedStyleType": style},
                    "fields": "namedStyleType",
                }
            })
        index += length + 1  # +1 za \n
    return requests


def doc_title(title: str, day: date | None = None) -> str:
    day = day or date.today()
    return f"{title} — {day.isoformat()}"


def get_or_create_folder(creds, name: str) -> str:
    """Vrne id skupne Drive mape z danim imenom; če je ni, jo ustvari.

    Z obsegom drive.file iskanje vidi samo mape, ki jih je ustvarila ta
    aplikacija — najdemo torej svojo mapo, ne uporabnikovih.
    """
    if name in _folder_cache:
        return _folder_cache[name]

    from googleapiclient.discovery import build

    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    safe_name = name.replace("'", "\\'")
    found = drive.files().list(
        q=(f"mimeType='application/vnd.google-apps.folder' "
           f"and name='{safe_name}' and trashed=false"),
        spaces="drive",
        fields="files(id,name)",
    ).execute().get("files", [])

    if found:
        folder_id = found[0]["id"]
    else:
        folder = drive.files().create(
            body={"name": name, "mimeType": "application/vnd.google-apps.folder"},
            fields="id",
        ).execute()
        folder_id = folder["id"]
        logger.info("Ustvarjena Drive mapa %r (%s)", name, folder_id)

    _folder_cache[name] = folder_id
    return folder_id


def folder_link(folder_id: str) -> str:
    return f"https://drive.google.com/drive/folders/{folder_id}"


def notes_folder_link(creds) -> str | None:
    """Povezava do skupne mape z zapiski; None, če je ni mogoče določiti.

    Po create_doc je mapa že v _folder_cache, zato brez dodatnega API klica.
    """
    try:
        folder_id = get_setting("drive_folder_id") or get_or_create_folder(
            creds, get_setting("docs_folder_name", DEFAULT_DOCS_FOLDER)
        )
        return folder_link(folder_id)
    except Exception:
        logger.exception("Povezave do mape ni bilo mogoče določiti")
        return None


def create_doc(creds, title: str, result: MeetingResult) -> str:
    """Ustvari Google Doc, ga napolni in premakne v skupno mapo. Vrne povezavo."""
    from googleapiclient.discovery import build

    docs = build("docs", "v1", credentials=creds, cache_discovery=False)
    doc = docs.documents().create(body={"title": doc_title(title)}).execute()
    doc_id = doc["documentId"]

    docs.documents().batchUpdate(
        documentId=doc_id, body={"requests": build_requests(result)}
    ).execute()

    try:
        folder_id = get_setting("drive_folder_id") or get_or_create_folder(
            creds, get_setting("docs_folder_name", DEFAULT_DOCS_FOLDER)
        )
        drive = build("drive", "v3", credentials=creds, cache_discovery=False)
        drive.files().update(
            fileId=doc_id, addParents=folder_id, removeParents="root", fields="id"
        ).execute()
    except Exception:
        logger.exception("Premik v Drive mapo ni uspel — dokument ostaja v korenu")

    return f"https://docs.google.com/document/d/{doc_id}/edit"
