"""PROMPT CHAINING, korak 1: surov transkript + uporabnikovi zapiski -> čist zapisnik.

Granolina osnovna ideja: uporabnikovi surovi zapiski so prvorazredni vhod,
transkript jih dopolni in razširi.
"""

import logging

from granova import llm

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """Si izkušen zapisnikar. Iz surovega transkripta sestanka (in morebitnih
uporabnikovih zapiskov) sestavi čist, urejen zapisnik v slovenščini.

Pravila:
- Piši v knjižni slovenščini, jasno in jedrnato.
- Odstrani mašila, ponavljanja in nepomembne vložke.
- Ohrani VSE vsebinske informacije: teme, argumente, odločitve, naloge, roke, imena.
- Če so priloženi uporabnikovi zapiski, jih obravnavaj kot prednostne poudarke —
  vsebino iz njih obvezno vključi in jo dopolni s podrobnostmi iz transkripta.
- Strukturiraj po temah s kratkimi naslovi."""


def enhance(transcript: str, raw_notes: str = "") -> str:
    user = f"TRANSKRIPT SESTANKA:\n{transcript}"
    if raw_notes.strip():
        user += f"\n\nUPORABNIKOVI ZAPISKI (prednostni poudarki):\n{raw_notes}"

    minutes = llm.complete(SYSTEM_PROMPT, user)
    log.info("Enhance: zapisnik dolg %d znakov", len(minutes))
    return minutes
