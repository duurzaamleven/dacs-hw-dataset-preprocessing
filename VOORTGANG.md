# Voortgang van het bouwen van deze repo

Bijgewerkt: 24-09-2026, aan het eind van de eerste bouwsessie. De pijplijn is compleet en getest, en
er is een volledige run gedaan op de echte data (de set is klein genoeg dat dit geen aparte,
onbeheerde stap hoeft te zijn).

## Klaar

- Skelet gebouwd naar het voorbeeld van de WarmingUP-preprocessing (`CLAUDE.md`, `README.md`,
  `GEBRUIKSVOORWAARDEN.md`, `LICENSE.md`, `pyproject.toml`, pakketstructuur), geschaald naar een veel
  kleinere set.
- **Gebruiksvoorwaarden alsnog nagelopen** (in de afnemende repo stond dat dit nog niet was gedaan):
  de KITE-pagina van DACS-HW is gedecodeerd (mhtml, quoted-printable) en gelezen. Twee datasets, twee
  verschillende data-eigenaren (Projectgroep DACS-HW/Inversable voor de woningdata, Enexis voor de
  onderstationdata), geen van beide met een licentienaam, beide beperkt tot "onderzoek en analyse met
  een maatschappelijk doel". Zie `GEBRUIKSVOORWAARDEN.md`.
- Ruwe data als **hardlink** (niet kopie) in `data/raw/` gezet (`New-Item -ItemType HardLink`, `mklink
  /H` werkte niet betrouwbaar vanuit deze sessie se shell); sha256 geverifieerd gelijk aan de bron en
  aan `literatuur/MANIFEST.md` van de afnemende repo. Bevestigd gitignored (`git status --ignored`).
- Pijplijn gebouwd: `kolommen.py` (kolomvertaling, overgenomen uit de bron-utils), `tijd.py`
  (UTC-parsing plus de Europe/Amsterdam-weergavezone-omzetting, met bronvermelding: eindrapport p. 10,
  "dorp Dalen (gemeente Coevorden)"), `lezers.py` (de zes `lees_*`-functies plus de
  kwartierverschuiving van de wijktrafodata, op precies één plek), `tabellen.py` (expliciete
  `pyarrow`-schema's per tabel), `manifest.py` (sha256, `UITVOER_CONTRACT_VERSIE`, atomisch schrijven,
  zowel voor pandas- als arrow-tabellen), `toetsen.py` (de aanvoer/retour-toets, als losse module/CLI-
  subcommando), `kwaliteitsrapport.py` (schrijft `docs/data-quality.md`: sleutelcontrole, dekking,
  een generieke zomertijdcontrole rond elke DST-wisseling), `datapackage.py` (genereert
  `datapackage.json` uit de `pyarrow`-schema's), `pijplijn.py` (orchestratie en CLI: `--raw-dir`,
  `--uit`, `--docs-dir`, `--droogloop`).
- **Geen chunking, geen voortgangsbestand**: de set is 17 MB uitgepakt (ontwerp §1), dus elke tabel
  wordt in één keer gelezen en geschreven; alleen een manifest voor hervatbaarheid op tabelniveau.
- 46 pytests geschreven en groen: kolomvertaling en typen (`test_lezers.py`), tijdzone-omzetting
  (`test_tijd.py`, inclusief een expliciete zomer/wintertijd-instantcontrole), manifest en atomisch
  schrijven voor zowel pandas- als arrow-tabellen (`test_manifest.py`), datapackage-consistentie
  (`test_datapackage.py`, met de aanpak van de WarmingUP-repo: elk schemaveld moet in het datapackage
  staan en omgekeerd), de aanvoer/retour-toets (`test_toetsen.py`), de zomertijd- en
  sleutelcontrolelogica van het kwaliteitsrapport (`test_kwaliteitsrapport.py`) en de volledige
  pijplijn end-to-end (`test_pijplijn.py`, hervatten, droogloop, tijdzonecontrole). Alle tests draaien
  op synthetische fixtures; een tiental tests draait bovendien tegen de echte data en slaat zichzelf
  over als `data/raw/` ontbreekt.
- **Volledige run gedraaid op de echte data** (`python -m dacs_hw_preprocessing -v`), 24-09-2026,
  1,4-3,1 s. Rijaantallen exact gelijk aan ontwerp-preprocessing.md §1 (zelf overgenomen uit de
  ontwerpparagraaf van de afnemende repo, hier onafhankelijk herbevestigd op de eigen leescode):
  43.962 / 2.763 / 11.018 / 1.334 / 69.320 / 66.
- **Aanvoer/retour-toets gedraaid**: 99,16% van 39.103 kwartieren, mediaan 1,29 °C (kwartielen
  0,39-2,24 °C). Dit is EXACT gelijk aan de eerder gerapporteerde uitkomst (99,16% van 39.103,
  mediaan 1,29 °C) die als referentie is meegegeven bij de start van deze sessie; de nieuwe,
  losstaande leesroute reproduceert die uitkomst dus onafhankelijk.
