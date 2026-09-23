# Ontwerp: DACS-HW-preprocessing

Wat deze pijplijn doet: zes CSV's uit twee ZIP-archieven naar getypeerde, herleidbare
Parquet-tabellen, met de kolomvertaling, de tijdzonebehandeling en de aannames die daarbij horen.
**Dit is geen analyse.** Er wordt hier niets geconcludeerd over flexibiliteit, congestie of
warmtepompgedrag; de repo is bedoeld om bruikbaar te zijn voor iedereen die met deze dataset werkt.

## 1. De brondata

Twee archieven (herkomst en sha256: [`GEBRUIKSVOORWAARDEN.md`](GEBRUIKSVOORWAARDEN.md)), samen
ongeveer 4 MB gecomprimeerd en **17 MB uitgepakt**. Dat is klein genoeg dat deze pijplijn zonder
chunking, zonder een voortgangsbestand en zonder hervatbaarheid op rijniveau kan: elke tabel wordt in
één keer ingelezen en in één keer weggeschreven. Alleen op tabelniveau is er een hervatpunt (het
manifest, zie §6), niet middenin een bestand.

| bestand | rijen | kolommen | periode (UTC) | korrel |
|---|---:|---:|---|---|
| `heatpump_15m.csv` | 43.962 | 38 | 2024-08-31 22:00 .. 2025-12-04 10:45 | 15 min, **aggregaat over woningen** |
| `heatpump_steering_15m.csv` | 2.763 | 4 | 2024-11-28 16:30 .. 2025-06-02 21:15 | 15 min, **aggregaat**, alleen kwartieren mét aansturing |
| `smartmeters_gas_hourly.csv` | 11.018 | 6 | 2024-08-31 22:00 .. 2025-12-03 23:00 | 1 uur, **aggregaat** |
| `household_monthly.csv` | 1.334 | 8 | 2024-09 .. 2025-11 (15 maanden) | maand, **per woning** |
| `wijktrafo_15min.csv` | 69.320 | 10 | 2023-12-04 23:15 .. 2025-12-04 11:00 | 15 min, één wijktransformator |
| `metadata.csv` | 66 | 8 | | kolomdefinities uit de bron zelf |

Rijaantallen geverifieerd op de echte archieven (`sha256` in GEBRUIKSVOORWAARDEN.md), niet uit een
rapport overgenomen.

