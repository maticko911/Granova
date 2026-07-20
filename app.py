"""Granova — vstopna točka.

Miruje v sistemski vrstici; ko je zaznan Google Meet klic, odpre živo okno in
začne snemati. Ob koncu klica transkript spelje skozi tekstovni cevovod
(Faza 1) in rezultat zapiše v Google Doc (ali lokalni Markdown, če Google še
ni nastavljen). Nato nazaj v mirovanje. Ne snema in ne kliče API-jev, ko ni klica.

Zagon:  python app.py
"""
from __future__ import annotations

import faulthandler
import logging
import logging.handlers
import queue
import sys
import threading
import tkinter as tk

from granova import autostart, notify, pipeline, single_instance, state, trust, updater
from granova.config import APP_DIR
from granova.live_window import LiveWindow
from granova.meet_detector import MeetDetector
from granova.recorder import Recorder

logger = logging.getLogger("granova.app")

LOG_PATH = APP_DIR / "granova.log"
_configured = False
_crash_file = None  # ostati mora odprt, dokler faulthandler piše vanj


def _configure_diagnostics() -> None:
    """Dnevnik v datoteko + globalni lovilci izjem — da noben tih zlom ne izgine.

    Pri samodejnem zagonu prek pythonw ni konzole: brez tega gre vsaka sledilna
    napaka v nič in aplikacija se navidez »samo zapre«. Zdaj vse pristane v
    data/granova.log, nativni zlomi pa v data/granova-crash.log.
    """
    global _configured, _crash_file
    if _configured:
        return
    _configured = True
    APP_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)
    if sys.stderr is not None:  # konzola obstaja le pri python (ne pythonw)
        stream = logging.StreamHandler()
        stream.setFormatter(fmt)
        root.addHandler(stream)

    try:
        _crash_file = open(APP_DIR / "granova-crash.log", "a", encoding="utf-8")
        faulthandler.enable(file=_crash_file)
    except Exception:
        logger.warning("faulthandler ni bilo mogoče vključiti", exc_info=True)

    def _log_uncaught(exc_type, exc, tb):
        logger.critical("Neujeta izjema", exc_info=(exc_type, exc, tb))

    sys.excepthook = _log_uncaught

    def _log_thread(args):
        name = args.thread.name if args.thread else "?"
        logger.critical(
            "Neujeta izjema v niti %s", name,
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    threading.excepthook = _log_thread


def _tray_image(color: str):
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill=color)
    return img


class GranovaApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()  # glavno okno je skrito; vidna so le živa okna
        self.root.report_callback_exception = lambda *a: logger.critical(
            "Napaka v tkinter callbacku", exc_info=a
        )

        self._events: queue.Queue = queue.Queue()
        self._window: LiveWindow | None = None
        self._recorder: Recorder | None = None
        self._meeting_name = ""
        self._finalizing = False
        self._last_link: str | None = None
        self._last_folder: str | None = None

        self.detector = MeetDetector(
            on_call_started=lambda name: self._events.put(("call_started", name)),
            on_call_ended=lambda: self._events.put(("stop_requested", None)),
        )
        self.tray = self._build_tray()

    # ---------- zagon ----------

    def run(self) -> None:
        trust.install()  # zaupaj sistemski certifikatni shrambi (protivirusno HTTPS skeniranje)
        self._lock = single_instance.acquire()
        if self._lock is None:
            logger.info("Granova že teče — druga instanca se umika")
            return
        APP_DIR.mkdir(parents=True, exist_ok=True)
        try:
            if autostart.refresh():
                logger.info("Samodejni zagon: vnos je kazal na staro mapo — posodobljen")
        except Exception:
            logger.warning("Samodejnega zagona ni bilo mogoče osvežiti", exc_info=True)
        self.tray.run_detached()
        self.detector.start()
        threading.Thread(target=self._retry_pending_jobs, daemon=True).start()
        self.root.after(200, self._pump)
        logger.info("Granova pripravljena — čakam na Google Meet klic")
        self.root.mainloop()

    def _build_tray(self):
        import pystray

        return pystray.Icon(
            "granova",
            _tray_image("#9e9e9e"),
            "Granova — čakam na Meet klic",
            menu=pystray.Menu(
                pystray.MenuItem("Odpri zadnji dokument", self._open_last, enabled=lambda i: bool(self._last_link)),
                pystray.MenuItem("Odpri mapo z zapiski", self._open_folder, enabled=lambda i: bool(self._last_folder)),
                pystray.MenuItem(
                    "Samodejni zagon ob prijavi",
                    self._toggle_autostart,
                    checked=lambda i: autostart.is_enabled(),
                ),
                pystray.MenuItem("Izhod", lambda: self._events.put(("quit", None))),
            ),
        )

    def _open_last(self) -> None:
        if self._last_link:
            import webbrowser

            webbrowser.open(self._last_link)

    def _open_folder(self) -> None:
        if self._last_folder:
            import webbrowser

            webbrowser.open(self._last_folder)

    def _toggle_autostart(self, icon, item) -> None:
        try:
            if autostart.is_enabled():
                autostart.disable()
            else:
                autostart.enable()
        except Exception:
            logger.exception("Preklop samodejnega zagona ni uspel")

    # ---------- dogodkovna zanka (tk nit) ----------

    def _pump(self) -> None:
        try:
            while True:
                try:
                    kind, payload = self._events.get_nowait()
                except queue.Empty:
                    break
                if kind == "call_started":
                    self._start_session(payload)
                elif kind == "stop_requested":
                    self._finalize()
                elif kind == "quit":
                    self._quit()
                    return
        except Exception:
            # Napaka pri obdelavi dogodka NE sme ubiti zanke: brez tega se
            # `after` spodaj nikoli ne prestavi in Granova tiho neha odzivati
            # (navidez teče, v resnici ne sliši več ne klicev ne menija).
            logger.exception("Napaka pri obdelavi dogodka — Granova teče naprej")
        self.root.after(200, self._pump)

    def _start_session(self, meeting_name: str) -> None:
        if self._recorder is not None:
            return  # seja že teče
        self._meeting_name = meeting_name
        self._finalizing = False
        window = LiveWindow(self.root, on_stop=lambda: self._events.put(("stop_requested", None)))
        window.set_title(meeting_name)
        recorder = Recorder(
            on_chunk=window.append_chunk,
            on_silence_timeout=lambda: self._events.put(("stop_requested", None)),
        )
        try:
            recorder.start()
        except Exception as exc:
            # Zajem ni stekel (npr. pomočnik za sistemski zvok ni preveden).
            # Povej v oknu in ostani v mirovanju: če bi _recorder ostal
            # nastavljen, se noben naslednji klic ne bi več začel.
            logger.exception("Snemanja ni bilo mogoče začeti")
            window.show_error(f"Snemanje se ni začelo: {exc}")
            return
        self._window = window
        self._recorder = recorder
        self.tray.icon = _tray_image("#e05252")
        self.tray.title = f"Granova — snemam: {meeting_name}"
        threading.Thread(target=self._enrich_title, daemon=True).start()

    def _enrich_title(self) -> None:
        """Koledar samo obogati naslov — brez njega vse deluje naprej."""
        try:
            from granova.auth import TOKEN_PATH, get_credentials
            from granova.calendar_watcher import fetch_current_event_title

            if not TOKEN_PATH.exists():
                return  # Google še ni prijavljen — ne odpiraj brskalnika sredi klica
            title = fetch_current_event_title(get_credentials())
            if title and self._window:
                self._window.set_title(title)
        except Exception:
            logger.exception("Obogatitev naslova ni uspela")

    def _finalize(self) -> None:
        if self._recorder is None or self._finalizing:
            return
        self._finalizing = True
        window, recorder = self._window, self._recorder
        title = window.get_title() or self._meeting_name or "Sestanek"
        window.show_processing()
        self.tray.icon = _tray_image("#d0a94b")
        self.tray.title = "Granova — pripravljam zapiske"
        threading.Thread(target=self._process, args=(recorder, window, title), daemon=True).start()
        self._recorder = None
        self._window = None

    # ---------- obdelava (delovna nit) ----------

    def _process(self, recorder: Recorder, window: LiveWindow, title: str) -> None:
        try:
            transcript = recorder.stop()
            if not transcript.strip():
                window.show_error("Ni zaznanega govora — zapiski niso bili narejeni")
                return
            job_path = state.save_job(transcript, title)
            link, folder = self._make_notes(transcript, title)
            if link is None:
                window.show_error("Premalo vsebine za zapiske")
            else:
                self._last_link = link
                self._last_folder = folder
                window.show_done(link, folder)
                notify.notify_saved(
                    "Zapiski so shranjeni — odpri iz okna ali sistemske vrstice.",
                    tray=self.tray,
                )
            state.delete_job(job_path)
        except Exception:
            logger.exception("Obdelava ni uspela — opravilo ostaja v vrsti za ponovni poskus")
            window.show_error("Napaka pri shranjevanju — Granova teče naprej in poskusi znova ob naslednjem zagonu")
        finally:
            self.tray.icon = _tray_image("#9e9e9e")
            self.tray.title = "Granova — čakam na Meet klic"

    def _make_notes(self, transcript: str, title: str, raw_notes: str = "") -> tuple[str | None, str | None]:
        """Cevovod + zapis. Vrne (povezava do dokumenta, povezava do mape).

        (None, None) če je gate zavrnil; ob lokalnem Markdown zapisu je mapa None.
        """
        result = pipeline.process_meeting(transcript, raw_notes)
        if result is None:
            return None, None
        try:
            from granova.auth import get_credentials
            from granova.docs_writer import create_doc, notes_folder_link

            creds = get_credentials()
            link = create_doc(creds, title, result)
            return link, notes_folder_link(creds)
        except Exception:
            logger.exception("Google Doc ni uspel — shranim lokalni Markdown")
            return self._write_local_markdown(title, result), None

    @staticmethod
    def _write_local_markdown(title: str, result) -> str:
        from granova.docs_writer import doc_title

        notes_dir = APP_DIR / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        safe = "".join(c for c in doc_title(title) if c not in '\\/:*?"<>|')
        path = notes_dir / f"{safe}.md"
        n = result.notes
        lines = [f"# {n.naslov}", "", "## Povzetek", n.povzetek, "", "## Ključne točke"]
        lines += [f"- {t}" for t in n.kljucne_tocke]
        if n.odlocitve:
            lines += ["", "## Odločitve"] + [f"- {o}" for o in n.odlocitve]
        if n.naloge:
            lines += ["", "## Naloge"] + [
                f"- {t.naloga}" + (f" ({', '.join(x for x in [t.nosilec, t.rok] if x)})" if t.nosilec or t.rok else "")
                for t in n.naloge
            ]
        lines += ["", "## Objava (osnutek)", result.objava.besedilo]
        lines += ["", "## Transkript", result.transcript]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path.as_uri()

    def _retry_pending_jobs(self) -> None:
        for path, job in state.load_jobs():
            try:
                link, folder = self._make_notes(job["transcript"], job.get("title", "Sestanek"), job.get("raw_notes", ""))
                state.delete_job(path)
                if link:
                    self._last_link = link
                    self._last_folder = folder
                    logger.info("Čakajoče opravilo dokončano: %s", link)
                    notify.notify_saved(
                        "Čakajoči zapiski so shranjeni — odpri iz sistemske vrstice.",
                        tray=self.tray,
                    )
            except Exception:
                logger.exception("Ponovni poskus opravila ni uspel: %s", path)

    def _quit(self) -> None:
        self.detector.stop()
        if self._recorder:
            try:
                self._recorder.stop()
            except Exception:
                pass
        self.tray.stop()
        self.root.quit()


if __name__ == "__main__":
    _configure_diagnostics()
    updater.self_update()  # prenese novo kodo z GitHuba in se znova zažene (če je novost)
    trust.install()
    try:
        GranovaApp().run()
    except Exception:
        logger.critical("Granova se je nepričakovano ustavila", exc_info=True)
        raise
