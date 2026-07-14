"""Zaupanje sistemski certifikatni shrambi.

Nekateri protivirusni programi in korporativni požarni zidovi (npr. Norton
"Web/Mail Shield", ESET, Kaspersky) skenirajo HTTPS promet: povezavo prestrežejo
in jo znova podpišejo z lastnim korenskim certifikatom. Ta koren je nameščen v
sistemski certifikatni shrambi Windows/macOS, NI pa v vgrajenem seznamu (certifi),
ki ga privzeto uporabljajo openai/httpx in Google knjižnice. Posledica: vsak klic
na OpenAI in Google spodleti s `CERTIFICATE_VERIFY_FAILED` in aplikacija ne more
narediti zapiskov ne odpreti Google dokumenta.

`install()` s pomočjo `truststore` preusmeri preverjanje certifikatov na sistemsko
shrambo, kjer tak koren obstaja — s čimer promet spet steče. Kliči ga čim prej,
pred prvim omrežnim klicem. Če truststore ni na voljo, tiho odneha (obnašanje
ostane kot prej).
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_installed = False


def install() -> None:
    """Preveri certifikate prek sistemske shrambe (idempotentno, nikoli ne vrže)."""
    global _installed
    if _installed:
        return
    try:
        import truststore

        truststore.inject_into_ssl()
        _installed = True
        logger.info("Zaupanje sistemski certifikatni shrambi (truststore) vključeno")
    except Exception:
        logger.warning(
            "truststore ni na voljo — če protivirusni program skenira HTTPS, "
            "lahko klici na OpenAI/Google spodletijo",
            exc_info=True,
        )
