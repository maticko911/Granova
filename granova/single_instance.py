"""Varovalo proti dvema instancama Granove hkrati.

Prva instanca zasede vrata 127.0.0.1:49517; vsaka naslednja ob bind-u dobi
OSError in se tiho umakne. Socket se sprosti sam ob smrti procesa, zato ni
zastarelih zaklepov (za razliko od lock-datoteke).
"""
from __future__ import annotations

import socket

PORT = 49517


def acquire(port: int = PORT) -> socket.socket | None:
    """Vrne odprt socket (drži ga do konca procesa) ali None, če app že teče."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        sock.close()
        return None
    return sock
