"""STRUKTURIRAN IZHOD, korak 2: čist zapisnik -> trije izdelki za stranko.

- povzetek + ključne točke (MeetingNotes)
- objava za družbena omrežja (Objava)
"""

import logging

from granova import llm
from granova.models import MeetingNotes, Objava

log = logging.getLogger(__name__)

NOTES_SYSTEM_PROMPT = """Si asistent za zapiske sestankov. Iz urejenega zapisnika izlušči
strukturirane zapiske v slovenščini: kratek naslov, povzetek (3-6 stavkov),
ključne točke, sprejete odločitve, naloge (z nosilcem in rokom, če sta omenjena)
ter imena udeležencev. Ne izmišljuj si informacij, ki jih v zapisniku ni —
prazni seznami so povsem sprejemljivi."""

OBJAVA_SYSTEM_PROMPT = """Si družbeni-mediji urednik. Iz zapisnika sestanka pripravi osnutek
objave za Instagram/Facebook v slovenščini — univerzalen, topel in profesionalen ton,
primeren za širšo javnost. Objava naj poudari, kar je bilo na sestanku najbolj
zanimivega ali koristnega za sledilce, BREZ internih/poslovno občutljivih podrobnosti
(številke, cene, interne odločitve). V predlogi dodaj ideje za hashtage in CTA."""


def generate(enhanced_minutes: str) -> dict:
    """Vrne {"notes": MeetingNotes, "objava": Objava}."""
    notes = llm.parse(NOTES_SYSTEM_PROMPT, enhanced_minutes, MeetingNotes)
    objava = llm.parse(OBJAVA_SYSTEM_PROMPT, enhanced_minutes, Objava)

    log.info(
        "Generate: %d ključnih točk, %d odločitev, %d nalog, objava %d znakov",
        len(notes.kljucne_tocke), len(notes.odlocitve), len(notes.naloge), len(objava.besedilo),
    )
    return {"notes": notes, "objava": objava}
