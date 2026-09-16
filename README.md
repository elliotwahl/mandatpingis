# Mandatpingis

Visualiserar riksdagsräkningen 2026 medan onsdagsrösterna räknas: ett mandat
studsar mellan S och SD och avgör om de rödgröna behåller egen majoritet.

**mandatpingis.liot.se** · Netlify-sajt `liotmandatpingis`

## Uppdatera sidan

```sh
python3 kvar_uppdatera.py   # vilka uppsamlingsdistrikt som återstår (~314 anrop)
python3 hamta_data.py       # färskt riksresultat + tidsserie
python3 bygg.py             # skriver public/index.html
git commit -am "uppdatering" && git push
```

`kvar_uppdatera.py` behöver bara köras när distrikt hunnit rapportera — de två
andra är snabba och kan köras hur ofta som helst.

## Var datan kommer ifrån

Allt från Valmyndigheten, `resultat.val.se`, öppen JSON utan nyckel:

```
/data/resultat/val2026/{valtyp}[_{kod}…]_{P|S}.json
/data/valgeografi/valgeografi_val2026.json
```

`P` = preliminär, `S` = länsstyrelsernas slutliga. Sidan bygger på `P` tills `S`
är komplett — `S` dyker upp så fort omräkningen börjar och innehåller då bara de
distrikt som hunnit räknas om, med `partiMandat: null`.

## Vad som räknas här och inte hos källan

**Mandatfördelningen** räknas om lokalt med jämkade uddatalsmetoden (första
divisor 1,2, sedan 3, 5, 7 …, 349 mandat, 4 %-spärr på giltiga röster) och
stäms av mot Valmyndighetens egen `partiMandat` vid varje körning.
`hamta_data.py` vägrar skriva data om de inte stämmer överens.

**Marginalerna** (`+1 kräver`, `−1 vid tapp`) finns inte hos någon källa. De är
minsta antal röster som får ett mandat att byta ägare, räknat ur kvoterna.

**Volymen som återstår** är en uppskattning ur 2022 års utfall per kommun,
uppräknad med den ökning som syns i årets redan rapporterade kommuner. Se
kommentaren i `kvar_uppdatera.py` för varför en platt kvot inte fungerar.

## Beroenden

Läser modulerna i `../mandatmarginal/` (`hamta.py`, `rakna.py`) och dess sparade
råfiler under `../mandatmarginal/raw/` — det är dessa som blir punkterna i
pingisdiagrammet. Utan dem går sidan att bygga, men serien blir tom.

Körs med systemets python3, inga tredjepartspaket.