**Alles op kwartier- of uurniveau in de eerste vier bestanden is een aggregaat over woningen of
meters, geen tijdreeks per woning.** Elke rij is een gemiddelde, mediaan, kwartielen en een
coveragetelling over de systemen die in dat interval data leverden (`README_dataset.md`: *"One row
per 15-minute interval containing statistics across the heat-pump systems that contributed data
during that interval."*). `household_monthly.csv` is het enige bestand met een woningsleutel
(`custom_id`), en is **niet** aan de kwartierbestanden te koppelen (dezelfde bron: *"This `id` is
stable across months within this dataset. It can not directly be compared with the 15min data."*).
`wijktrafo_15min.csv` gaat over precies één wijktransformator, zonder woningtoewijzing.

## 2. Wat er uit komt

Zes Parquet-bestanden (zstd), één per brontabel, elk in één stuk weggeschreven:

- `heatpump_15m.parquet`
- `heatpump_steering_15m.parquet`
- `smartmeters_gas_hourly.parquet`
- `household_monthly.parquet`
- `wijktrafo_15min.parquet`
- `metadata.parquet`

Geen partitionering per woning (die is er niet: de kwartierbestanden zijn aggregaten, zie §1), geen
kleinere tabellen die uit een grotere zijn afgeleid. Elke tabel is de kolomvertaalde, getypeerde
vorm van precies één brontabel.

## 3. Kolomvertaling

Conform `physiquant__unit` (<https://github.com/energietransitie/physiquant__unit>): de eenheid staat
in de naam na de dubbele underscore, `_cum` alleen voor een meterstand. Omdat de bron aggregaten
levert, krijgt elke statistiekkolom een suffix vóór die dubbele underscore: `_mean` → `_gem`,
`_median` → `_med`, `_lower_quartile` → `_q25`, `_upper_quartile` → `_q75`, `_std` → `_std`.
Coveragekolommen (hoeveel systemen/meters bijdroegen) krijgen een `n_`-naam zonder eenheidssuffix:
het is een telling, geen fysische grootheid, en hoort bij iedere uitspraak over de bijbehorende
statistiek.

### `heatpump_15m`

| bron | naam | opmerking |
|---|---|---|
| `interval_start` | `tijdstip_start` | UTC in de bron, begin-gelabeld |
| `hp_online_count` | `n_wp_online` | |
| `boiler_thermal_hp_count` | `n_wp_ketel` | |
| `boiler_thermal_energy_kwh_mean`/`_median`/`_lower_quartile`/`_upper_quartile` | `q_ketel_gem`/`_med`/`_q25`/`_q75__kWh` | geleverde warmte door de ketel, **niet** het gasvolume |
| `heatpump_thermal_hp_count` | `n_wp_warmtepomp` | |
| `heatpump_thermal_energy_kwh_*` | `q_warmtepomp_*__kWh` | geleverde warmte, elektrisch deel |
| `electricity_hp_count` | `n_wp_elektriciteit` | |
| `electricity_consumption_kwh_*` | `e_warmtepomp_*__kWh` | elektrisch verbruik van de warmtepompsystemen |
| `room_temperature_hp_count` | `n_wp_temp_binnen` | |
| `room_temperature_c_*` | `temp_binnen_*__degC` | |
| `room_setpoint_hp_count` | `n_wp_setpoint` | |
| `room_setpoint_c_mean`/`_median`/`_lower_quartile`/`_upper_quartile`/`_std` | `temp_setpoint_gem`/`_med`/`_q25`/`_q75`/`_std__degC` | als enige kolom ook met `_std` |
| `inlet_water_temperature_hp_count` | `n_wp_temp_retour` | |
| `inlet_water_temperature_c_*` | `temp_retour_*__degC` | zie §4 voor de inlet/outlet-interpretatie |
| `outlet_water_temperature_hp_count` | `n_wp_temp_aanvoer` | |
| `outlet_water_temperature_c_*` | `temp_aanvoer_*__degC` | idem |

### `heatpump_steering_15m`

Alleen kwartieren met minstens twee gestuurde warmtepompen staan erin; een afwezig kwartier betekent
"geen (of één) warmtepomp gestuurd", niet "waarde nul" (`README_dataset.md`).

| bron | naam | opmerking |
|---|---|---|
| `interval_start` | `tijdstip_start` | |
| `steered_hwp_count` | `n_wp_gestuurd` | |
| `power_limit_kw_mean` | `p_limiet_gem__W` | × 1000 (kW → W) |
| `power_limit_kw_median` | `p_limiet_med__W` | × 1000, zelfde stijl als `_mean` |

### `smartmeters_gas_hourly`

| bron | naam | opmerking |
|---|---|---|
| `interval_start` | `tijdstip_start` | uurresolutie |
| `gas_meter_count` | `n_meter_gas` | |
| `gas_delivered_m3_mean`/`_median`/`_lower_quartile`/`_upper_quartile` | `g_gebruik_gem`/`_med`/`_q25`/`_q75__m3` | |

### `household_monthly`

Sleutel is `custom_id`, **niet** `id` (`metadata.csv` noemt het veld abusievelijk `id`; de kolom in
de data zelf heet `custom_id`, zie §7). `maand_start` blijft een **kalendermaand**, geen tz-aware
UTC-instant: de bron zegt expliciet dat het een Europe/Amsterdam-kalenderlabel is
(`README_dataset.md`, "Time interpretation": *"Monthly `month` values are Europe/Amsterdam calendar
labels ... not an instant or UTC timestamp"*). Deze pijplijn parseert die kolom daarom bewust naïef
(zonder tijdzone), in tegenstelling tot `tijdstip_start` in de andere vijf tabellen.

| bron | naam | opmerking |
|---|---|---|
| `month` | `maand_start` | kalendermaand, geen instant |
| `custom_id` | `custom_id__str` | stabiel binnen deze dataset, niet koppelbaar aan de kwartierbestanden |
| `total_electricity_delivered_kwh` | `e_geleverd_tot__kWh` | |
| `total_electricity_returned_kwh` | `e_teruglevering_tot__kWh` | |
| `total_net_electricity_consumption_kwh` | `e_net_tot__kWh` | |
| `total_gas_delivered_m3` | `g_geleverd_tot__m3` | |
| `hp_electricity_kwh` | `e_warmtepomp_tot__kWh` | zie de `hp_`/`hwp_`-tegenstrijdigheid in §7 |
| `hp_gas_m3` | `g_warmtepomp_tot__m3` | idem |

Lege velden betekenen "geen meting beschikbaar", geen nul (`README_dataset.md`); dat wordt hier niet
ingevuld, dus `NaN` blijft `NaN`.

### `wijktrafo_15min`

| bron | naam | opmerking |
|---|---|---|
| `timestamp` | `tijdstip_start` | zie §4.1 voor de kwartierverschuiving |
| `stroom_L1`/`L2`/`L3` | `i_trafo_L1`/`L2`/`L3__A` | geen eenheidsconversie nodig |
| `spanning_L1`/`L2`/`L3` | `u_trafo_L1`/`L2`/`L3__V` | idem |
| `belasting_L1`/`L2`/`L3` | `p_trafo_L1`/`L2`/`L3__W` | × 1000 (kW → W) |

### `metadata`

Geen kolomvertaling: dit is een opzoektabel over de brontabellen (`field`, `description`, `file`,
...) uit de bron zelf, geen meetdata. `physiquant__unit` is hier niet van toepassing; de tabel wordt
ongewijzigd overgenomen, inclusief de twee bekende fouten die erin zitten (§7).

## 4. Twee valkuilen in de vorm, allebei geverifieerd

### 4.1 De wijktrafodata is eind-gelabeld, de rest begin-gelabeld

Uit `Toelichting DACS-HW Enexis Dataset.txt`, de toelichting die met `wijktrafo_15min.zip`
meegeleverd wordt: *"Het gemiddelde is het gemiddelde signaal in het kwartier (15 min)
**voorafgaand** aan tijdstip waarop het gemiddeld is genoteerd."*

Uit `README_dataset.md`, over de vijf DACS-bestanden: *"`interval_start` is the beginning of the
represented period. Values describe `[interval_start, interval_start + 15 minutes)`."*

**De twee bronnen gebruiken tegengestelde conventies.** Wie ze zonder correctie samenvoegt, schuift
de trafodata een kwartier op ten opzichte van de warmtepompdata. De afspraak in deze pijplijn:
**alles wordt begin-gelabeld**, conform `tijdstip_start` in de andere vijf tabellen, en de
wijktrafodata schuift dus één kwartier terug bij het inlezen. **Dit gebeurt op precies één plek**
(de inleesfunctie voor `wijktrafo_15min`) en nergens anders.

### 4.2 Stroom maal spanning is niet de belasting

De toelichting zegt het zelf: *"Doordat het sample interval van stroom / spanning / belasting los
van elkaar loopt, geldt dat stroom maal spanning is niet de belasting."* Alle drie zijn afzonderlijk
naar een kwartiergemiddelde herbemonsterd. Een controle `P ?= U · I` hoort dus te falen en is geen
kwaliteitsindicator. **Bewust niet gebouwd** in deze pijplijn.

## 5. De inlet/outlet-interpretatie: een aanname, geverifieerd

`inlet_water_temperature` en `outlet_water_temperature` zijn hier vertaald naar `temp_retour` en
`temp_aanvoer`: het water dat de warmtepomp verlaat (`outlet`) is de aanvoer naar de woning; het
water dat binnenkomt (`inlet`) is de retour van de woning. **Dit is een naamgevingskeuze van deze
pijplijn, geen letterlijke bronclaim**; `README_dataset.md` en `metadata.csv` documenteren zelf niet
welke kant "inlet" en "outlet" is ten opzichte van de woning.

Deze interpretatie is toetsbaar: bij een draaiende warmtepomp hoort de aanvoer structureel boven de
retour te liggen. De toets (`toetsen.toets_aanvoer_retour`) selecteert kwartieren met gemeten
warmtelevering (`q_warmtepomp_gem__kWh > 0`) en vergelijkt `temp_aanvoer_gem__degC` met
`temp_retour_gem__degC`. Dit is een **losse functie**, geen onderdeel van de kolomvertaling zelf: de
uitkomst wordt gerapporteerd zoals gemeten, niet gebruikt om de kolomnamen met terugwerkende kracht
aan te passen (zie `docs/data-quality.md` voor de uitkomst op de volledige set).

## 6. Hervatbaarheid, manifest en contractversie

Ondanks de kleine omvang (§1) blijft het patroon van een manifest en atomisch schrijven gehandhaafd,
voor consistentie met de zusterrepo's en omdat het geen kosten heeft bij een kleine set:

- elke tabel wordt eerst naar `<pad>.tmp` geschreven en pas na een geslaagde schrijfactie atomisch
  hernoemd naar zijn definitieve naam;
- `_manifest.jsonl` in de uitvoermap: per tabel het pad, de sha256 en het aantal rijen; een
  hervatting slaat een tabel over zodra het manifest zegt dat hij af is én het bestand op schijf
  nog klopt (bestaat, juiste contractversie);
- `UITVOER_CONTRACT_VERSIE`: wijzigt de vorm of betekenis van de uitvoer, dan gaat dit omhoog.

Geen voortgangsbestand (`_voortgang.json`) en geen chunking: bij 17 MB uitgepakt is een volledige
run een kwestie van seconden, dus een ETA-mechanisme voegt niets toe.

## 7. Bekende gebreken in de bron

Drie gebreken, geen verwijten, wel dingen die een volgende gebruiker laten struikelen:

1. **`smartmeters_electricity_15m.csv` ontbreekt.** `README_dataset.md` wijdt er een eigen paragraaf
   aan en `metadata.csv` definieert er elf velden voor (`smart_meter_online_count`,
   `delivered_power_kw_*`, `returned_power_kw_*`), maar het bestand zit niet in het archief. Dit zou
   de elektrische kant van de woning op kwartierniveau geven; het is niet het minst belangrijke
   ontbrekende bestand.
2. **`metadata.csv` noemt bestandsnamen die niet bestaan**: `hwp_15m.csv` en `smartmeters_15m.csv`,
   tegenover de werkelijke `heatpump_15m.csv` en het (ontbrekende) `smartmeters_electricity_15m.csv`.
3. **Twee tegenstrijdigheden in de definities.**
   - `metadata.csv` definieert voor `household_monthly.csv` een veld `id`, terwijl de kolom in de
     data zelf `custom_id` heet (§3, tabel `household_monthly`).
   - Voor de aanstuurtabel zegt `metadata.csv` "at least one steered HP", terwijl `README_dataset.md`
     "at least two" zegt; de data geeft de README gelijk (het minimum van `steered_hwp_count` is 2,
     geverifieerd op de volledige set).
4. **De `hp_`/`hwp_`-tegenstrijdigheid.** De lopende tekst van `README_dataset.md` noemt de laatste
   twee velden van `household_monthly.csv` `hwp_electricity_kwh`/`hwp_gas_m3`, maar zowel de
   CSV-header als `metadata.csv` gebruiken `hp_electricity_kwh`/`hp_gas_m3` (zonder de "w"). Deze
   pijplijn volgt de data en `metadata.csv`, niet de lopende tekst van de README.

Geen van deze vier wordt hier gecorrigeerd; het doel is het afgenomen artefact vast te leggen zoals
het is, met de afwijking benoemd.

## 8. Wat deze pijplijn niet doet

- **Geen woningmodelkalibratie en geen gelijktijdigheidsanalyse.** Kan niet met de aggregaten in de
  kwartierbestanden (§1); dat is een analysevraag, geen preprocessingvraag.
- **Geen koppeling tussen de trafodata en de woningen.** De trafodata is één transformator zonder
  woningtoewijzing.
- **Geen `P ≈ U·I`-toets** (§4.2).
- **Geen weerkoppeling.**
- **Geen chunking, geen voortgangsbestand** (§6): de set is te klein om dat te rechtvaardigen.
