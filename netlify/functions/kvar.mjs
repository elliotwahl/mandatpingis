// Hur mycket som återstår att räkna, live.
//
// Valmyndigheten säger hur MÅNGA distrikt som är oräknade, men inte hur stora
// de är — och storleken spänner från ett par hundra röster till Göteborgs
// femtontusen. Volymen måste därför räknas per distrikt.
//
// kvarlista.json innehåller de föräldrafiler som fortfarande saknade sitt
// uppsamlingsdistrikt när sidan byggdes, med förväntad volym ur 2022. Ett
// distrikt som väl rapporterat blir aldrig orapporterat igen, så det räcker att
// kontrollera dem — listan krymper monotont och svepet blir aldrig större än
// vad som faktiskt återstår. Vid bygget var det 57 filer, inte 314.
//
// Svaret cachas 5 minuter vid kanten, så antalet läsare inte multiplicerar
// trafiken mot val.se.

import lista from "./kvarlista.json" with { type: "json" };

const BAS = "https://resultat.val.se/data/resultat/val2026";
const SAMTIDIGT = 12;

async function rapporterat(nyckel) {
  // true  = uppsamlingsdistriktet har röster, alltså färdigt
  // false = fortfarande tomt
  // null  = gick inte att avgöra, räkna som kvar
  try {
    const r = await fetch(`${BAS}/${nyckel}_P.json`, {
      headers: { "User-Agent": "mandatpingis.liot.se" },
    });
    if (!r.ok) return null;
    const j = await r.json();
    for (const b of j.valkretsar || []) {
      if (b.namn && b.namn.startsWith("Uppsamlingsdistrikt")) {
        return ((b.rosterPaverkaMandat || {}).antalRoster || 0) > 0;
      }
    }
    return null;
  } catch {
    return null;
  }
}

const FARDIG = {
  "cache-control": "public, max-age=21600, s-maxage=86400",
};

export default async () => {
  // Inget kvar att kontrollera: svara utan att röra val.se alls.
  if (!lista.length) {
    return Response.json({
      antal: 0, volym: 0, storsta: [], kontrollerade: 0, osakra: 0,
      klar: true, tid: new Date().toISOString(),
    }, { headers: FARDIG });
  }

  const kvar = [];
  let osakra = 0;

  for (let i = 0; i < lista.length; i += SAMTIDIGT) {
    const grupp = lista.slice(i, i + SAMTIDIGT);
    const svar = await Promise.all(grupp.map((x) => rapporterat(x.n)));
    grupp.forEach((x, j) => {
      if (svar[j] === false) kvar.push(x);
      else if (svar[j] === null) { kvar.push(x); osakra++; }
    });
  }

  kvar.sort((a, b) => b.est - a.est);
  // Alla har rapporterat: inget mer kommer att ändras, sluta svepa.
  const klar = kvar.length === 0;
  return Response.json({
    antal: kvar.length,
    volym: kvar.reduce((s, x) => s + x.est, 0),
    storsta: kvar.slice(0, 8).map((x) => ({ namn: x.namn, est: x.est })),
    kontrollerade: lista.length,
    osakra,
    klar,
    tid: new Date().toISOString(),
  }, {
    headers: klar ? FARDIG : {
      "cache-control": "public, max-age=300, stale-while-revalidate=600",
    },
  });
};

export const config = { path: "/api/kvar" };
