"""Samoposodobitev iz GitHuba ob zagonu.

Stranka je aplikacijo namestila s `git clone`, zato je GitHub že brezplačen
distribucijski kanal — manjka le, da nova koda dejansko pride na njen računalnik.
Ob vsakem zagonu `self_update()` potihoma preveri GitHub in prenese novo različico;
če se je koda posodobila, se proces znova zažene z novo kodo. Stranka ne naredi nič.

Varovalke (nobena posodobitev ne sme pokvariti zagona ali uničiti dela):
  * Brez interneta / GitHub nedosegljiv → posodobitev se preskoči, zažene se
    obstoječa različica (git klici imajo časovno omejitev).
  * Posodobi se LE, če je delovna kopija čista (`git status --porcelain` prazen).
    Tako razvijalčev računalnik z nezapisanimi spremembami nikoli ne povozimo.
  * Uporabi se `pull --ff-only` — nikoli `reset --hard`; če veje ni mogoče
    previti naprej (npr. lokalni commiti), se posodobitev varno preskoči.
  * `data/` (žetoni, ključi) je v `.gitignore`, zato ga posodobitev ne dotakne.
  * Enkratni okoljski zastavici prepreči morebitno zanko ponovnih zagonov.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("granova.updater")

# Ko se proces po posodobitvi znova zažene, to zastavico postavimo, da druga
# runda posodobitve ne teče (varovalka proti zanki ponovnih zagonov).
_DONE_ENV = "GRANOVA_SELFUPDATE_DONE"
# Razvijalec lahko samoposodobitev izklopi (npr. med delom na kodi).
_DISABLE_ENV = "GRANOVA_NO_SELFUPDATE"

_GIT_TIMEOUT = 30  # sekund na git klic — mrežni zastoj ne sme zamrzniti zagona


def _repo_dir() -> Path:
    """Koren repozitorija (mapa z app.py)."""
    return Path(__file__).resolve().parent.parent


def _git(args: list[str], repo: Path) -> subprocess.CompletedProcess | None:
    """Zažene git ukaz v mapi repozitorija. Vrne rezultat ali None ob napaki.

    Na Windows prepreči utrip konzolnega okna (CREATE_NO_WINDOW).
    """
    kwargs: dict = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT,
            **kwargs,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.info("git %s ni uspel: %s", " ".join(args), exc)
        return None


def _ok(proc: subprocess.CompletedProcess | None) -> bool:
    return proc is not None and proc.returncode == 0


def _rev(repo: Path, ref: str) -> str | None:
    proc = _git(["rev-parse", ref], repo)
    return proc.stdout.strip() if _ok(proc) else None


def self_update() -> None:
    """Prenese novo kodo z GitHuba in znova zažene proces, če je bila posodobljena.

    Ob normalnem stanju (brez novosti, brez interneta ali nečista kopija) se tiho
    vrne in zagon steče naprej. Ob uspešni posodobitvi se ne vrne — proces se
    zamenja z novim (os.execv).
    """
    if os.environ.get(_DONE_ENV) or os.environ.get(_DISABLE_ENV):
        return
    if shutil.which("git") is None:
        return  # ni gita (npr. namestitev iz ZIP-a) — ni kaj posodobiti

    repo = _repo_dir()
    if not (repo / ".git").exists():
        return  # ni git kopija

    # Posodobi le čisto delovno kopijo — nezapisanih sprememb nikoli ne povozimo.
    status = _git(["status", "--porcelain"], repo)
    if not _ok(status):
        return
    if status.stdout.strip():
        logger.info("Delovna kopija ni čista — samoposodobitev preskočena")
        return

    if not _ok(_git(["fetch", "--quiet", "origin"], repo)):
        return  # najverjetneje brez interneta — zaženi obstoječo različico

    local = _rev(repo, "HEAD")
    remote = _rev(repo, "@{u}")
    if not local or not remote or local == remote:
        return  # ni upstreama ali smo že posodobljeni

    logger.info("Nova različica na GitHubu (%s → %s) — posodabljam", local[:7], remote[:7])
    pull = _git(["pull", "--ff-only", "--quiet", "origin"], repo)
    if not _ok(pull):
        logger.info("Previjanje naprej ni mogoče — samoposodobitev preskočena")
        return

    # Če so se spremenile odvisnosti, jih dokup pred ponovnim zagonom.
    if _requirements_changed(repo, local, remote):
        _pip_install(repo)

    logger.info("Posodobljeno na %s — ponovni zagon z novo kodo", remote[:7])
    _reexec(repo)


def _requirements_changed(repo: Path, old: str, new: str) -> bool:
    diff = _git(["diff", "--name-only", old, new], repo)
    if not _ok(diff):
        return True  # ne vemo zagotovo → raje dokup odvisnosti
    return any(line.strip() == "requirements.txt" for line in diff.stdout.splitlines())


def _pip_install(repo: Path) -> None:
    req = repo / "requirements.txt"
    if not req.exists():
        return
    kwargs: dict = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(req)],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=600,
            **kwargs,
        )
        logger.info("Odvisnosti posodobljene")
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.info("Namestitev odvisnosti ni uspela: %s", exc)


def _reexec(repo: Path) -> None:
    """Zamenja tekoči proces z novim zagonom app.py (že posodobljena koda).

    Enkratna zastavica prepreči, da bi znova zagnani proces spet posodabljal.
    """
    os.environ[_DONE_ENV] = "1"
    app = str(repo / "app.py")
    try:
        os.execv(sys.executable, [sys.executable, app])
    except OSError as exc:
        # Če ponovni zagon spodleti, ne obtiči — nova koda se uveljavi ob
        # naslednjem zagonu, obstoječa pa steče naprej zdaj.
        logger.warning("Ponovni zagon po posodobitvi ni uspel: %s", exc)
