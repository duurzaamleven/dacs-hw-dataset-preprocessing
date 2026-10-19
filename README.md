# dacs-hw-dataset-preprocessing

Van de ruwe meetdata van **DACS-HW** (Digitale Aggregatie en Collectieve Sturing van Hybride
Warmtepompen, MOOI322001) naar getypeerde, herleidbare Parquet-tabellen. De preprocessing staat op
zichzelf: wat hier uit komt is bruikbaar voor iedereen die met deze dataset aan de slag gaat,
ongeacht welke analyse erop volgt.

> **Lees eerst [`GEBRUIKSVOORWAARDEN.md`](GEBRUIKSVOORWAARDEN.md).** Gebruik moet gemeld worden
> (woningdata) of vooraf worden opgegeven via een downloadformulier (Enexis-onderstationdata),
> uitkomsten horen gedeeld te worden met de KITE-community, en de ruwe data staat niet in deze repo
> en wordt er ook niet via verspreid.

## Wat dit is

Een veldproef in het dorp **Dalen** (gemeente Coevorden), waarin 97 hybride warmtepompen daadwerkelijk
zijn **aangestuurd**, niet alleen gemeten, met daarnaast onafhankelijke meetdata van de
wijktransformator waarop de deelnemende woningen zijn aangesloten. De openbare dataset publiceert dit
als twee archieven met zes CSV-bestanden: vijf kwartier- of uuraggregaten over de deelnemende
systemen, en één maandbestand per (gepseudonimiseerde) woning.

## Wat eruit komt

Zes Parquet-bestanden (zstd), elk de kolomvertaalde, getypeerde vorm van precies één brontabel. Zie
[`ontwerp-preprocessing.md`](ontwerp-preprocessing.md) voor de volledige kolomvertaling, de keuzes en
de aannames.

- streamend lezen uit de twee originele zips, zonder uitpakken;
- alle tz-aware tijdstempels (`tijdstip_start` in vijf van de zes tabellen) worden intern eerst als
  UTC geparsed en pas als laatste stap omgezet naar de weergavezone Europe/Amsterdam (zelfde instant,
  andere tz-metadata; zie `ontwerp-preprocessing.md` §3 en `tijd.py`); `household_monthly`'s
  `maand_start` blijft een kalendermaand, geen instant;
- de wijktrafodata is in de bron **eind-gelabeld**, de rest **begin-gelabeld**; de kwartierverschuiving
  die dat rechttrekt gebeurt op precies één plek (ontwerp §4.1);
- de toewijzing van `inlet`/`outlet` aan retour/aanvoer is een interpretatie, met een losse toets
  (`toetsen.toets_aanvoer_retour`, ontwerp §5) die de uitkomst rapporteert, niet gebruikt om de
  kolomnamen aan te passen;
- de set is klein genoeg (17 MB uitgepakt) dat elke tabel in één keer gelezen en geschreven wordt: geen
  chunking en geen voortgangsbestand, wel een manifest voor hervatbaarheid op tabelniveau.

## Beginnen

```
pip install -e ".[dev]"
pytest -q
```

Zet `dataset-dacs-hw.zip` en `wijktrafo_15min.zip` in `data/raw/` (zie GEBRUIKSVOORWAARDEN.md voor
waar je ze vandaan haalt) en draai:

```
python -m dacs_hw_preprocessing --droogloop     # laat zien wat er zou gebeuren
python -m dacs_hw_preprocessing                 # de volledige run (een kwestie van seconden)
```

Belangrijkste CLI-opties: `--raw-dir` (standaard `data/raw`), `--uit`/`--out-dir` (standaard
`data/processed`), `--docs-dir` (standaard `docs`), `--droogloop` om niets te schrijven. Zonder
`--droogloop` hervat een nieuwe aanroep een eerder afgebroken run automatisch (tabelniveau).

Alleen de aanvoer/retour-toets (ontwerp §5), zonder de rest van de pijplijn te draaien:

```
python -m dacs_hw_preprocessing.toetsen
```

## Machineleesbare beschrijving: datapackage.json

Naast `docs/datacatalogus.md` (voor mensen) schrijft de pijplijn aan het eind van elke run ook
`datapackage.json`: een machineleesbare beschrijving van de zes uitvoertabellen volgens de
[Frictionless Data Package-standaard](https://specs.frictionlessdata.io/data-package/) (kolomnamen,
types, beschrijvingen, primaire sleutels). Wordt uit de code gegenereerd, niet met de hand
bijgehouden; regenereren kan met `python -m dacs_hw_preprocessing.datapackage`.

## Documenten

| document | waarover |
|---|---|
| [`GEBRUIKSVOORWAARDEN.md`](GEBRUIKSVOORWAARDEN.md) | de voorwaarden van de datasets, de meldplicht, en hoe je de datasets zelf verkrijgt |
| [`LICENSE`](LICENSE) | de licentie van de **code**: EUPL-1.2 |
| [`ontwerp-preprocessing.md`](ontwerp-preprocessing.md) | wat deze pijplijn doet, de kolomvertaling, en de keuzes |
| [`docs/datacatalogus.md`](docs/datacatalogus.md) | metadatabeschrijving van de uitvoer voor een datacatalogus: tabellen, kolommen, kwaliteit, hoe te laden |
| `docs/data-quality.md` | gegenereerd kwaliteitsrapport, door de pijplijn zelf geschreven |
| `datapackage.json` | machineleesbare Frictionless Data Package-beschrijving, door de pijplijn zelf gegenereerd |
| [`VOORTGANG.md`](VOORTGANG.md) | bouwstatus van de repo zelf: wat af is, wat volgt, open vragen |

## Licentie

De **code** in deze repository valt onder de European Union Public Licence 1.2 (`EUPL-1.2`), zie
[`LICENSE`](LICENSE). Copyright © 2026 Kenniscentrum Duurzaam Leven, Stichting Milieu Centraal.
Besloten op 19-10-2026.

De **data** valt daar niet onder. De twee datasets die deze code verwerkt, hebben elk een eigen
data-eigenaar en een eigen voorwaarde (zie [`GEBRUIKSVOORWAARDEN.md`](GEBRUIKSVOORWAARDEN.md)):

- de **woningdata** (Projectgroep DACS-HW, aanspreekpunt Inversable): gebruik melden bij
  data@inversable.com, en uitkomsten, resultaten en analyses onder dezelfde gebruiksvoorwaarden
  delen met de KITE-community;
- de **Enexis-onderstationdata** (Enexis): beschikbaar voor onderzoek en analyse met een
  maatschappelijk doel, via een eigen aanvraagprocedure met een downloadformulier.

Geen van beide vraagt dat de rekenmethode openbaar wordt onder eenzelfde licentie; wel dat
resultaten met de KITE-community gedeeld worden. De verdeling is dus: de code onder `EUPL-1.2`, de
inzichten en resultaten onder de voorwaarden van de datasets. De ruwe data staat niet in deze
repository en wordt er ook niet via verspreid.
