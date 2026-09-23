# Datacatalogus: DACS-HW-dataset (voorbewerkte uitvoer)

Dit document beschrijft de UITVOER van deze repo: de getypeerde Parquet-tabellen die
`dacs_hw_preprocessing` van de twee ruwe DACS-HW-archieven maakt. Het is bedoeld om in een
datacatalogus te zetten naast (een verwijzing naar) de dataset zelf.

**Deze repo is niet de data-eigenaar en de ruwe data staat hier niet in.** Twee verschillende
data-eigenaren (Projectgroep DACS-HW/Inversable voor de woningdata, Enexis voor de
onderstationdata); licentie, meldplicht en herkomst staan in
[`GEBRUIKSVOORWAARDEN.md`](../GEBRUIKSVOORWAARDEN.md). Dit document beschrijft alleen wat de
pijplijn ervan maakt.

Alle kolomnamen volgen de conventie
[`physiquant__unit`](https://github.com/energietransitie/physiquant__unit): eenheid na de dubbele
underscore.

Rijaantallen, dekkingscijfers en de zomertijd- en aanvoer/retour-toetsuitkomsten in dit document zijn
afgelezen uit de echte, volledige-run-uitvoer (17-09-2026 opgehaald, gedraaid 24-09-2026; zie
[`VOORTGANG.md`](../VOORTGANG.md) en [`data-quality.md`](data-quality.md), dat de pijplijn zelf
schrijft), niet uit het ontwerp of het geheugen overgenomen.

## 1. Wat deze set is

Voorbewerkte meetdata van **DACS-HW** (Digitale Aggregatie en Collectieve Sturing van Hybride
Warmtepompen), MOOI322001, een consortium van Enablemi (penvoerder), Enexis, Intergas, Inversable,
Voorstroom, Samen Energie Neutraal en de TU/e, afgerond december 2025.

- **Zes tabellen**, gepubliceerd als twee archieven: woningdata (vijf CSV's: vijf kwartier-/
  uurbestanden plus een maandbestand) en Enexis-onderstationdata (één CSV, de wijktransformator).
- **Rijaantallen** (17-09-2026 opgehaald, volledige run 24-09-2026): 43.962 in `heatpump_15m`, 2.763
  in `heatpump_steering_15m`, 11.018 in `smartmeters_gas_hourly`, 1.334 in `household_monthly`
  (93 unieke woningen), 69.320 in `wijktrafo_15min`, 66 in `metadata`.
- **Gemeten periode.** `heatpump_15m`: 2024-08-31 22:00 t/m 2025-12-04 10:45 UTC.
  `heatpump_steering_15m` (alleen kwartieren met minstens twee gestuurde warmtepompen):
  2024-11-28 16:30 t/m 2025-06-02 21:15 UTC. `smartmeters_gas_hourly`: 2024-08-31 22:00 t/m
  2025-12-03 23:00 UTC. `household_monthly`: september 2024 t/m november 2025 (15 kalendermaanden).
  `wijktrafo_15min`: 2023-12-04 23:00 t/m 2025-12-04 10:45 UTC (na de kwartierverschuiving van §4.1;
  merk op dat deze reeks negen maanden vóór de warmtepompdata begint).
- **Data-eigenaar, licentie en meldplicht:** zie [`GEBRUIKSVOORWAARDEN.md`](../GEBRUIKSVOORWAARDEN.md).
  Kort samengevat: twee verschillende eigenaren, geen van beide noemt een licentienaam, gebruik is
  beperkt tot onderzoek/analyse met een maatschappelijk doel en moet gemeld (woningdata) of vooraf
  via een downloadformulier opgegeven worden (Enexis-data).
- **Hoe je de brondata zelf verkrijgt:** eveneens in GEBRUIKSVOORWAARDEN.md (URL en sha256 voor de
  woningdata; voor de Enexis-data een downloadformulier, geen vaste URL).

## 2. De veldproef: locatie en steekproef

Bron voor deze paragraaf: het eindrapport (Bisschop, De Boer, Van Hooijdonk, Hormann, Li, Matien,
Paterakis, Van Urk, Visser & Wolterink, *Digitale Aggregatie en Collectieve Sturing van Hybride
Warmtepompen, Openbare versie*, MOOI322001, Enablemi e.a., 23 januari 2026); noch het archief zelf,
noch de KITE-pagina documenteert dit.

**Locatie.** "*Een fysieke pilot heeft plaatsgevonden in het dorp Dalen (gemeente Coevorden). In de
desbetreffende wijk zijn 255 woningen aangesloten via laagspanningskabels op 1 wijktransformator.
Deze wijktransformator heeft een totaal vermogen van 400 kVA*" (p. 10). Enexis selecteerde deze wijk
in Dalen omdat hij "*voldoende aangesloten [woningen]*" telde, "*achter één wijktransformator*" hing
en "*een divers woning[bestand]*" had (p. 8).

**Woningkenmerken.** "*De woningen zijn gebouwd in de periode van circa 1959 tot 1994, met een
duidelijke spreiding over de jaren zestig, zeventig en negentig*" (p. 10); binnen de wijk komen
tussenwoningen, twee-onder-een-kapwoningen en vrijstaande woningen voor. Het rapport noemt dit
expliciet "*een realistische afspiegeling van een gemiddelde Nederlandse woonwijk*" (p. 10), zonder
dat verder statistisch te onderbouwen (geen vergelijking met CBS-cijfers zoals bij het
WarmingUP-eindrapport).

**Aantal deelnemende systemen.** "*In totaal zijn 97 toestellen in Dalen geplaatst en getest*" (p. 8).
Een aparte simulatieanalyse in het rapport gebruikt meetdata van "*92 hybride warmtepompsystemen in
Dalen*" (p. 19); het verschil tussen 97 geplaatste en 92 gebruikte systemen is in het rapport niet
toegelicht. De openbare kwartierbestanden dekken minder systemen dan beide getallen: de tellerkolommen
(§6) lopen van 26 tot 88 met mediaan 75 voor `heatpump_15m`, en `household_monthly` bevat 93 unieke
woningen; de set verliest dus onderweg systemen (bijvoorbeeld door tijdelijke uitval of latere
aansluiting) maar niet dramatisch.

**Wat niet is vastgesteld**: individuele werving, opt-out-gronden, en of er een representativiteitstoets
tegen landelijke cijfers is uitgevoerd (in tegenstelling tot het WarmingUP-eindrapport, dat dit wel
deed). Wie dat nodig heeft, moet bij het consortium (contact via KITE) navragen.

## 3. Meetopstelling

Uit `README_dataset.md` (bijgeleverd in `dataset-dacs-hw.zip`) en `metadata.csv`:

- **Warmtepompsystemen** (`heatpump_15m`, `heatpump_steering_15m`): per aangesloten systeem werden
  elektrisch verbruik, door de ketel en door de warmtepomp geleverde warmte, binnentemperatuur,
  setpoint, en de water-in-/uittemperatuur van het toestel bijgehouden; gepubliceerd als
  kwartierstatistiek (gemiddelde, mediaan, kwartielen) over de systemen die in dat kwartier data
  leverden, NIET als tijdreeks per systeem (ontwerp-preprocessing.md §1).
- **Aansturing** (`heatpump_steering_15m`): een vermogenslimiet werd opgelegd aan een deel van de
  warmtepompen; deze tabel bevat alleen kwartieren waarin minstens twee toestellen tegelijk werden
  aangestuurd, met het aantal gestuurde toestellen en de opgelegde limiet. "*Source heater
  identifiers are not published*" (`README_dataset.md`): welke toestellen precies gestuurd werden, is
  niet uit de openbare set af te leiden.
- **Slimme meters** (`smartmeters_gas_hourly`, `household_monthly`): gasgebruik per uur als
  meteraggregaat, en per woning per maand het totale elektriciteits- en gasverbruik plus het
  toegeschreven warmtepompaandeel.
- **Wijktransformator** (`wijktrafo_15min`): Enexis meette stroom, spanning en belasting per fase
  (L1/L2/L3) op de ene wijktransformator (400 kVA, p. 10) waarachter de 255 woningen van de pilotwijk
  hangen, onafhankelijk van de warmtepompmeting. Volgens `Toelichting DACS-HW Enexis Dataset.txt`
  gaat het om "*Stroom (eenheid A, resolutie 0,01 A)*", "*Spanning (eenheid V, resolutie 0,001 V)*"
  en "*Belasting (eenheid kW, resolutie 0,01 kW)*", elk apart naar een kwartiergemiddelde
  herbemonsterd (zie §4.2 hieronder). Sensormerk, meetonzekerheid en kalibratie van de individuele
  meters zijn in de meegeleverde documentatie niet gespecificeerd; **niet vastgesteld** in wat deze
  repo weet.
- **Ketel- en thermostaatlogging**: begrepen in de `heatpump_15m`-statistieken (ketelwarmte,
  binnentemperatuur, setpoint); geen aparte brontabel zoals bij WarmingUP.

## 4. Tijdconventies

- `heatpump_15m`, `heatpump_steering_15m`, `smartmeters_gas_hourly`, `wijktrafo_15min`: `tijdstip_start`
  is **tz-aware, weergavezone Europe/Amsterdam** (`timestamp[ns, tz=Europe/Amsterdam]`). De bron
  draagt UTC (ISO-8601-tijdstempels, deels met `Z`-suffix, deels met een expliciete `+00:00`-offset);
  deze pijplijn parseert dat eerst naar UTC (`tijd.naar_utc_tijdstip`, de interne rekenbasis) en zet
  het pas als allerlaatste stap vóór het schrijven om naar de weergavezone
  (`tijd.naar_weergave_tijdzone`, `tz_convert`, geen `tz_localize`): **het instant verandert niet,
  alleen de tz-metadata.**

  Onderbouwing voor Europe/Amsterdam als weergavezone (analoog aan de WarmingUP- en
  IM3-preprocessing): de veldproef is één fysieke locatie, het dorp Dalen, gemeente Coevorden,
  provincie Drenthe (eindrapport p. 10, zie §2), dus Europees Nederland; de KITE-projectpagina
  bevestigt dit ("een uitgebreide veldtest met 100 hybride warmtepompen in woningen ... aangesloten
  op één wijktransformator", zie GEBRUIKSVOORWAARDEN.md).
- `household_monthly`: `maand_start` blijft een **lokale kalendermaand** (`Europe/Amsterdam`), als
  naïeve timestamp (GEEN tijdzone), NIET omgerekend naar UTC; de bron zegt dit expliciet
  (`README_dataset.md`, "Time interpretation": *"Monthly `month` values are Europe/Amsterdam calendar
  labels ... not an instant or UTC timestamp"*). Een omzetting naar UTC zou de maand zelf kunnen laten
  verschuiven.
- **Kwartierverschuiving wijktrafodata (ontwerp §4.1).** De bron is EIND-gelabeld
  (`Toelichting DACS-HW Enexis Dataset.txt`: *"Het gemiddelde is het gemiddelde signaal in het
  kwartier (15 min) voorafgaand aan tijdstip waarop het gemiddeld is genoteerd"*), de rest van deze
  dataset is BEGIN-gelabeld (`README_dataset.md`: *"`interval_start` is the beginning of the
  represented period"*). Deze pijplijn schuift de wijktrafodata daarom één kwartier terug bij het
  inlezen, op precies één plek.

### 4.1 Zomertijdcontrole

Uitgevoerd op de volledige verwerkte uitvoer (24-09-2026), rond elke DST-wisseling (laatste zondag
van maart/oktober, 01:00 UTC) binnen de gedekte periode van elke tijdreeks-tabel; methode en cijfers
ook in [`data-quality.md`](data-quality.md) (`kwaliteitsrapport._zomertijdcontrole`, door de pijplijn
zelf gegenereerd). **Geen correctie in de data.**

- **`heatpump_15m` en `smartmeters_gas_hourly`: geen enkel gat en geen dubbele tijdstempels** rond
  vier DST-wisselingen (oktober 2024, maart 2025, oktober 2025). Dit is precies wat verwacht mag
  worden van een bron die al in UTC is opgeslagen (in tegenstelling tot een bron die lokale tijd
  registreert): de UTC-klok springt nooit, dus een correcte UTC-opslag laat geen DST-sporen na.
- **`heatpump_steering_15m`**: één gat rond de maartwissel 2025 (120 minuten), maar deze tabel is
  sparse per ontwerp (alleen kwartieren MET aansturing); een gat hier betekent "geen aansturing", geen
  DST-signaal, en wordt door de controle ook niet als zodanig gemarkeerd.
- **`wijktrafo_15min`: TWEE gaten gevonden, allebei bij een oktoberwissel, geen enkel gat bij een
  maartwissel.** Bij de wisseling van 2024-10-27 ontbreekt het VOLLEDIGE tweede, dubbelzinnige uur
  (01:00-01:59 UTC, vier kwartieren); bij die van 2025-10-26 ontbreken drie van de vier kwartieren
  van datzelfde uur (01:00, 01:15, 01:30 UTC; 01:45 UTC is wel aanwezig). Geen enkel gat bij de
  maartwissels van 2024 of 2025, en geen enkele dubbele tijdstempel rond welke wisseling dan ook.

  Dit is hetzelfde patroon als bij de WarmingUP-preprocessing (`boiler_temp`, zie die repo's
  datacatalogus §4.1): een gat dat uitsluitend rond de OKTOBERwissel optreedt en niet rond de
  maartwissel past bij een keten waarin ergens vóór de UTC-opslag lokale tijd is gebruikt, en waarbij
  bij de omzetting de TWEEDE (wintertijd-)doorgang van het dubbelzinnige lokale uur (02:00-02:59, dat
  zowel als CEST=UTC 00:00-00:59 als CET=UTC 01:00-01:59 voorkomt) verloren gaat. Dit is hier een
  **aannemelijke verklaring, geen vaststelling**: de wijktrafodata komt van Enexis, een andere
  meetketen dan de warmtepompdata (die zelf geen enkel spoor van dit patroon toont), en de precieze
  oorzaak bij Enexis is met de middelen van deze repo niet te achterhalen. Het ontbrekende uur wordt
  hier niet teruggezet; de bron zelf documenteert bovendien dat een rij zonder enige geldige meting
  simpelweg ontbreekt (`Toelichting DACS-HW Enexis Dataset.txt`: *"Als alle meetwaarden op een rij ...
  NULL zijn dan ontbreekt deze rij/dit interval in de dataset"*), dus het is niet aan deze pijplijn te
  onderscheiden van willekeurige uitval met dezelfde timing.
- **Geen dubbele tijdstempels** in enige tabel, op geen enkele DST-wisseling en ook niet daarbuiten
  (zie de sleutelcontrole in `data-quality.md`, waar elke primaire sleutel op de volledige uitvoer nul
  dubbelingen telt).

## 5. Uitvoertabellen

Alle tabellen zijn Parquet, zstd-gecomprimeerd, elk in één stuk weggeschreven (geen partitionering:
de kwartier-/uurbestanden zijn aggregaten, geen tijdreeks per woning; ontwerp-preprocessing.md §1).

### 5.1 `heatpump_15m.parquet`

**43.962 rijen.** 15-minutenaggregaat over de warmtepompsystemen die in dat kwartier data leverden.

| kolom | type | eenheid | beschrijving | bronkolom |
|---|---|---|---|---|
| `tijdstip_start` | timestamp(ns, Europe/Amsterdam) | | begin van het kwartierinterval | `interval_start` |
| `n_wp_online` | int32 | | aantal systemen dat minstens één metriek meldde | `hp_online_count` |
| `n_wp_ketel` | int32 | | aantal systemen met geldige ketelwarmte | `boiler_thermal_hp_count` |
| `q_ketel_gem`/`_med`/`_q25`/`_q75__kWh` | float32 | kWh | door de ketel geleverde warmte (NIET het gasvolume) | `boiler_thermal_energy_kwh_*` |
| `n_wp_warmtepomp` | int32 | | aantal systemen met geldige warmtepompwarmte | `heatpump_thermal_hp_count` |
| `q_warmtepomp_gem`/`_med`/`_q25`/`_q75__kWh` | float32 | kWh | door de warmtepomp (elektrisch) geleverde warmte | `heatpump_thermal_energy_kwh_*` |
| `n_wp_elektriciteit` | int32 | | aantal systemen met geldig elektrisch verbruik | `electricity_hp_count` |
| `e_warmtepomp_gem`/`_med`/`_q25`/`_q75__kWh` | float32 | kWh | elektrisch verbruik van de warmtepompsystemen | `electricity_consumption_kwh_*` |
| `n_wp_temp_binnen` | int32 | | aantal systemen met geldige binnentemperatuur | `room_temperature_hp_count` |
| `temp_binnen_gem`/`_med`/`_q25`/`_q75__degC` | float32 | °C | gemeten binnentemperatuur | `room_temperature_c_*` |
| `n_wp_setpoint` | int32 | | aantal systemen met geldig setpoint | `room_setpoint_hp_count` |
| `temp_setpoint_gem`/`_med`/`_q25`/`_q75`/`_std__degC` | float32 | °C | ingestelde temperatuur, als enige ook met std | `room_setpoint_c_*` |
| `n_wp_temp_retour` | int32 | | aantal systemen met geldige inlet-temperatuur | `inlet_water_temperature_hp_count` |
| `temp_retour_gem`/`_med`/`_q25`/`_q75__degC` | float32 | °C | retourtemperatuur (interpretatie, zie §5.1.1) | `inlet_water_temperature_c_*` |
| `n_wp_temp_aanvoer` | int32 | | aantal systemen met geldige outlet-temperatuur | `outlet_water_temperature_hp_count` |
| `temp_aanvoer_gem`/`_med`/`_q25`/`_q75__degC` | float32 | °C | aanvoertemperatuur (interpretatie, zie §5.1.1) | `outlet_water_temperature_c_*` |

#### 5.1.1 De inlet/outlet-interpretatie, getoetst

`outlet_water_temperature` is hier vertaald naar `temp_aanvoer` (het water dat de warmtepomp
verlaat, naar de woning) en `inlet_water_temperature` naar `temp_retour` (het water dat
terugkomt). **Dit is een naamgevingskeuze van deze pijplijn, geen letterlijke bronclaim**; de bron
documenteert zelf niet welke kant "inlet" en "outlet" is ten opzichte van de woning.

Deze interpretatie is getoetst (`toetsen.toets_aanvoer_retour`, volledige uitvoer, 24-09-2026): van
de 39.103 kwartieren met gemeten warmtelevering (`q_warmtepomp_gem__kWh > 0`) én beide temperaturen
beschikbaar, ligt in **99,16%** de aanvoer boven de retour, met een mediaan verschil van **1,29 °C**
(kwartielen 0,39-2,24 °C). Dat is consistent met de interpretatie, al ligt het verschil in absolute
zin klein (mediaan onder anderhalve graad); bij 0,84% van de kwartieren ligt de aanvoer juist ONDER de
retour, wat bij een net gestopte of net startende warmtepomp (vergelijkbaar met de
`temp_retour > temp_aanvoer`-uitzondering in de WarmingUP-preprocessing) fysisch plausibel is en hier
niet nader onderzocht is. **Dit is een bevinding, geen bewezen feit**: de toets bevestigt de
interpretatie niet weerlegt haar niet, en de kolomnamen zijn niet met terugwerkende kracht aangepast.

### 5.2 `heatpump_steering_15m.parquet`

**2.763 rijen**, periode 2024-11-28 16:30 t/m 2025-06-02 21:15 UTC. Alleen kwartieren met minstens
twee gestuurde warmtepompen; een afwezig kwartier betekent "geen (of één) warmtepomp gestuurd", geen
waarde nul.

| kolom | type | eenheid | beschrijving | bronkolom |
|---|---|---|---|---|
| `tijdstip_start` | timestamp(ns, Europe/Amsterdam) | | begin van het kwartierinterval | `interval_start` |
| `n_wp_gestuurd` | int32 | | aantal distincte gestuurde warmtepompen | `steered_hwp_count` |
| `p_limiet_gem__W` | float32 | W | gemiddeld opgelegd vermogenslimiet | `power_limit_kw_mean` (x1000) |
| `p_limiet_med__W` | float32 | W | mediaan opgelegd vermogenslimiet | `power_limit_kw_median` (x1000) |

Dekking (§6): `n_wp_gestuurd` loopt van 2 tot 87, mediaan 60. De brontabel publiceert geen
toestel-identifiers (`README_dataset.md`: *"Source heater identifiers are not published"*), dus welke
toestellen precies gestuurd werden, is uit deze tabel niet af te leiden.

### 5.3 `smartmeters_gas_hourly.parquet`

**11.018 rijen**, periode 2024-08-31 22:00 t/m 2025-12-03 23:00 UTC. Uuraggregaat gasgebruik over de
slimme meters die dat uur een geldige meting leverden.

| kolom | type | eenheid | beschrijving | bronkolom |
|---|---|---|---|---|
| `tijdstip_start` | timestamp(ns, Europe/Amsterdam) | | begin van het uurinterval | `interval_start` |
| `n_meter_gas` | int32 | | aantal meters met een geldige gaswaarde | `gas_meter_count` |
| `g_gebruik_gem`/`_med`/`_q25`/`_q75__m3` | float32 | m³ | gasgebruik per bijdragende meter | `gas_delivered_m3_*` |

### 5.4 `household_monthly.parquet`

**1.334 rijen, 93 unieke woningen**, periode september 2024 t/m november 2025 (15 kalendermaanden).
Eén rij per (gepseudonimiseerde) woning per kalendermaand; een woning-maand kan ontbreken als er in
die maand geen enkele geldige bron was.

| kolom | type | eenheid | beschrijving | bronkolom | opmerking |
|---|---|---|---|---|---|
| `maand_start` | timestamp(ns), GEEN tz | | kalendermaand, Europe/Amsterdam-label | `month` | zie §4 |
| `custom_id__str` | string | | gepseudonimiseerde woningsleutel | `custom_id` | `metadata.csv` noemt dit veld abusievelijk `id` (§8) |
| `e_geleverd_tot__kWh` | float32 | kWh | totaal aan het net onttrokken elektriciteit | `total_electricity_delivered_kwh` | |
| `e_teruglevering_tot__kWh` | float32 | kWh | totaal teruggeleverde elektriciteit | `total_electricity_returned_kwh` | |
| `e_net_tot__kWh` | float32 | kWh | netto elektriciteitsverbruik | `total_net_electricity_consumption_kwh` | kan negatief zijn |
| `g_geleverd_tot__m3` | float32 | m³ | totaal geleverd gasvolume | `total_gas_delivered_m3` | |
| `e_warmtepomp_tot__kWh` | float32 | kWh | elektriciteitsverbruik van het warmtepompsysteem | `hp_electricity_kwh` | zie de `hp_`/`hwp_`-tegenstrijdigheid in §8 |
| `g_warmtepomp_tot__m3` | float32 | m³ | gasgebruik gerapporteerd door het hybride systeem | `hp_gas_m3` | idem |

Lege velden betekenen "geen meting beschikbaar", geen nul (`README_dataset.md`); hier niet ingevuld,
dus `NaN` blijft `NaN`. `custom_id__str` is stabiel binnen deze dataset maar **niet** te koppelen aan
de vijf kwartier-/uurbestanden (dezelfde bron, sectie "Privacy").

### 5.5 `wijktrafo_15min.parquet`

**69.320 rijen**, periode 2023-12-04 23:00 t/m 2025-12-04 10:45 UTC (na de kwartierverschuiving van
§4). Stroom, spanning en belasting per fase van de ene wijktransformator (400 kVA) achter de 255
woningen van de pilotwijk in Dalen (eindrapport p. 10).

| kolom | type | eenheid | beschrijving | bronkolom | opmerking |
|---|---|---|---|---|---|
| `tijdstip_start` | timestamp(ns, Europe/Amsterdam) | | begin van het kwartierinterval | `timestamp` | een kwartier teruggeschoven, zie §4 |
| `i_trafo_L1`/`L2`/`L3__A` | float32 | A | stroom per fase | `stroom_L1`/`L2`/`L3` | |
| `u_trafo_L1`/`L2`/`L3__V` | float32 | V | spanning per fase | `spanning_L1`/`L2`/`L3` | |
| `p_trafo_L1`/`L2`/`L3__W` | float32 | W | belasting per fase | `belasting_L1`/`L2`/`L3` | x1000; **stroom x spanning != belasting**, zie §4.2 van het ontwerp |

Geen woningtoewijzing: dit is één transformator zonder koppeling naar individuele woningen of
warmtepompsystemen.

### 5.6 `metadata.parquet`

**66 rijen.** Kolomdefinities uit de bron zelf, ongewijzigd overgenomen (alle velden als tekst; een
lege cel is hier letterlijk een lege tekst, geen `NaN`). Bevat zelf twee bekende fouten (§8):
niet-bestaande bestandsnamen, en het veld `id` waar de data `custom_id` heet.

## 6. Kwaliteit en dekking

Cijfers uit [`data-quality.md`](data-quality.md) (door de pijplijn zelf geschreven, volledige run
24-09-2026, `uitvoer_contract_versie` `2026-09-24-eerste-opzet`).

**Sleutelcontrole**: alle zes primaire sleutels (§9) zijn op de volledige uitvoer geverifieerd
UNIEK: nul dubbele sleutels in elke tabel.

**Dekking** (coveragekolommen): `n_wp_online` (`heatpump_15m`) loopt van 26 tot 88, mediaan 75;
`n_wp_gestuurd` (`heatpump_steering_15m`) van 2 tot 87, mediaan 60; `n_meter_gas`
(`smartmeters_gas_hourly`) van 20 tot 82, mediaan 80. De verzameling bijdragende systemen wisselt per
interval (`README_dataset.md` waarschuwt hier zelf voor); een verandering in een statistiek kan dus
deels een verandering in de POPULATIE zijn, niet in het gedrag.

**Geen sentinelwaarden en geen plausibiliteitsvlaggen** zoals bij de WarmingUP- of
IM3-preprocessing: de bron documenteert ontbrekende metingen al als lege CSV-velden (die als `NaN`
overkomen), en deze pijplijn voegt daar geen eigen bereikcontrole aan toe (ontwerp-preprocessing.md
noemt geen plausibiliteitsgrenzen voor deze dataset; een latere sessie kan dit alsnog toevoegen als
daar behoefte aan blijkt).

**Zomertijdcontrole**: zie §4.1.

**Aanvoer/retour-toets**: zie §5.1.1.

## 7. Hoe te laden

Elke tabel is een gewoon, volledig Parquet-bestand (geen per-woningpartitionering: de
kwartier-/uurbestanden zijn aggregaten, zie §1):

```python
import pandas as pd

heatpump_15m = pd.read_parquet("data/processed/heatpump_15m.parquet")
household_monthly = pd.read_parquet("data/processed/household_monthly.parquet")
```

`datapackage.json` (zie §9) beschrijft alle zes tabellen machineleesbaar, inclusief kolomtypen,
beschrijvingen en primaire sleutels.

**Uitvoercontractversie:** `2026-09-24-eerste-opzet` (`manifest.UITVOER_CONTRACT_VERSIE`, staat ook
in elke regel van `_manifest.jsonl`). Dit is de eerste opzet; deze versie hoort omhoog te gaan zodra
de vorm of betekenis van de uitvoer verandert.

## 8. Bekende beperkingen en open vragen

- **`smartmeters_electricity_15m.csv` ontbreekt.** `README_dataset.md` wijdt er een eigen paragraaf
  aan en `metadata.csv` definieert er elf velden voor, maar het bestand zit niet in het archief. Dit
  zou de elektrische kant van de woning op kwartierniveau geven; het is niet het minst belangrijke
  ontbrekende bestand.
- **`metadata.csv` noemt bestandsnamen die niet bestaan**: `hwp_15m.csv` en `smartmeters_15m.csv`,
  tegenover de werkelijke `heatpump_15m.csv` en het ontbrekende `smartmeters_electricity_15m.csv`.
- **`metadata.csv` noemt het veld `id` voor `household_monthly.csv`**, terwijl de kolom in de data
  zelf `custom_id` heet; deze pijplijn volgt de data.
- **De `hp_`/`hwp_`-tegenstrijdigheid.** De lopende tekst van `README_dataset.md` noemt de laatste
  twee velden van `household_monthly.csv` `hwp_electricity_kwh`/`hwp_gas_m3`, maar zowel de
  CSV-header als `metadata.csv` gebruiken `hp_electricity_kwh`/`hp_gas_m3` (zonder de "w"). Deze
  pijplijn volgt de data en `metadata.csv`, niet de lopende tekst van de README.
- **`metadata.csv` zegt "at least one steered HP", `README_dataset.md` zegt "at least two".** De
  data geeft de README gelijk: het minimum van `n_wp_gestuurd` in de verwerkte uitvoer is 2.
- **De inlet/outlet-interpretatie is een aanname**, getoetst met 99,16% bevestiging maar niet bewezen
  (§5.1.1).
- **De zomertijdgaten in `wijktrafo_15min`** (§4.1) zijn een bevinding, geen vaststaande verklaring:
  de meest waarschijnlijke verklaring (lokale tijd ergens in de Enexis-meetketen, vóór de
  UTC-omzetting) is aannemelijk gemaakt, niet bewezen; de warmtepompdata toont geen vergelijkbaar
  patroon.
- **Geen sentinelwaarden of plausibiliteitsgrenzen ingebouwd** (§6): mocht een latere gebruiker
  fysisch onmogelijke waarden tegenkomen (bijvoorbeeld een negatieve temperatuur of een absurd hoog
  vermogen), dan is dat met de huidige pijplijn niet gevlagd.
- **97 versus 92 versus 93 systemen.** Het eindrapport noemt 97 geplaatste toestellen (p. 8) en 92
  gebruikt voor een simulatieanalyse (p. 19); de verwerkte `household_monthly`-tabel bevat 93 unieke
  `custom_id`'s. Het verschil tussen deze drie getallen is in het eindrapport niet toegelicht en met
  de middelen van deze repo niet te herleiden.
- **Sensormerk, kalibratie en meetonzekerheid** van de individuele warmtepomp- en trafometingen zijn
  in de meegeleverde documentatie niet gespecificeerd (§3).

## 9. Datapackage (machineleesbare beschrijving)

`datapackage.json` (repo-root, en aan het eind van elke run herschreven) is een machineleesbare
beschrijving van deze zes tabellen volgens de
[Frictionless Data Package-standaard](https://specs.frictionlessdata.io/data-package/): per tabel een
Table Schema (kolomnamen, types, beschrijvingen, primaire sleutel), plus licentie- en
herkomstinformatie voor beide data-eigenaren. Het wordt UIT DE CODE gegenereerd
(`dacs_hw_preprocessing.datapackage`, uit dezelfde `pyarrow`-schema's die de pijplijn zelf gebruikt om
te schrijven, `tabellen.py`), niet met de hand bijgehouden, en is te regenereren met
`python -m dacs_hw_preprocessing.datapackage`. Een test (`tests/test_datapackage.py`) borgt dat elk
veld in een schema in het datapackage staat en omgekeerd. Anders dan bij de WarmingUP-preprocessing
hebben alle zes tabellen hier een geverifieerd unieke primaire sleutel (§6), dus geen enkele resource
laat `primaryKey` weg.

## 10. Bronnen

- Bisschop, E., De Boer, H., Van Hooijdonk, R., Hormann, R., Li, X., Matien, E., Paterakis, N., Van
  Urk, T., Visser, L., & Wolterink, G. (2026, 23 januari). *Digitale Aggregatie en Collectieve
  Sturing van Hybride Warmtepompen, Openbare versie* (Eindrapport, referentienummer MOOI322001).
  Geen expliciete copyrightvermelding aangetroffen in de tekst zelf; geciteerd met bronvermelding
  conform GEBRUIKSVOORWAARDEN.md, niet overgenomen als tabel of figuur.
- KITE (Kennis- en Dataplatform Individuele Technieken), RVO. Projectpagina *DACS-HW*, community
  Kennisdelen RVO. Zie GEBRUIKSVOORWAARDEN.md voor de letterlijke citaten over licentie en meldplicht.
- `README_dataset.md` en `metadata.csv` (bijgeleverd in `dataset-dacs-hw.zip`).
- `Toelichting DACS-HW Enexis Dataset.txt` (bijgeleverd in `wijktrafo_15min.zip`).
