"""Bygger public/index.html.

Sidan renderas i webbläsaren ur /api/data (Netlify-funktionen) och pollar den
var 30:e sekund. Byggtidens ögonblicksbild bakas in som startläge, så att sidan
visar riktiga siffror direkt vid första paint och fortfarande fungerar om
funktionen skulle fallera.

Pingisserien: historiken fram till bygget bakas in, och varje ny avläsning som
pollningen ser läggs till. Läsarens egen serie sparas i localStorage, så den
växer även mellan omladdningar.

    python3 hamta_data.py && python3 bygg.py
"""
import json
import os

ROT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROT, "data")
UT = os.path.join(ROT, "public", "index.html")

D = json.load(open(os.path.join(DATA, "sida.json"), encoding="utf-8"))
S = json.load(open(os.path.join(DATA, "serie.json"), encoding="utf-8"))

INIT = json.dumps({
    "snapshot": {
        "hamtat": D["hamtat"], "raknade": D["raknade"], "ska": D["ska"],
        "roster": D["roster"], "valdeltagande": D["valdeltagande"],
        "slutRaknade": D["slut_raknade"], "kontroll": D["kontroll"],
        "partier": [{"p": p["p"], "mandat": p["mandat"], "andel": p["andel"],
                     "andel22": p["andel22"], "plus": p["plus"],
                     "minus": p["minus"], "farg": p["farg"]}
                    for p in D["partier"]],
        "rod": D["rod"], "tido": D["tido"],
        "avst": S[-1]["avst"] if S else None,
        "sd": S[-1]["sd"] if S else 0, "s": S[-1]["s"] if S else 0,
    },
    "serie": S,
    "kvar": {"antal": D["upp_kvar"], "volym": D["upp_volym"],
             "storsta": D["storsta_kvar"]},
}, ensure_ascii=False, separators=(",", ":"))

