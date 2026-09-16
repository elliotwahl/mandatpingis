import json, math
import os, subprocess, sys
ROT = os.path.dirname(os.path.abspath(__file__))
KALLA = os.path.join(ROT, "data")
UT = os.path.join(ROT, "public", "index.html")
D = json.load(open(os.path.join(KALLA, "sida.json"), encoding="utf-8"))
S = json.load(open(os.path.join(KALLA, "serie.json"), encoding="utf-8"))

def tal(n): return f"{n:,}".replace(",", " ")
MAJ = 175; TOT = 349
rod, tido = D["rod"], D["tido"]
ledare = "rod" if rod >= MAJ else "tido" if tido >= MAJ else None
pct = D["raknade"] / D["ska"] * 100

# ---- pingis-diagram, signerat rotskalat -----------------------------------
W, H = 860, 260
PAD_L, PAD_R, PAD_T, PAD_B = 62, 18, 22, 34
def sq(v): return math.copysign(math.sqrt(abs(v)), v)
vals = [r["avst"] for r in S]
lo, hi = min(sq(v) for v in vals), max(sq(v) for v in vals)
lo, hi = min(lo, -12), max(hi, 12)
span = hi - lo
def X(i): return PAD_L + i * (W - PAD_L - PAD_R) / max(len(S) - 1, 1)
def Y(v): return PAD_T + (hi - sq(v)) * (H - PAD_T - PAD_B) / span
pts = " ".join(f"{X(i):.1f},{Y(r['avst']):.1f}" for i, r in enumerate(S))
noll = Y(0)
ticks = [t for t in (-5000, -1000, -200, 0, 200) if lo <= sq(t) <= hi]
tickmarkup = "".join(
    f'<line x1="{PAD_L}" y1="{Y(t):.1f}" x2="{W-PAD_R}" y2="{Y(t):.1f}" '
    f'class="{"grid zero" if t == 0 else "grid"}"/>'
    f'<text x="{PAD_L-8}" y="{Y(t)+3.5:.1f}" class="tick" text-anchor="end">'
    f'{"delat" if t == 0 else tal(abs(t))}</text>' for t in ticks)
# markera skiften
skiften = "".join(
    f'<circle cx="{X(i):.1f}" cy="{Y(r["avst"]):.1f}" r="4.5" class="flip"/>'
    for i, r in enumerate(S) if i and S[i-1]["sd"] != r["sd"])
sista = f'<circle cx="{X(len(S)-1):.1f}" cy="{Y(S[-1]["avst"]):.1f}" r="6" class="nu"/>'
omrade = (f'<path d="M {X(0):.1f},{noll:.1f} L ' +
          " L ".join(f"{X(i):.1f},{Y(r['avst']):.1f}" for i, r in enumerate(S)) +
          f' L {X(len(S)-1):.1f},{noll:.1f} Z" class="fyll"/>')

partirader = "".join(
    f'<tr><th scope="row"><span class="dot" style="background:{p["farg"] or "#8A94A6"}"></span>'
    f'{p["p"]}</th>'
    f'<td class="num stor">{p["mandat"]}</td>'
    f'<td class="num">{str(p["andel"]).replace(".", ",")} %</td>'
    f'<td class="num dim">{str(p["andel22"]).replace(".", ",")}</td>'
    f'<td class="num">{tal(p["plus"])}</td>'
    f'<td class="num">{tal(p["minus"]) if p["minus"] is not None else "—"}</td></tr>'
    for p in D["partier"])

kvarrader = "".join(
    f'<li><span class="kn">{k["namn"]}</span>'
    f'<span class="kv">{tal(k["est"])}</span></li>' for k in D["storsta_kvar"])

sista_avst = S[-1]["avst"]
if sista_avst >= 0:
    lage = f"SD håller det med <strong>{tal(sista_avst)}</strong> rösters marginal"
else:
    lage = f"SD saknar <strong>{tal(-sista_avst)}</strong> röster för att ta det"

html = f"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mandatpingis — ett mandat avgör riksdagsmajoriteten</title>
<meta name="description" content="Ett riksdagsmandat studsar mellan S och SD medan onsdagsrösterna räknas. Live-läge ur Valmyndighetens preliminära resultat.">
<meta name="robots" content="index,follow">
<meta property="og:title" content="Mandatpingis">
<meta property="og:description" content="Ett riksdagsmandat studsar mellan S och SD medan onsdagsrösterna räknas.">
<meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
:root {{
  --bg:#F4F6F9; --panel:#FFFFFF; --ink:#101620; --dim:#5D6879; --faint:#8E99AA;
  --line:#DCE2EB; --net:#101620; --ball:#E0A400;
  --rod:#C40000; --tido:#1B5CB1;
  color-scheme: light dark;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg:#0D1117; --panel:#151B24; --ink:#E9EEF5; --dim:#97A3B4; --faint:#6E7A8B;
    --line:#232C38; --net:#E9EEF5; --ball:#FFC531;
    --rod:#FF5A5A; --tido:#6FA8FF;
  }}
}}
:root[data-theme="dark"] {{
  --bg:#0D1117; --panel:#151B24; --ink:#E9EEF5; --dim:#97A3B4; --faint:#6E7A8B;
  --line:#232C38; --net:#E9EEF5; --ball:#FFC531;
  --rod:#FF5A5A; --tido:#6FA8FF;
}}
* {{ box-sizing:border-box; }}
html, body {{ margin:0; }}
img {{ max-width:100%; }}
body {{
  background:var(--bg); color:var(--ink);
  font-family:"Familjen Grotesk", system-ui, -apple-system, sans-serif;
  font-size:16px; line-height:1.5;
}}
.wrap {{ max-width:900px; margin:0 auto; padding-inline:20px; padding-block:32px 56px; }}
.mono {{ font-family:"IBM Plex Mono", ui-monospace, monospace; }}
.num {{ font-variant-numeric:tabular-nums; }}
h1 {{ font-size:clamp(2.1rem,7vw,3.2rem); font-weight:700; letter-spacing:-.02em;
     margin:0; text-wrap:balance; }}
