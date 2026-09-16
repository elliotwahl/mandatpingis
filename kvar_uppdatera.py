"""Räknar ut vilka uppsamlingsdistrikt som återstår och hur stora de är.

Valmyndigheten publicerar inte hur många röster ett oräknat distrikt kommer att
innehålla. Volymen uppskattas därför ur 2022 års slutliga resultat för samma
kommun, uppräknad med den faktiska ökning som syns i de kommuner som redan
rapporterat i år (2026 var den +32 % när sidan byggdes).

Varför inte en platt kvot: uppsamlingsrösternas andel av kommunens vanliga
röster faller kraftigt med kommunstorlek (11,6 % i minsta fjärdedelen mot 3,6 %
i den största), och ingen rapporterad kommun är i närheten av Göteborgs storlek.
En platt kvot överskattade volymen med nästan det dubbla.

Distriktsfilerna går inte att hämta var för sig — uppsamlingsdistriktet har ofta
samma kod som sin förälder, vilket ger 404. De läses ur föräldrafilen, där de
ligger som barn under namnet "Uppsamlingsdistrikt NN".

    python3 kvar_uppdatera.py        # ~630 anrop första gången, ~314 sedan
"""
import concurrent.futures as cf
import json
import os
import urllib.error
import urllib.request

ROT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROT, "data")
BAS = "https://resultat.val.se/data"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read())
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        return None


def foraldrar(ar):
    """Filnamnen på nivån direkt ovanför valdistrikt."""
    vg = get(f"{BAS}/valgeografi/valgeografi_val{ar}.json")
    rd = [v for v in vg["valgeografi"] if v["kod"] == "RD"][0]
    ut = []

    def walk(n, p):
        q = p + [n["kod"]]
        barn = n.get("valgeografi") or []
        if barn and barn[0]["typ"] == "VALDISTRIKT":
            ut.append("_".join(q))
            return
        for k in barn:
            walk(k, q)
    walk(rd, [])
    return ut


def svep(ar, suffix):
    """{nyckel: {upp, vanl, namn}} för varje förälder."""
    namn = foraldrar(ar)
    urler = [(n, f"{BAS}/resultat/val{ar}/{n}_{suffix}.json") for n in namn]
    ut = {}
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for n, j in zip([x[0] for x in urler],
                        ex.map(lambda x: get(x[1]), urler)):
            if not j:
                continue
            u, v = 0, 0
            har = False
            for b in j.get("valkretsar") or []:
                rp = b.get("rosterPaverkaMandat") or {}
                antal = rp.get("antalRoster") or 0
                if b["namn"].startswith("Uppsamlingsdistrikt"):
                    har, u = True, antal
                else:
                    v += antal
            if har:
                ut[n] = {"upp": u, "vanl": v, "namn": j["namn"]}
    return ut


def main():
    os.makedirs(DATA, exist_ok=True)
    bas22 = os.path.join(DATA, "bas2022.json")
    if os.path.exists(bas22):
        n22 = json.load(open(bas22, encoding="utf-8"))
    else:
        print("hämtar 2022 som baslinje (görs en gång) …")
        n22 = svep(2022, "S")
        json.dump(n22, open(bas22, "w", encoding="utf-8"), ensure_ascii=False)
    print("hämtar 2026 …")
    n26 = svep(2026, "P")

    rapp = [k for k in n26 if n26[k]["upp"] > 0 and k in n22 and n22[k]["upp"]]
    vaxt = (sum(n26[k]["upp"] for k in rapp) /
            sum(n22[k]["upp"] for k in rapp)) if rapp else 1.0
    kvar = sorted(((n22[k]["upp"] * vaxt, n26[k]["namn"])
                   for k in n26 if n26[k]["upp"] == 0 and k in n22),
                  reverse=True)
    ut = {
        "antal": len(kvar),
        "volym": round(sum(x for x, _ in kvar)),
        "vaxt": round(vaxt, 4),
        "storsta": [{"namn": n, "est": round(x)} for x, n in kvar[:8]],
    }
    json.dump(ut, open(os.path.join(DATA, "kvar.json"), "w", encoding="utf-8"),
              ensure_ascii=False)

    # Lista över de föräldrar som fortfarande saknas, med förväntad volym.
    # Funktionen /api/kvar kontrollerar bara dessa — ett distrikt som väl
    # rapporterat blir aldrig orapporterat igen, så listan krymper monotont
    # och sveper aldrig mer än vad som faktiskt är kvar.
    lista = [{"n": k, "namn": n26[k]["namn"], "est": round(n22[k]["upp"] * vaxt)}
             for k in n26 if n26[k]["upp"] == 0 and k in n22]
    lista.sort(key=lambda x: -x["est"])
    json.dump(lista, open(os.path.join(DATA, "kvarlista.json"), "w",
                          encoding="utf-8"), ensure_ascii=False)
    # Samma lista bredvid funktionen, så esbuild kan bunta in den.
    fn = os.path.join(ROT, "netlify", "functions")
    os.makedirs(fn, exist_ok=True)
    json.dump(lista, open(os.path.join(fn, "kvarlista.json"), "w",
                          encoding="utf-8"), ensure_ascii=False)
    print(f"kvarlista.json: {len(lista)} föräldrar att kontrollera live")
    print(f"{ut['antal']} kvar, uppskattat {ut['volym']:,} röster "
          f"(uppräkning {vaxt:.3f})".replace(",", " "))


if __name__ == "__main__":
    main()