- **Zomertijdcontrole uitgevoerd** op de volledige verwerkte uitvoer (zie `docs/data-quality.md` en
  `docs/datacatalogus.md` §4.1): `heatpump_15m` en `smartmeters_gas_hourly` tonen GEEN enkel gat of
  dubbele tijdstempel rond vier DST-wisselingen (verwacht van een bron die al in UTC is opgeslagen);
  `heatpump_steering_15m` toont één gat bij de maartwissel 2025, maar die tabel is sparse per ontwerp
  (geen DST-signaal); `wijktrafo_15min` toont TWEE gaten, allebei bij een OKTOBERwissel (2024: het
  volledige tweede dubbelzinnige uur ontbreekt, vier kwartieren; 2025: drie van de vier kwartieren
  van dat uur), geen enkel gat bij een maartwissel, en nergens dubbele tijdstempels. Dit patroon
  (alleen oktober, nooit maart) is dezelfde signatuur als bij de WarmingUP-preprocessing en wijst op
  een lokale-tijd-verwarring ergens in de Enexis-meetketen; niet bewezen, wel aannemelijk gemaakt.
- `docs/datacatalogus.md` geschreven met citaten met paginanummer uit het eindrapport (locatie: dorp
  Dalen, gemeente Coevorden; 255 woningen op één wijktransformator van 400 kVA; woningen gebouwd
  1959-1994; 97 geplaatste toestellen tegenover 92 gebruikt voor een simulatie tegenover 93 unieke
  `custom_id`'s in de verwerkte data, een discrepantie die het rapport zelf niet toelicht).

## Gemeten getallen (samenvatting)

| tabel | rijen | periode (UTC) |
|---|---:|---|
| `heatpump_15m` | 43.962 | 2024-08-31 22:00 .. 2025-12-04 10:45 |
| `heatpump_steering_15m` | 2.763 | 2024-11-28 16:30 .. 2025-06-02 21:15 |
| `smartmeters_gas_hourly` | 11.018 | 2024-08-31 22:00 .. 2025-12-03 23:00 |
| `household_monthly` | 1.334 (93 woningen) | 2024-09 .. 2025-11 |
| `wijktrafo_15min` | 69.320 | 2023-12-04 23:00 .. 2025-12-04 10:45 (na verschuiving) |
| `metadata` | 66 | n.v.t. |

Volledige-runduur: 1,4-3,1 s (herhaalde metingen op dezelfde machine; de set is klein genoeg dat dit
geen betekenisvolle prestatie-eis is).

## Niet gedaan / bewust uitgesteld

- **Geen sentinelwaarden of plausibiliteitsvlaggen** (zoals `q_flag_*__bool` bij WarmingUP/IM3): het
  ontwerp van de afnemende repo noemt hiervoor geen specifieke grenzen voor DACS-HW, en de bron
  documenteert ontbrekende metingen al als lege velden. Een latere sessie kan dit alsnog toevoegen als
  daar behoefte aan blijkt (bijvoorbeeld een boventemperatuurgrens voor `temp_aanvoer`/`temp_retour`).
- **Geen conceptmelding** aan de twee data-eigenaren opgesteld; dat is een aparte stap na deze
  bouwsessie, met de vier gebreken uit ontwerp-preprocessing.md §7 als inhoud.
- **Geen GitHub-repo aangemaakt en niet gepusht**, zoals gevraagd; dat gebeurt na controle door de
  opdrachtgever.
- De discrepantie tussen 97/92/93 systemen (§2 van de datacatalogus) is benoemd, niet verklaard.
- De precieze oorzaak van de zomertijdgaten in `wijktrafo_15min` bij Enexis is niet verder onderzocht
  dan de aannemelijke verklaring in `docs/datacatalogus.md` §4.1.

## Open vragen voor een volgende sessie of voor de opdrachtgever

1. Klopt de aanname dat `outlet_water_temperature` de aanvoer is en `inlet_water_temperature` de
   retour? De toets (99,16% aanvoer boven retour) ondersteunt het, bewijst het niet.
2. Zijn er plausibiliteitsgrenzen gewenst voor de temperatuur- en vermogenskolommen, analoog aan de
   WarmingUP-/IM3-preprocessing?
3. Is de verklaring voor de zomertijdgaten in `wijktrafo_15min` (lokale tijd bij Enexis) na te gaan,
   bijvoorbeeld door de vraag aan Enexis voor te leggen samen met de gebruiksmelding?
4. Waarom noemt het eindrapport drie verschillende aantallen systemen (97 geplaatst, p. 8; 92 gebruikt
   voor een simulatie, p. 19) tegenover 93 unieke `custom_id`'s in de verwerkte
   `household_monthly`-tabel?
