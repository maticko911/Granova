"""Živo okno med klicem (kot Granola / Whisper Flow).

Majhno always-on-top okno v kotu zaslona: statusna pika, pretečeni čas, drseči
živi transkript, polje za naslov in gumb Ustavi. Posodobitve prihajajo iz
delovnih niti prek vrste (queue) — tkinter se dotika samo glavna nit
(prek `after` zanke), zato je vse nitno varno.
"""
from __future__ import annotations

import queue
import time
import tkinter as tk
from tkinter import scrolledtext

BG = "#1e1e1e"
FG = "#e8e8e8"
ACCENT_REC = "#e05252"
ACCENT_OK = "#5cb85c"
ACCENT_WAIT = "#d0a94b"


class LiveWindow:
    """En primerek na sejo. Ustvari se v glavni (tk) niti."""

    def __init__(self, root: tk.Tk, on_stop) -> None:
        self._on_stop = on_stop
        self._queue: queue.Queue = queue.Queue()
        self._start_time = time.time()
        self._stopped = False

        self._win = tk.Toplevel(root)
        self._win.title("Granova")
        self._win.attributes("-topmost", True)
        self._win.configure(bg=BG)
        self._win.geometry(self._corner_geometry(width=380, height=260))
        self._win.protocol("WM_DELETE_WINDOW", self._handle_stop)

        header = tk.Frame(self._win, bg=BG)
        header.pack(fill="x", padx=10, pady=(8, 4))
        self._dot = tk.Label(header, text="●", fg=ACCENT_REC, bg=BG, font=("Segoe UI", 12))
        self._dot.pack(side="left")
        self._status = tk.Label(header, text="Snemam", fg=FG, bg=BG, font=("Segoe UI", 10, "bold"))
        self._status.pack(side="left", padx=(4, 0))
        self._timer = tk.Label(header, text="0:00", fg=FG, bg=BG, font=("Segoe UI", 10))
        self._timer.pack(side="right")

        self._title_var = tk.StringVar()
        title_entry = tk.Entry(
            self._win, textvariable=self._title_var, bg="#2a2a2a", fg=FG,
            insertbackground=FG, relief="flat", font=("Segoe UI", 10),
        )
        title_entry.pack(fill="x", padx=10, pady=(0, 6), ipady=3)

        self._text = scrolledtext.ScrolledText(
            self._win, wrap="word", bg="#252525", fg=FG, relief="flat",
            font=("Segoe UI", 9), state="disabled", height=8,
        )
        self._text.pack(fill="both", expand=True, padx=10)

        footer = tk.Frame(self._win, bg=BG)
        footer.pack(fill="x", padx=10, pady=8)
        self._link_label = tk.Label(footer, text="", fg="#6fa8dc", bg=BG, cursor="hand2", font=("Segoe UI", 9, "underline"))
        self._stop_btn = tk.Button(
            footer, text="Ustavi", command=self._handle_stop,
            bg="#3a3a3a", fg=FG, relief="flat", padx=14, pady=3,
        )
        self._stop_btn.pack(side="right")

        self._win.after(200, self._tick)

    @staticmethod
    def _corner_geometry(width: int, height: int) -> str:
        root = tk._default_root
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = screen_w - width - 20
        y = screen_h - height - 80
        return f"{width}x{height}+{x}+{y}"

    # ---- klici iz delovnih niti (nitno varni) ----

    def set_title(self, title: str) -> None:
        self._queue.put(("title", title))

    def append_chunk(self, text: str) -> None:
        self._queue.put(("chunk", text))

    def show_processing(self) -> None:
        self._queue.put(("status", ("Pripravljam zapiske…", ACCENT_WAIT)))

    def show_done(self, doc_link: str | None) -> None:
        self._queue.put(("done", doc_link))

    def show_error(self, message: str) -> None:
        self._queue.put(("status", (message, ACCENT_REC)))

    def close(self) -> None:
        self._queue.put(("close", None))

    def get_title(self) -> str:
        return self._title_var.get().strip()

    # ---- tk nit ----

    def _tick(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "chunk":
                    self._text.configure(state="normal")
                    self._text.insert("end", payload + " ")
                    self._text.see("end")
                    self._text.configure(state="disabled")
                elif kind == "title":
                    if not self._title_var.get().strip():
                        self._title_var.set(payload)
                elif kind == "status":
                    text, color = payload
                    self._status.configure(text=text)
                    self._dot.configure(fg=color)
                elif kind == "done":
                    self._status.configure(text="✓ Zapiski pripravljeni")
                    self._dot.configure(fg=ACCENT_OK)
                    self._stop_btn.configure(text="Zapri", command=self._destroy)
                    if payload:
                        self._link_label.configure(text="Odpri Google Doc")
                        self._link_label.pack(side="left")
                        self._link_label.bind("<Button-1>", lambda e, url=payload: self._open(url))
                elif kind == "close":
                    self._destroy()
                    return
        except queue.Empty:
            pass
        if not self._stopped:
            elapsed = int(time.time() - self._start_time)
            self._timer.configure(text=f"{elapsed // 60}:{elapsed % 60:02d}")
        try:
            self._win.after(200, self._tick)
        except tk.TclError:
            pass  # okno uničeno

    @staticmethod
    def _open(url: str) -> None:
        import webbrowser

        webbrowser.open(url)

    def _handle_stop(self) -> None:
        if self._stopped:
            self._destroy()
            return
        self._stopped = True
        self._stop_btn.configure(state="disabled")
        self._on_stop()

    def _destroy(self) -> None:
        try:
            self._win.destroy()
        except tk.TclError:
            pass
