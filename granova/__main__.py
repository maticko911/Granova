"""CLI za ročni zagon Faze 1:

    python -m granova examples/sample_transcript_sl.txt [pot_do_zapiskov.txt]

Izpiše zapiske, objavo in urejen zapisnik na standardni izhod.
"""

import logging
import sys
from pathlib import Path

from granova.pipeline import process_meeting


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    from granova import trust
    trust.install()  # zaupaj sistemski certifikatni shrambi (protivirusno HTTPS skeniranje)

    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    transcript = Path(sys.argv[1]).read_text(encoding="utf-8")
    raw_notes = Path(sys.argv[2]).read_text(encoding="utf-8") if len(sys.argv) > 2 else ""

    result = process_meeting(transcript, raw_notes)
    if result is None:
        print("\nTranskript zavrnjen — ni smiselnega sestanka, dokument ne bi bil ustvarjen.")
        return 2

    n = result.notes
    print(f"\n{'=' * 60}\n{n.naslov}\n{'=' * 60}")
    print(f"\nPOVZETEK\n{n.povzetek}")
    print("\nKLJUČNE TOČKE")
    for t in n.kljucne_tocke:
        print(f"  • {t}")
    if n.odlocitve:
        print("\nODLOČITVE")
        for o in n.odlocitve:
            print(f"  • {o}")
    if n.naloge:
        print("\nNALOGE")
        for a in n.naloge:
            extra = " — ".join(x for x in (a.nosilec, a.rok) if x)
            print(f"  • {a.naloga}" + (f" ({extra})" if extra else ""))
    if n.udelezenci:
        print(f"\nUDELEŽENCI: {', '.join(n.udelezenci)}")

    print(f"\n{'=' * 60}\nOBJAVA (IG/FB)\n{'=' * 60}\n{result.objava.besedilo}")
    if result.objava.predlogi:
        print("\nPredlogi:")
        for p in result.objava.predlogi:
            print(f"  • {p}")

    print(f"\n{'=' * 60}\nUREJEN ZAPISNIK\n{'=' * 60}\n{result.enhanced_minutes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
