# Datakwaliteit

Dit bestand wordt door de pijplijn zelf geschreven (`dacs_hw_preprocessing.kwaliteitsrapport`), niet met de hand bijgehouden.

Uitvoercontractversie: `2026-09-24-eerste-opzet`.

## Rijaantallen en sleutelcontrole

Elke tabel heeft een primaire sleutel (zie `datapackage.json`); dit rapport controleert die op de ECHTE uitvoer, in plaats van uniciteit aan te nemen.

| tabel | sleutel | rijen | dubbele sleutels |
|---|---|---:|---:|
| `heatpump_15m` | `tijdstip_start` | 43.962 | 0 |
| `heatpump_steering_15m` | `tijdstip_start` | 2.763 | 0 |
| `smartmeters_gas_hourly` | `tijdstip_start` | 11.018 | 0 |
| `household_monthly` | `maand_start + custom_id__str` | 1.334 | 0 |
| `wijktrafo_15min` | `tijdstip_start` | 69.320 | 0 |
| `metadata` | `field + file` | 66 | 0 |

## Dekking (coveragekolommen)

Hoeveel systemen of meters bijdroegen per interval; hoort bij elke uitspraak over de bijbehorende statistiek (ontwerp-preprocessing.md §1).

| tabel | kolom | min | mediaan | max |
|---|---|---:|---:|---:|
| `heatpump_15m` | `n_wp_online` | 26 | 75.0 | 88 |
| `heatpump_steering_15m` | `n_wp_gestuurd` | 2 | 60.0 | 87 |
| `smartmeters_gas_hourly` | `n_meter_gas` | 20 | 80.0 | 82 |

## Zomertijdcontrole

Rond elke DST-wisseling (laatste zondag van maart/oktober, 01:00 UTC) binnen de gedekte periode van elke tijdreeks-tabel: de grootste stap tussen opeenvolgende tijdstempels in een venster van twee uur vóór en na de wisseling, en het aantal dubbele tijdstempels in dat venster. `heatpump_steering_15m` is sparse per ontwerp (alleen kwartieren met aansturing), dus een gat daarin is GEEN DST-signaal en wordt niet als zodanig gemarkeerd.

| tabel | wisseling | grootste stap in venster (min) | gat gevonden | dubbel in venster |
|---|---|---:|---|---:|
| `heatpump_15m` | 2024-10-27 (oktober (naar wintertijd)) | 15 | nee | 0 |
| `heatpump_15m` | 2025-03-30 (maart (naar zomertijd)) | 15 | nee | 0 |
| `heatpump_15m` | 2025-10-26 (oktober (naar wintertijd)) | 15 | nee | 0 |
| `heatpump_steering_15m` | 2025-03-30 (maart (naar zomertijd)) | 120 | n.v.t. (sparse) | 0 |
| `smartmeters_gas_hourly` | 2024-10-27 (oktober (naar wintertijd)) | 60 | nee | 0 |
| `smartmeters_gas_hourly` | 2025-03-30 (maart (naar zomertijd)) | 60 | nee | 0 |
| `smartmeters_gas_hourly` | 2025-10-26 (oktober (naar wintertijd)) | 60 | nee | 0 |
| `wijktrafo_15min` | 2024-03-31 (maart (naar zomertijd)) | 15 | nee | 0 |
| `wijktrafo_15min` | 2024-10-27 (oktober (naar wintertijd)) | 75 | **ja** | 0 |
| `wijktrafo_15min` | 2025-03-30 (maart (naar zomertijd)) | 15 | nee | 0 |
| `wijktrafo_15min` | 2025-10-26 (oktober (naar wintertijd)) | 60 | **ja** | 0 |

**Geen correctie in de data**: een gevonden gat betekent dat de bron voor dat interval geen rij bevat (de bron zegt zelf: als alle metingen op een tijdstip ontbreken, ontbreekt de rij, zie `Toelichting DACS-HW Enexis Dataset.txt`); dit rapport telt alleen.

## Aanvoer/retour-toets (ontwerp-preprocessing.md §5)

Toetst de interpretatie dat `outlet_water_temperature` de aanvoer naar de woning is en `inlet_water_temperature` de retour: bij warmtelevering (`q_warmtepomp_gem__kWh > 0`) hoort de aanvoer boven de retour te liggen.

- `n_kwartieren_met_warmtelevering`: 39103
- `n_kwartieren_met_beide_temperaturen`: 39103
- `aandeel_aanvoer_boven_retour`: 0.9915863233000025
- `verschil_mediaan__degC`: 1.2900009155273438
- `verschil_q25__degC`: 0.3899993896484375
- `verschil_q75__degC`: 2.239999771118164

