// Proxar Valmyndighetens preliminära riksresultat och räknar mandatfördelningen.
//
// Varför en funktion och inte fetch direkt från sidan: resultat.val.se skickar
// inga CORS-headers, så webbläsaren får inte läsa svaret. Källan sätter själv
// cache-control: max-age=57, alltså är nytt material att vänta ungefär varje
// minut — sidan pollar därefter.
//
// Mandatfördelningen räknas här och inte i webbläsaren, så att kontrollen mot
// Valmyndighetens egen partiMandat sker på ett ställe. Stämmer de inte överens
// skickas kontroll:false och sidan vägrar visa marginaler.

const BAS = "https://resultat.val.se/data/resultat/val2026";
const TIDO = ["M", "KD", "L", "SD"];
const ROD = ["S", "V", "MP", "C"];
const MANDAT = 349;
const SPARR = 0.04;

const divisor = (n) => (n === 0 ? 1.2 : 2 * n + 1);

function fordela(roster, platser = MANDAT) {
  const t = {};
  for (const p of Object.keys(roster)) t[p] = 0;
  for (let i = 0; i < platser; i++) {
    let bast = null;
    let basta = -Infinity;
    for (const p of Object.keys(roster)) {
      const k = roster[p] / divisor(t[p]);
      if (k > basta) { basta = k; bast = p; }
    }
    t[bast]++;
  }
  return t;
}

function marginaler(roster, t) {
  const partier = Object.keys(roster);
  const ut = {};
  for (const p of partier) {
    let svagast = Infinity;
    let starkast = -Infinity;
    for (const q of partier) {
      if (q === p) continue;
      if (t[q] > 0) svagast = Math.min(svagast, roster[q] / divisor(t[q] - 1));
      starkast = Math.max(starkast, roster[q] / divisor(t[q]));
    }
    ut[p] = {
      mandat: t[p],
      roster: roster[p],
      plus: Math.round(svagast * divisor(t[p]) - roster[p]),
      minus: t[p] > 0
        ? Math.round(roster[p] - starkast * divisor(t[p] - 1))
        : null,
    };
  }
  return ut;
}

async function hamta(suffix) {
  const r = await fetch(`${BAS}/RD_${suffix}.json`, {
    headers: { "User-Agent": "mandatpingis.liot.se" },
  });
  if (!r.ok) return null;
  return r.json();
}

export default async () => {
  let prel, slut;
  try {
    [prel, slut] = await Promise.all([hamta("P"), hamta("S")]);
  } catch {
    return Response.json({ fel: "kunde inte nå Valmyndigheten" }, { status: 502 });
  }
  if (!prel) {
    return Response.json({ fel: "inget preliminärt resultat" }, { status: 502 });
  }

  const rader = prel.rosterPaverkaMandat.partiroster;
  const giltiga = prel.rosterPaverkaMandat.antalRoster;
  const alla = {};
  for (const r of rader) if (r.partikod) alla[r.partiforkortning] = r.antalRoster;
  const kvalade = {};
  for (const [p, v] of Object.entries(alla)) {
    if (v >= giltiga * SPARR) kvalade[p] = v;
  }

  const t = fordela(kvalade);
  const facit = {};
  for (const p of prel.partiMandat || []) facit[p.partiforkortning] = p.antalMandat;
  const harFacit = Object.keys(facit).length > 0;
  const kontroll = harFacit && Object.entries(facit)
    .every(([p, n]) => (t[p] || 0) === n);

  const marg = marginaler(kvalade, t);
  const sd = marg.SD;
  const avst = sd ? (t.SD >= 63 ? sd.minus : -sd.plus) : null;

  // När alla distrikt är räknade slutar sidan polla och funktionen ska sluta
  // belasta val.se. Svaret får då lång cache, så kanten serverar det utan att
  // väcka funktionen igen.
  const klar = prel.antalValdistriktRaknade >= prel.antalValdistriktSomSkaRaknas;

  return Response.json({
    klar,
    hamtat: prel.senasteRapporteringstid,
    raknade: prel.antalValdistriktRaknade,
    ska: prel.antalValdistriktSomSkaRaknas,
    roster: prel.totaltAntalRoster,
    valdeltagande: prel.valdeltagande,
    slutRaknade: slut ? slut.antalValdistriktRaknade : 0,
    slutKlar: !!(slut && slut.partiMandat &&
      slut.antalValdistriktRaknade >= slut.antalValdistriktSomSkaRaknas),
    kontroll,
    partier: rader.filter((r) => r.partikod).map((r) => ({
      p: r.partiforkortning,
      mandat: marg[r.partiforkortning]?.mandat ?? 0,
      andel: r.andelRoster,
      andel22: r.andelRosterForegaendeVal,
      plus: marg[r.partiforkortning]?.plus ?? null,
      minus: marg[r.partiforkortning]?.minus ?? null,
      farg: r.fargkod,
    })).sort((a, b) => b.mandat - a.mandat || b.andel - a.andel),
    rod: ROD.reduce((s, p) => s + (t[p] || 0), 0),
    tido: TIDO.reduce((s, p) => s + (t[p] || 0), 0),
    avst,
    sd: t.SD || 0,
    s: t.S || 0,
    tid: new Date().toISOString(),
  }, {
    headers: {
      // Källan uppdateras ungefär varje minut; håll svaret kort men inte noll,
      // så att många samtidiga läsare inte multiplicerar trafiken mot val.se.
      // Är räkningen klar ändras ingenting mer — cacha då länge.
      "cache-control": klar
        ? "public, max-age=21600, s-maxage=86400"
        : "public, max-age=20, stale-while-revalidate=40",
    },
  });
};

export const config = { path: "/api/data" };