.sub {{ color:var(--dim); margin:.35rem 0 0; max-width:62ch; }}
.stamp {{ font-family:"IBM Plex Mono", monospace; font-size:.72rem; letter-spacing:.09em;
   text-transform:uppercase; color:var(--faint); display:flex; flex-wrap:wrap; gap:.4rem 1.1rem;
   margin-top:1.1rem; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:10px;
   padding:22px; margin-top:22px; }}
.lbl {{ font-family:"IBM Plex Mono", monospace; font-size:.7rem; letter-spacing:.12em;
   text-transform:uppercase; color:var(--faint); margin:0 0 .9rem; }}

/* bordet */
.board {{ text-align:center; }}
.score {{ display:flex; align-items:flex-end; justify-content:center; gap:clamp(14px,5vw,44px);
   margin-bottom:18px; flex-wrap:wrap; }}
.side .n {{ font-size:clamp(3rem,13vw,5rem); font-weight:700; line-height:.9;
   font-variant-numeric:tabular-nums; display:block; }}
.side .t {{ font-family:"IBM Plex Mono", monospace; font-size:.72rem; letter-spacing:.11em;
   text-transform:uppercase; color:var(--dim); }}
.side.r .n {{ color:var(--rod); }} .side.t2 .n {{ color:var(--tido); }}
.side.win .n::after {{ content:""; display:block; height:3px; margin-top:.35rem;
   background:currentColor; border-radius:2px; }}
.vs {{ font-family:"IBM Plex Mono", monospace; color:var(--faint); font-size:.8rem;
   padding-bottom:1.2rem; }}
.track {{ position:relative; height:44px; border-radius:6px; overflow:hidden;
   background:var(--line); display:flex; }}
.track .r {{ background:var(--rod); }} .track .t2 {{ background:var(--tido); }}
.netline {{ position:absolute; top:-9px; bottom:-9px; width:3px; background:var(--net);
   box-shadow:0 0 0 2px var(--panel); border-radius:2px; }}
.netlbl {{ font-family:"IBM Plex Mono", monospace; font-size:.68rem; letter-spacing:.1em;
   color:var(--dim); margin-top:14px; }}
.verdict {{ margin-top:16px; font-size:1.05rem; text-wrap:balance; }}
.verdict strong {{ font-variant-numeric:tabular-nums; }}

/* diagram */
svg {{ width:100%; height:auto; display:block; }}
.grid {{ stroke:var(--line); stroke-width:1; }}
.grid.zero {{ stroke:var(--net); stroke-width:1.5; stroke-dasharray:4 3; }}
.tick {{ fill:var(--faint); font-family:"IBM Plex Mono", monospace; font-size:10px; }}
.linje {{ fill:none; stroke:var(--ball); stroke-width:2.2; stroke-linejoin:round; }}
.fyll {{ fill:var(--ball); opacity:.10; }}
.flip {{ fill:var(--bg); stroke:var(--ball); stroke-width:2.2; }}
.nu {{ fill:var(--ball); stroke:var(--panel); stroke-width:2.5; }}

table {{ width:100%; border-collapse:collapse; font-variant-numeric:tabular-nums; }}
th, td {{ padding:.5rem .35rem; border-bottom:1px solid var(--line); text-align:right; }}
thead th {{ font-family:"IBM Plex Mono", monospace; font-size:.64rem; letter-spacing:.09em;
   text-transform:uppercase; color:var(--faint); font-weight:500; white-space:nowrap; }}
tbody th {{ text-align:left; font-weight:600; white-space:nowrap; }}
td.stor {{ font-size:1.15rem; font-weight:600; }}
td.dim {{ color:var(--faint); }}
.dot {{ display:inline-block; width:9px; height:9px; border-radius:2px; margin-right:.5rem;
   vertical-align:baseline; }}
.tblwrap {{ overflow-x:auto; }}

ul.kvar {{ list-style:none; margin:0; padding:0; }}
ul.kvar li {{ display:flex; justify-content:space-between; gap:1rem; padding:.42rem 0;
   border-bottom:1px solid var(--line); }}
