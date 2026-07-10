import sys
import types
from datetime import date

import pytest

import granova.docs_writer as docs_writer
from granova.docs_writer import build_requests, create_doc, doc_title, get_or_create_folder
from granova.models import ActionItem, MeetingNotes, MeetingResult, Objava


def sample_result() -> MeetingResult:
    return MeetingResult(
        notes=MeetingNotes(
            naslov="Marketinški sestanek",
            povzetek="Dogovorili smo se o jesenski kampanji.",
            kljucne_tocke=["Katalog: 700 izvodov", "Dogodek 15. oktobra"],
            odlocitve=["Potrjen proračun"],
            naloge=[ActionItem(naloga="Priprava kataloga", nosilec="Marko", rok="1. 9.")],
            udelezenci=["Marko", "Nina"],
        ),
        objava=Objava(besedilo="Jeseni prihaja nekaj velikega! 🍂", predlogi=["#jesen"]),
        enhanced_minutes="UREJEN ZAPISNIK ...",
        transcript="celoten transkript šžč",
    )


def test_doc_title_format():
    assert doc_title("Sestanek", date(2026, 7, 9)) == "Sestanek — 2026-07-09"


def test_build_requests_single_insert_plus_heading_styles():
    requests = build_requests(sample_result())

    inserts = [r for r in requests if "insertText" in r]
    styles = [r for r in requests if "updateParagraphStyle" in r]
    assert len(inserts) == 1
    text = inserts[0]["insertText"]["text"]

    # vse tri sekcije so v besedilu
    for section in ["Povzetek in ključne točke", "Objava (osnutek)", "Transkript"]:
        assert section in text
    assert "celoten transkript šžč" in text
    assert "Priprava kataloga" in text

    # trije HEADING_1 + podnaslovi
    h1 = [s for s in styles if s["updateParagraphStyle"]["paragraphStyle"]["namedStyleType"] == "HEADING_1"]
    assert len(h1) == 3


def test_heading_ranges_point_at_heading_text():
    requests = build_requests(sample_result())
    # Docs API indeksira v UTF-16 enotah (emoji 🍂 šteje 2) — preveri v UTF-16
    u16 = requests[0]["insertText"]["text"].encode("utf-16-le")
    for r in requests[1:]:
        rng = r["updateParagraphStyle"]["range"]
        # indeks 1 v Docs = začetek besedila -> odmik -1
        segment = u16[(rng["startIndex"] - 1) * 2 : (rng["endIndex"] - 1) * 2].decode("utf-16-le")
        assert segment in {
            "Povzetek in ključne točke", "Ključne točke", "Odločitve", "Naloge",
            "Objava (osnutek)", "Predlogi", "Transkript",
        }


# --- Lažni Google servisi (brez omrežja) ---------------------------------

class _Exec:
    def __init__(self, result):
        self._result = result

    def execute(self):
        return self._result


class FakeDrive:
    """Posnema drive.files().list/create/update verige."""

    def __init__(self, existing_folders=None):
        self.existing_folders = existing_folders or []
        self.list_calls = 0
        self.created = []
        self.updates = []

    def files(self):
        return self

    def list(self, **kwargs):
        self.list_calls += 1
        self.last_query = kwargs.get("q", "")
        return _Exec({"files": self.existing_folders})

    def create(self, body=None, fields=None):
        self.created.append(body)
        return _Exec({"id": "new-folder-id"})

    def update(self, **kwargs):
        self.updates.append(kwargs)
        return _Exec({"id": kwargs.get("fileId")})


class FakeDocs:
    def __init__(self):
        self.created_titles = []
        self.batch_updates = []

    def documents(self):
        return self

    def create(self, body=None):
        self.created_titles.append(body["title"])
        return _Exec({"documentId": "doc-123"})

    def batchUpdate(self, documentId=None, body=None):
        self.batch_updates.append((documentId, body))
        return _Exec({})


@pytest.fixture
def google_services(monkeypatch):
    """Podtakne googleapiclient.discovery.build in izprazni predpomnilnik mape."""
    docs = FakeDocs()
    drive = FakeDrive()

    def fake_build(service, version, credentials=None, cache_discovery=False):
        return docs if service == "docs" else drive

    mod = types.ModuleType("googleapiclient.discovery")
    mod.build = fake_build
    pkg = types.ModuleType("googleapiclient")
    pkg.discovery = mod
    monkeypatch.setitem(sys.modules, "googleapiclient", pkg)
    monkeypatch.setitem(sys.modules, "googleapiclient.discovery", mod)

    monkeypatch.setattr(docs_writer, "_folder_cache", {})
    monkeypatch.setattr(docs_writer, "get_setting", lambda name, default=None: default)
    return docs, drive


def test_get_or_create_folder_finds_existing(google_services):
    _, drive = google_services
    drive.existing_folders = [{"id": "existing-id", "name": "Granola zapiski"}]

    folder_id = get_or_create_folder(creds=None, name="Granola zapiski")

    assert folder_id == "existing-id"
    assert drive.created == []
    assert "Granola zapiski" in drive.last_query


def test_get_or_create_folder_creates_when_missing(google_services):
    _, drive = google_services

    folder_id = get_or_create_folder(creds=None, name="Granola zapiski")

    assert folder_id == "new-folder-id"
    assert len(drive.created) == 1
    assert drive.created[0]["mimeType"] == "application/vnd.google-apps.folder"


def test_get_or_create_folder_is_memoized(google_services):
    _, drive = google_services

    first = get_or_create_folder(creds=None, name="Granola zapiski")
    second = get_or_create_folder(creds=None, name="Granola zapiski")

    assert first == second
    assert drive.list_calls == 1  # drugi klic ne gre na API


def test_create_doc_files_doc_into_shared_folder(google_services):
    docs, drive = google_services
    drive.existing_folders = [{"id": "folder-1", "name": "Granola zapiski"}]

    link = create_doc(creds=None, title="Sestanek", result=sample_result())

    assert link == "https://docs.google.com/document/d/doc-123/edit"
    assert len(docs.created_titles) == 1
    assert docs.created_titles[0].startswith("Sestanek — ")
    assert len(docs.batch_updates) == 1

    assert len(drive.updates) == 1
    move = drive.updates[0]
    assert move["fileId"] == "doc-123"
    assert move["addParents"] == "folder-1"
    assert move["removeParents"] == "root"