HTML = """<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mandatpingis — ett mandat avgör riksdagsmajoriteten</title>
<meta name="description" content="Ett riksdagsmandat studsar mellan S och SD medan onsdagsrösterna räknas. Live ur Valmyndighetens preliminära resultat.">
<meta property="og:title" content="Mandatpingis">
<meta property="og:description" content="Ett riksdagsmandat studsar mellan S och SD medan onsdagsrösterna räknas.">
<meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
:root {
  --bg:#F4F6F9; --panel:#FFFFFF; --ink:#101620; --dim:#5D6879; --faint:#8E99AA;
  --line:#DCE2EB; --net:#101620; --ball:#E0A400; --live:#1B9E4B;
  --rod:#C40000; --tido:#1B5CB1;
  color-scheme: light dark;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg:#0D1117; --panel:#151B24; --ink:#E9EEF5; --dim:#97A3B4; --faint:#6E7A8B;
    --line:#232C38; --net:#E9EEF5; --ball:#FFC531; --live:#3DD17A;
    --rod:#FF5A5A; --tido:#6FA8FF;
  }
}
:root[data-theme="dark"] {
  --bg:#0D1117; --panel:#151B24; --ink:#E9EEF5; --dim:#97A3B4; --faint:#6E7A8B;
  --line:#232C38; --net:#E9EEF5; --ball:#FFC531; --live:#3DD17A;
  --rod:#FF5A5A; --tido:#6FA8FF;
}
* { box-sizing:border-box; }
html, body { margin:0; }
img { max-width:100%; }
body {
  background:var(--bg); color:var(--ink);
  font-family:"Familjen Grotesk", system-ui, -apple-system, sans-serif;
  font-size:16px; line-height:1.5;
}
.wrap { max-width:900px; margin:0 auto; padding-inline:20px; padding-block:32px 56px; }
.mono { font-family:"IBM Plex Mono", ui-monospace, monospace; }
.num { font-variant-numeric:tabular-nums; }
h1 { font-size:clamp(2.1rem,7vw,3.2rem); font-weight:700; letter-spacing:-.02em;
     margin:0; text-wrap:balance; }
.sub { color:var(--dim); margin:.35rem 0 0; max-width:62ch; }
.stamp { font-family:"IBM Plex Mono", monospace; font-size:.72rem; letter-spacing:.09em;
   text-transform:uppercase; color:var(--faint); display:flex; flex-wrap:wrap;
   gap:.4rem 1.1rem; margin-top:1.1rem; align-items:center; }
.puls { display:inline-flex; align-items:center; gap:.42rem; color:var(--live); }
.puls i { width:7px; height:7px; border-radius:50%; background:currentColor;
   animation:blink 2.4s ease-in-out infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.25} }
.puls.av { color:var(--faint); } .puls.av i { animation:none; }
.card { background:var(--panel); border:1px solid var(--line); border-radius:10px;
   padding:22px; margin-top:22px; }
.lbl { font-family:"IBM Plex Mono", monospace; font-size:.7rem; letter-spacing:.12em;
   text-transform:uppercase; color:var(--faint); margin:0 0 .9rem; }
.board { text-align:center; }
.score { display:flex; align-items:flex-end; justify-content:center;
   gap:clamp(14px,5vw,44px); margin-bottom:18px; flex-wrap:wrap; }
.side .n { font-size:clamp(3rem,13vw,5rem); font-weight:700; line-height:.9;
   font-variant-numeric:tabular-nums; display:block;
   transition:color .25s ease; }
.side .t { font-family:"IBM Plex Mono", monospace; font-size:.72rem; letter-spacing:.11em;
   text-transform:uppercase; color:var(--dim); }
.side.r .n { color:var(--rod); } .side.t2 .n { color:var(--tido); }
.side .n::after { content:""; display:block; height:3px; margin-top:.35rem;
   border-radius:2px; background:transparent; }
.side.win .n::after { background:currentColor; }
.vs { font-family:"IBM Plex Mono", monospace; color:var(--faint); font-size:.8rem;
   padding-bottom:1.2rem; }
.track { position:relative; height:44px; border-radius:6px; overflow:hidden;
   background:var(--line); display:flex; }
.track .r { background:var(--rod); transition:width .4s ease; }
.track .t2 { background:var(--tido); transition:width .4s ease; }
.netline { position:absolute; top:-9px; bottom:-9px; width:3px; background:var(--net);
   box-shadow:0 0 0 2px var(--panel); border-radius:2px; }
.netlbl { font-family:"IBM Plex Mono", monospace; font-size:.68rem; letter-spacing:.1em;
   color:var(--dim); margin-top:14px; }
.verdict { margin-top:16px; font-size:1.05rem; text-wrap:balance; }
.verdict strong { font-variant-numeric:tabular-nums; }
svg { width:100%; height:auto; display:block; }
.grid { stroke:var(--line); stroke-width:1; }
.grid.zero { stroke:var(--net); stroke-width:1.5; stroke-dasharray:4 3; }
.tick { fill:var(--faint); font-family:"IBM Plex Mono", monospace; font-size:10px; }
.linje { fill:none; stroke:var(--ball); stroke-width:2.2; stroke-linejoin:round; }
.fyll { fill:var(--ball); opacity:.10; }
.flip { fill:var(--panel); stroke:var(--ball); stroke-width:2.2; }
.nu { fill:var(--ball); stroke:var(--panel); stroke-width:2.5; }
table { width:100%; border-collapse:collapse; font-variant-numeric:tabular-nums; }
th, td { padding:.5rem .35rem; border-bottom:1px solid var(--line); text-align:right; }
thead th { font-family:"IBM Plex Mono", monospace; font-size:.64rem; letter-spacing:.09em;
   text-transform:uppercase; color:var(--faint); font-weight:500; white-space:nowrap; }
tbody th { text-align:left; font-weight:600; white-space:nowrap; }
td.stor { font-size:1.15rem; font-weight:600; }
td.dim { color:var(--faint); }
.dot { display:inline-block; width:9px; height:9px; border-radius:2px; margin-right:.5rem; }
.tblwrap { overflow-x:auto; }
ul.kvar { list-style:none; margin:0; padding:0; }
ul.kvar li { display:flex; justify-content:space-between; gap:1rem; padding:.42rem 0;
   border-bottom:1px solid var(--line); }
ul.kvar li:last-child { border-bottom:0; }
.kn { color:var(--ink); } .kv { font-family:"IBM Plex Mono", monospace; color:var(--dim);
   font-variant-numeric:tabular-nums; }
.grid2 { display:grid; gap:22px; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); }
.foot { color:var(--faint); font-size:.85rem; margin-top:34px; }
.lagevaljare { margin-left:auto; display:inline-flex; border:1px solid var(--line);
   border-radius:999px; overflow:hidden; }
.lagevaljare button { font:inherit; font-family:"IBM Plex Mono",monospace;
   font-size:.66rem; letter-spacing:.1em; text-transform:uppercase; cursor:pointer;
   border:0; background:transparent; color:var(--faint); padding:.42rem .8rem; }
.lagevaljare button[aria-pressed="true"] { background:var(--ink); color:var(--bg); }
.lagevaljare button:focus-visible { outline:2px solid var(--ball); outline-offset:1px; }
#bord { display:none; }
/* Pingisläge: brädan blir ett bordtennisbord sett uppifrån. Nätet står kvar
   vid 175 mandat, blockens andel tonar halvorna, och bollen ligger på den sida
   som just nu håller det omstridda mandatet. */
[data-lage="pingis"] .track, [data-lage="pingis"] .netlbl { display:none; }
[data-lage="pingis"] #bord { display:block; }
[data-lage="pingis"] .board { background:#0C4A6E; border-color:#0A3A55; }
[data-lage="pingis"] .board .lbl, [data-lage="pingis"] .board .side .t { color:#9CC9E3; }
[data-lage="pingis"] .board .verdict { color:#EAF4FA; }
[data-lage="pingis"] .board .vs { color:#7FB3D0; }
[data-lage="pingis"] .board .side.r .n { color:#FF8A8A; }
[data-lage="pingis"] .board .side.t2 .n { color:#8FC4FF; }
.bordyta { fill:#1668A8; }
.bordlinje { stroke:#F2F6F8; stroke-width:3; fill:none; }
.bordhalva.r { fill:var(--rod); } .bordhalva.t2 { fill:var(--tido); }
.natstolpe { fill:#E8EEF2; } .nat { fill:#DCE6EC; }
.boll { fill:#FFD34D; stroke:#7A5B00; stroke-width:1.5;
   transition:cx .55s cubic-bezier(.34,1.3,.64,1), cy .55s ease; }
.bolltext { fill:#EAF4FA; font-family:"IBM Plex Mono",monospace; font-size:11px; }
.studs { animation:studs .55s ease; }
@keyframes studs { 0%,100%{transform:translateY(0)} 45%{transform:translateY(-14px)} }
.varn { color:var(--rod); font-weight:600; }
@media (prefers-reduced-motion:reduce) { *{animation:none!important;transition:none!important} }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Mandatpingis</h1>
    <p class="sub">Ett enda riksdagsmandat studsar mellan S och SD medan onsdagsrösterna
      räknas. Det avgör om de rödgröna behåller egen majoritet.</p>
    <div class="stamp">
      <span class="puls" id="puls"><i></i><span id="pulstext">live</span></span>
      <span id="st-tid"></span>
      <span id="st-distrikt"></span>
      <span id="st-valdelt"></span>
      <span class="lagevaljare" role="group" aria-label="Utseende">
        <button type="button" id="lage-enkel" aria-pressed="true">Enkel</button>
        <button type="button" id="lage-pingis" aria-pressed="false">Pingis</button>
      </span>
    </div>
  </header>

  <section class="card board">
    <p class="lbl">Blocken · majoritet vid 175 av 349</p>
    <div class="score">
      <div class="side r" id="sida-rod">
        <span class="n" id="n-rod">—</span><span class="t">Rödgröna · S V MP C</span></div>
      <div class="vs">mot</div>
      <div class="side t2" id="sida-tido">
        <span class="n" id="n-tido">—</span><span class="t">Tidö · M KD L SD</span></div>
    </div>
    <div class="track">
      <div class="r" id="bar-rod"></div><div class="t2" id="bar-tido"></div>
      <div class="netline" style="left:50.143%"></div>
    </div>
    <div id="bord"></div>
    <p class="netlbl mono">▲ nätet går vid 175 mandat</p>
    <p class="verdict" id="verdict"></p>
  </section>

  <section class="card">
    <p class="lbl">Pingisen · avstånd till det 349:e mandatet, per avläsning</p>
    <div id="chart"></div>
    <p class="netlbl mono" id="chart-txt"></p>
  </section>

  <section class="card">
    <p class="lbl">Partierna</p>
    <div class="tblwrap">
      <table>
        <thead><tr><th scope="col" style="text-align:left">Parti</th>
          <th scope="col">Mandat</th><th scope="col">Andel</th><th scope="col">2022</th>
          <th scope="col">+1 kräver</th><th scope="col">−1 vid tapp</th></tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </section>

  <div class="grid2">
    <section class="card">
      <p class="lbl">Kvar att räkna</p>
      <p style="margin:0 0 .8rem"><span class="mono num" id="k-antal"
         style="font-size:2rem;font-weight:600"></span>
        uppsamlingsdistrikt, uppskattat <span class="mono num" id="k-volym"></span> röster.</p>
      <p style="margin:0;color:var(--dim);font-size:.92rem">Sena förtidsröster och brevröster
        som inte kunnat knytas till ett vallokalsdistrikt. Alla 6 312 vallokalsdistrikt är
        färdigräknade. Länsstyrelserna har räknat om <span class="mono num" id="k-slut"></span>
        distrikt.</p>
    </section>
    <section class="card">
      <p class="lbl">Störst av det som saknas</p>
      <ul class="kvar" id="k-lista"></ul>
    </section>
  </div>

  <p class="foot">Källa: Valmyndigheten, <span class="mono">resultat.val.se</span>, preliminärt
    resultat, hämtat om var 30:e sekund. Mandatfördelningen räknas om med jämkade
    uddatalsmetoden och stäms av mot Valmyndighetens egen fördelning vid varje hämtning.
    Volymen som återstår är uppskattad ur 2022 års utfall per kommun och är inte ett
    officiellt tal. Siffrorna är preliminära — länsstyrelsernas slutliga rösträkning är en
    omräkning där redan räknade tal kan ändras.</p>
</div>

<script>
const INIT = __INIT__;
const MAJ = 175, TOT = 349;
const $ = (id) => document.getElementById(id);
// toLocaleString ger hårt mellanslag, som får full teckenbredd i IBM Plex Mono
// och slitar isär tusentalen. Smalt hårt mellanslag i stället.
const tal = (n) => (n == null ? "—"
  : Math.round(n).toLocaleString("sv-SE").replace(/\u00a0|\s/g, "\u202f"));
const pct = (v) => Number(v).toFixed(1).replace(".", ",");

let serie = INIT.serie.slice();
try {
  const sparad = JSON.parse(localStorage.getItem("mandatpingis.serie") || "[]");
  if (Array.isArray(sparad) && sparad.length) {
    const m = new Map(serie.map((r) => [r.raknade, r]));
    for (const r of sparad) if (r && r.raknade) m.set(r.raknade, r);
    serie = [...m.values()].sort((a, b) => a.raknade - b.raknade);
  }
} catch (e) { /* privat läge eller blockerad lagring — kör vidare utan historik */ }

function spara() {
  try {
    localStorage.setItem("mandatpingis.serie", JSON.stringify(serie.slice(-400)));
  } catch (e) { /* strunt samma */ }
}

function ritaChart() {
  const W = 860, H = 260, PL = 62, PR = 18, PT = 22, PB = 34;
  if (serie.length < 2) { $("chart").innerHTML = ""; return; }
  const sq = (v) => Math.sign(v) * Math.sqrt(Math.abs(v));
  const ys = serie.map((r) => sq(r.avst));
  let lo = Math.min(...ys, -12), hi = Math.max(...ys, 12);
  const span = hi - lo || 1;
  const X = (i) => PL + i * (W - PL - PR) / Math.max(serie.length - 1, 1);
  const Y = (v) => PT + (hi - sq(v)) * (H - PT - PB) / span;
  let g = "";
  for (const t of [-5000, -1000, -200, 0, 200, 1000]) {
    const y = sq(t);
    if (y < lo || y > hi) continue;
    g += `<line x1="${PL}" y1="${Y(t).toFixed(1)}" x2="${W - PR}" y2="${Y(t).toFixed(1)}" class="grid${t === 0 ? " zero" : ""}"/>`
      + `<text x="${PL - 8}" y="${(Y(t) + 3.5).toFixed(1)}" class="tick" text-anchor="end">${t === 0 ? "delat" : tal(Math.abs(t))}</text>`;
  }
  const pts = serie.map((r, i) => `${X(i).toFixed(1)},${Y(r.avst).toFixed(1)}`);
  const noll = Y(0).toFixed(1);
  const fyll = `<path d="M ${X(0).toFixed(1)},${noll} L ${pts.join(" L ")} L ${X(serie.length - 1).toFixed(1)},${noll} Z" class="fyll"/>`;
  let byten = 0, flip = "";
  serie.forEach((r, i) => {
    if (i && serie[i - 1].sd !== r.sd) {
      byten++;
      flip += `<circle cx="${X(i).toFixed(1)}" cy="${Y(r.avst).toFixed(1)}" r="4.5" class="flip"/>`;
    }
  });
  const sistI = serie.length - 1;
  $("chart").innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Avstånd i röster mellan SD och det sista mandatet över tid">`
    + g + fyll + `<polyline class="linje" points="${pts.join(" ")}"/>` + flip
    + `<circle cx="${X(sistI).toFixed(1)}" cy="${Y(serie[sistI].avst).toFixed(1)}" r="6" class="nu"/>`
    + `<text x="${PL}" y="${H - 10}" class="tick">${serie[0].tid} · ${tal(serie[0].raknade)} distrikt</text>`
    + `<text x="${W - PR}" y="${H - 10}" class="tick" text-anchor="end">${serie[sistI].tid} · ${tal(serie[sistI].raknade)} distrikt</text>`
    + `</svg>`;
  $("chart-txt").textContent = `Över den streckade linjen håller SD mandatet, under saknas det.`
    + ` Ringar markerar de ${byten} gånger mandatet bytt ägare.`;
}

function ritaBord(d) {
  const W = 860, H = 246, M = 32;
  const bw = W - M * 2, bh = H - M * 2;
  const natX = M + bw * MAJ / TOT;
  const rodB = bw * d.rod / TOT, tidoB = bw * d.tido / TOT;
  const harRod = d.avst == null ? null : d.avst < 0;   // SD saknar -> S håller det
  const bollX = harRod === null ? natX : harRod ? M + rodB * 0.55 : M + bw - tidoB * 0.55;
  const bollY = M + bh * 0.5;
  $("bord").innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img"
      aria-label="Bordtennisbord där nätet står vid 175 mandat och bollen ligger hos den sida som håller det omstridda mandatet">
    <rect x="${M}" y="${M}" width="${bw}" height="${bh}" rx="4" class="bordyta"/>
    <rect x="${M}" y="${M}" width="${rodB.toFixed(1)}" height="${bh}" class="bordhalva r" opacity="0.30"/>
    <rect x="${(M + bw - tidoB).toFixed(1)}" y="${M}" width="${tidoB.toFixed(1)}" height="${bh}" class="bordhalva t2" opacity="0.30"/>
    <rect x="${M}" y="${M}" width="${bw}" height="${bh}" rx="4" class="bordlinje"/>
    <line x1="${M}" y1="${M + bh / 2}" x2="${W - M}" y2="${M + bh / 2}" class="bordlinje" stroke-width="2"/>
    <rect x="${natX - 1.5}" y="${M - 9}" width="3" height="${bh + 18}" class="nat"/>
    <rect x="${natX - 5}" y="${M - 14}" width="10" height="6" rx="2" class="natstolpe"/>
    <rect x="${natX - 5}" y="${M + bh + 8}" width="10" height="6" rx="2" class="natstolpe"/>
    <circle id="bollen" cx="${bollX.toFixed(1)}" cy="${bollY}" r="11" class="boll"/>
    <text x="${M}" y="${H - 4}" class="bolltext">Rödgröna</text>
    <text x="${W - M}" y="${H - 4}" class="bolltext" text-anchor="end">Tidö</text>
    <text x="${natX}" y="11" class="bolltext" text-anchor="middle">175</text>
  </svg>`;
}

let forraSd = null;
function rita(d) {
  $("st-tid").textContent = "Uppdaterad " + d.hamtat;
  $("st-distrikt").textContent = `${tal(d.raknade)} av ${tal(d.ska)} distrikt · ${(d.raknade / d.ska * 100).toFixed(1)} %`;
  $("st-valdelt").textContent = "Valdeltagande " + d.valdeltagande;

  $("n-rod").textContent = d.rod;
  $("n-tido").textContent = d.tido;
  $("sida-rod").classList.toggle("win", d.rod >= MAJ);
  $("sida-tido").classList.toggle("win", d.tido >= MAJ);
  $("bar-rod").style.width = (d.rod / TOT * 100).toFixed(3) + "%";
  $("bar-tido").style.width = (d.tido / TOT * 100).toFixed(3) + "%";

  let v;
  if (!d.kontroll) {
    v = `<span class="varn">Den egna mandatfördelningen stämmer inte mot Valmyndighetens — marginalerna visas inte.</span>`;
  } else {
    const led = d.rod >= MAJ
      ? `De rödgröna har egen majoritet — med ${d.rod - MAJ + 1} mandats marginal.`
      : d.tido >= MAJ
        ? `Tidö har egen majoritet — med ${d.tido - MAJ + 1} mandats marginal.`
        : "Ingen sida når 175.";
    const lage = d.avst == null ? ""
      : d.avst >= 0
        ? ` Det omstridda mandatet: SD håller det med <strong>${tal(d.avst)}</strong> rösters marginal.`
        : ` Det omstridda mandatet: SD saknar <strong>${tal(-d.avst)}</strong> röster för att ta det.`;
    v = led + lage;
  }
  $("verdict").innerHTML = v;
  ritaBord(d);
  if (forraSd !== null && d.sd !== forraSd) {
    const b = $("bollen");
    if (b) { b.classList.remove("studs"); void b.getBBox(); b.classList.add("studs"); }
  }
  forraSd = d.sd;

  $("tbody").innerHTML = d.partier.map((p) => `<tr>`
    + `<th scope="row"><span class="dot" style="background:${p.farg || "#8E99AA"}"></span>${p.p}</th>`
    + `<td class="num stor">${p.mandat}</td>`
    + `<td class="num">${pct(p.andel)}\u202f%</td>`
    + `<td class="num dim">${pct(p.andel22)}</td>`
    + `<td class="num">${d.kontroll ? tal(p.plus) : "—"}</td>`
    + `<td class="num">${d.kontroll && p.minus != null ? tal(p.minus) : "—"}</td></tr>`).join("");

  $("k-slut").textContent = tal(d.slutRaknade);
  // Antalet distrikt är alltid färskt ur riksfilen; volymen och listan kommer
  // från /api/kvar, som kontrollerar de återstående en och en.
  if (!kvarLive) ritaKvar(INIT.kvar, Math.max(d.ska - d.raknade, 0));
  else ritaKvar(kvarLive, kvarLive.antal);
}

let kvarLive = null;
function ritaKvar(k, antal) {
  $("k-antal").textContent = tal(antal);
  const skala = k.antal ? antal / k.antal : 1;
  $("k-volym").textContent = tal(k.volym * skala);
  $("k-lista").innerHTML = (k.storsta || [])
    .map((x) => `<li><span class="kn">${x.namn}</span><span class="kv">${tal(x.est)}</span></li>`)
    .join("");
}

async function hamtaKvar() {
  try {
    const r = await fetch("/api/kvar", { cache: "no-store" });
    if (!r.ok) return;
    const k = await r.json();
    if (typeof k.antal === "number") { kvarLive = k; ritaKvar(k, k.antal); }
  } catch (e) { /* behåll ögonblicksbilden */ }
}

function laggTill(d) {
  if (d.avst == null) return;
  const t = new Date();
  const rad = {
    tid: String(t.getHours()).padStart(2, "0") + ":" + String(t.getMinutes()).padStart(2, "0"),
    raknade: d.raknade, rod: d.rod, tido: d.tido, s: d.s, sd: d.sd, avst: d.avst,
  };
  const i = serie.findIndex((r) => r.raknade === d.raknade);
  if (i >= 0) serie[i] = { ...serie[i], ...rad, tid: serie[i].tid };
  else serie.push(rad);
  serie.sort((a, b) => a.raknade - b.raknade);
  spara();
}

let fel = 0;
async function hamta() {
  try {
    const r = await fetch("/api/data", { cache: "no-store" });
    if (!r.ok) throw new Error(r.status);
    const d = await r.json();
    if (d.fel) throw new Error(d.fel);
    fel = 0;
    $("puls").classList.remove("av");
    $("pulstext").textContent = "live";
    laggTill(d);
    rita(d);
    ritaChart();
  } catch (e) {
    fel++;
    if (fel >= 2) {
      $("puls").classList.add("av");
      $("pulstext").textContent = "ingen kontakt";
    }
  }
}

function satt(lage) {
  document.documentElement.setAttribute("data-lage", lage);
  $("lage-enkel").setAttribute("aria-pressed", String(lage !== "pingis"));
  $("lage-pingis").setAttribute("aria-pressed", String(lage === "pingis"));
  try { localStorage.setItem("mandatpingis.lage", lage); } catch (e) {}
}
$("lage-enkel").addEventListener("click", () => satt("enkel"));
$("lage-pingis").addEventListener("click", () => satt("pingis"));
let startlage = "enkel";
try { startlage = localStorage.getItem("mandatpingis.lage") || "enkel"; } catch (e) {}
satt(startlage);

rita(INIT.snapshot);
ritaChart();
hamta();
hamtaKvar();
setInterval(hamta, 30000);
setInterval(hamtaKvar, 180000);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) hamta();
});
</script>
</body>
</html>
"""

open(UT, "w", encoding="utf-8").write(HTML.replace("__INIT__", INIT))
print(f"skrev {UT} ({len(HTML) + len(INIT)} tecken, {len(S)} seriepunkter)")