ul.kvar li:last-child {{ border-bottom:0; }}
.kn {{ color:var(--ink); }} .kv {{ font-family:"IBM Plex Mono", monospace; color:var(--dim);
   font-variant-numeric:tabular-nums; }}
.grid2 {{ display:grid; gap:22px; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); }}
.foot {{ color:var(--faint); font-size:.85rem; margin-top:34px; }}
.foot a {{ color:var(--dim); }}
@media (prefers-reduced-motion:reduce) {{ * {{ animation:none !important; transition:none !important; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Mandatpingis</h1>
    <p class="sub">Ett enda riksdagsmandat studsar mellan S och SD medan onsdagsrösterna
      räknas. Det avgör om de rödgröna behåller egen majoritet.</p>
    <div class="stamp">
      <span>Uppdaterad {D['hamtat']}</span>
      <span>{tal(D['raknade'])} av {tal(D['ska'])} distrikt · {pct:.1f} %</span>
      <span>Valdeltagande {D['valdeltagande']}</span>
    </div>
  </header>

  <section class="card board">
    <p class="lbl">Blocken · majoritet vid {MAJ} av {TOT}</p>
    <div class="score">
      <div class="side r {'win' if ledare=='rod' else ''}">
        <span class="n">{rod}</span><span class="t">Rödgröna · S V MP C</span></div>
      <div class="vs">mot</div>
      <div class="side t2 {'win' if ledare=='tido' else ''}">
        <span class="n">{tido}</span><span class="t">Tidö · M KD L SD</span></div>
    </div>
    <div class="track">
      <div class="r" style="width:{rod/TOT*100:.3f}%"></div>
      <div class="t2" style="width:{tido/TOT*100:.3f}%"></div>
      <div class="netline" style="left:{MAJ/TOT*100:.3f}%"></div>
    </div>
    <p class="netlbl mono">▲ nätet går vid {MAJ} mandat</p>
    <p class="verdict">{'De rödgröna har egen majoritet — med ' + str(rod-MAJ+1) + ' mandats marginal.' if ledare=='rod' else 'Tidö har egen majoritet.' if ledare=='tido' else 'Ingen sida når 175.'}
      Det omstridda mandatet: {lage}.</p>
  </section>

  <section class="card">
    <p class="lbl">Pingisen · avstånd till det 349:e mandatet, per avläsning</p>
    <svg viewBox="0 0 {W} {H}" role="img"
         aria-label="Avståndet i röster mellan SD och det sista mandatet över eftermiddagen">
      {tickmarkup}
      {omrade}
      <polyline class="linje" points="{pts}"/>
      {skiften}{sista}
      <text x="{PAD_L}" y="{H-10}" class="tick">{S[0]['tid']} · {tal(S[0]['raknade'])} distrikt</text>
      <text x="{W-PAD_R}" y="{H-10}" class="tick" text-anchor="end">{S[-1]['tid']} · {tal(S[-1]['raknade'])} distrikt</text>
    </svg>
    <p class="netlbl mono">Över den streckade linjen håller SD mandatet, under saknas det.
      Ringar markerar de {sum(1 for i,r in enumerate(S) if i and S[i-1]['sd']!=r['sd'])} gånger mandatet bytt ägare.</p>
  </section>

  <section class="card">
    <p class="lbl">Partierna</p>
    <div class="tblwrap">
      <table>
        <thead><tr><th scope="col" style="text-align:left">Parti</th>
          <th scope="col">Mandat</th><th scope="col">Andel</th><th scope="col">2022</th>
          <th scope="col">+1 kräver</th><th scope="col">−1 vid tapp</th></tr></thead>
        <tbody>{partirader}</tbody>
      </table>
    </div>
  </section>

  <div class="grid2">
    <section class="card">
      <p class="lbl">Kvar att räkna</p>
      <p style="margin:0 0 .8rem"><span class="mono num" style="font-size:2rem;font-weight:600">{tal(D['upp_kvar'])}</span>
        uppsamlingsdistrikt, uppskattat <span class="mono num">{tal(D['upp_volym'])}</span> röster.</p>
      <p style="margin:0;color:var(--dim);font-size:.92rem">Det är sena förtidsröster och
        brevröster som inte kunnat knytas till ett vallokalsdistrikt. Alla 6 312 vallokalsdistrikt
        är färdigräknade. Länsstyrelserna har hittills räknat om {tal(D['slut_raknade'])} distrikt.</p>
    </section>
    <section class="card">
      <p class="lbl">Störst av det som saknas</p>
      <ul class="kvar">{kvarrader}</ul>
    </section>
  </div>

  <p class="foot">Källa: Valmyndigheten, <span class="mono">resultat.val.se</span>, preliminärt
    resultat. Mandatfördelningen är omräknad med jämkade uddatalsmetoden och stämd mot
    Valmyndighetens egen fördelning vid varje avläsning. Volymen som återstår är uppskattad ur
    2022 års utfall per kommun och är inte ett officiellt tal. Siffrorna är preliminära —
    länsstyrelsernas slutliga rösträkning är en omräkning där redan räknade tal kan ändras.</p>
</div>
</body>
</html>
"""
open(UT, "w", encoding="utf-8").write(html)
print("skrev", UT, len(html), "tecken")
