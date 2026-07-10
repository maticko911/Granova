"""Pydantic modeli — lepilo med LLM izhodi in ostalim sistemom."""

from pydantic import BaseModel, Field


class MeetingGate(BaseModel):
    """Ocena, ali je transkript smiseln sestanek (gate vzorec)."""

    is_meaningful: bool = Field(description="Ali transkript vsebuje smiseln sestanek")
    confidence_score: float = Field(description="Zaupanje v oceno, od 0 do 1")


class ActionItem(BaseModel):
    naloga: str = Field(description="Kaj je treba narediti")
    nosilec: str | None = Field(default=None, description="Kdo je zadolžen")
    rok: str | None = Field(default=None, description="Do kdaj")


class Objava(BaseModel):
    """Osnutek objave za družbena omrežja (IG/FB)."""

    besedilo: str = Field(description="Besedilo objave, pripravljeno za kopiranje")
    predlogi: list[str] = Field(description="Predlogi hashtagov, CTA-jev, variacij")


class MeetingNotes(BaseModel):
    """Strukturirani zapiski sestanka v slovenščini."""

    naslov: str = Field(description="Kratek naslov sestanka")
    povzetek: str = Field(description="Kratek povzetek sestanka, 3-6 stavkov")
    kljucne_tocke: list[str] = Field(description="Ključne točke pogovora")
    odlocitve: list[str] = Field(description="Sprejete odločitve")
    naloge: list[ActionItem] = Field(description="Dogovorjene naloge")
    udelezenci: list[str] = Field(description="Imena omenjenih udeležencev")


class MeetingResult(BaseModel):
    """Končni rezultat cevovoda — vse, kar gre kasneje v Google Doc."""

    notes: MeetingNotes
    objava: Objava
    enhanced_minutes: str
    transcript: str
