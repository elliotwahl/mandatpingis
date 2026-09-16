"""Hämtar färsk data till Mandatpingis och skriver data/sida.json + data/serie.json.

Läser Valmyndighetens preliminära riksresultat via mandatmarginal-projektets
moduler, och bygger tidsserien ur dess sparade råfiler — varje avläsning som
finns på disk blir en punkt i pingisdiagrammet.

    python3 hamta_data.py && python3 bygg.py
"""
import glob
import json
import os
import re
import sys

ROT = os.path.dirname(os.path.abspath(__file__))
MANDAT = os.path.join(os.path.dirname(ROT), "mandatmarginal")
sys.path.insert(0, MANDAT)

import hamta          # noqa: E402
import rakna          # noqa: E402

DATA = os.path.join(ROT, "data")
RAW = os.path.join(MANDAT, "raw")
TIDO = ("M", "KD", "L", "SD")
ROD = ("S", "V", "MP", "C")


def serie():
    """Tidsserie ur alla sparade preliminärfiler. Signerat avstånd: positivt =
    SD håller det 349:e mandatet med den marginalen, negativt = så många röster
    saknas för att ta det."""
    sett = {}
    for f in sorted(glob.glob(os.path.join(RAW, "RD_P_*.json"))):
        try:
            j = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if not j.get("partiMandat"):
            continue
        try:
            t = rakna.fordela(rakna.kvalade(j))
            marg = rakna.marginaler(j)
        except Exception:
            continue
        if sum(t.values()) != 349:
            continue
        m = re.search(r"(\d{8})T(\d{6})Z", os.path.basename(f))
        sd = marg["SD"]
        sett[j["antalValdistriktRaknade"]] = {
            "tid": f"{m.group(2)[:2]}:{m.group(2)[2:4]}",
            "raknade": j["antalValdistriktRaknade"],
            "rod": sum(t[p] for p in ROD),
            "tido": sum(t[p] for p in TIDO),
            "s": t["S"], "sd": t["SD"],
            "avst": sd["minus_1"] if t["SD"] >= 63 else -sd["plus_1"],
        }
    return [sett[k] for k in sorted(sett)]


def kvarvarande():
    """Uppsamlingsdistrikt som inte rapporterat, med volym uppskattad ur 2022.

    Kräver att data/kvar.json finns — den byggs av kvar_uppdatera.py, som sveper
    de 314 föräldrafilerna. Saknas den returneras tomt, och sidan visar noll.
    """
    p = os.path.join(DATA, "kvar.json")
    if not os.path.exists(p):
        return 0, 0, []
    k = json.load(open(p, encoding="utf-8"))
    return k["antal"], k["volym"], k["storsta"]


def main():
    os.makedirs(DATA, exist_ok=True)
    h = hamta.hamta()
    data, _ = hamta.basfil(h)
    if data is None:
        print("inget svar från Valmyndigheten", file=sys.stderr)
        return 1
    slut = (h.get("S") or {}).get("data") or {}
    s = rakna.sammanfatta(data)
    if not s["kontroll_ok"]:
        print("VARNING: egen fördelning stämmer inte mot Valmyndighetens — "
              "sidan byggs inte", file=sys.stderr)
        return 1
    pr = {p["partiforkortning"]: p
          for p in data["rosterPaverkaMandat"]["partiroster"]}
    antal, volym, storsta = kvarvarande()

    ut = {
        "hamtat": data["senasteRapporteringstid"],
        "raknade": data["antalValdistriktRaknade"],
        "ska": data["antalValdistriktSomSkaRaknas"],
        "roster": data["totaltAntalRoster"],
        "valdeltagande": data["valdeltagande"],
        "rostberattigade": data["antalRostberattigade"],
        "slut_raknade": slut.get("antalValdistriktRaknade", 0),
        "partier": [{
            "p": p, "mandat": s["marginaler"][p]["mandat"],
            "roster": s["marginaler"][p]["roster"],
            "andel": pr[p]["andelRoster"],
            "andel22": pr[p]["andelRosterForegaendeVal"],
            "plus": s["marginaler"][p]["plus_1"],
            "minus": s["marginaler"][p]["minus_1"],
            "farg": pr[p]["fargkod"],
            "block": "tido" if p in TIDO else "rod",
        } for p in sorted(s["marginaler"],
                          key=lambda x: -s["marginaler"][x]["roster"])],
        "rod": sum(s["egen_fordelning"][p] for p in ROD),
        "tido": sum(s["egen_fordelning"][p] for p in TIDO),
        "upp_kvar": antal, "upp_volym": volym, "storsta_kvar": storsta,
        "kontroll": s["kontroll_ok"],
    }
    json.dump(ut, open(os.path.join(DATA, "sida.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    sr = serie()
    json.dump(sr, open(os.path.join(DATA, "serie.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    print(f"{ut['raknade']}/{ut['ska']} distrikt · rödgröna {ut['rod']} "
          f"tidö {ut['tido']} · {len(sr)} seriepunkter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
