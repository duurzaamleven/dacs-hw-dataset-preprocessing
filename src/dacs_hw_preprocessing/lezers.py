"""Inleesstap: zes CSV's uit twee ZIP-archieven naar getypeerde ``pandas.DataFrame``'s.

Implementeert de kolomvertaling (ontwerp-preprocessing.md §3) en de kwartierverschuiving van de
wijktrafodata (§4.1). Leest rechtstreeks uit de twee ZIP-archieven in ``data/raw/`` (buiten
versiebeheer, zie ``.gitignore``); geen uitpakken nodig, de set is klein genoeg (17 MB uitgepakt) om
in één keer in te lezen (ontwerp §1, §6).

**Aggregaat, geen tijdreeks per woning.** Iedere 15-minuten- of uurrij in ``heatpump_15m``,
``heatpump_steering_15m`` en ``smartmeters_gas_hourly`` is een statistiek over woningen/systemen,
geen woning (ontwerp §1). Dat verandert deze inleesstap niet; de kolomnamen dragen daarom een
statistieksuffix (`_gem`, `_med`, `_q25`, `_q75`, `_std`) vóór de dubbele underscore, zodat
`physiquant__unit` intact blijft (`kolommen.py`).

**Geen P = U·I-toets.** Ontwerp §4.2: stroom, spanning en belasting van de wijktrafodata zijn los van
elkaar naar een kwartiergemiddelde herbemonsterd, dus `stroom * spanning != belasting` hoort te
gelden en is geen kwaliteitsindicator. Bewust niet gebouwd.

**De inlet/outlet-toewijzing is een interpretatie.** Ontwerp §5 wijst `inlet_water_temperature` toe
aan `temp_retour` en `outlet_water_temperature` aan `temp_aanvoer` (het water dat de warmtepomp
verlaat, is de aanvoer naar de woning). Dat is hier een naamgevingskeuze, geen bronclaim; de toets of
die toewijzing klopt staat in :func:`dacs_hw_preprocessing.toetsen.toets_aanvoer_retour`.

Tz-aware tijdstempels worden hier al naar UTC geparsed (:func:`tijd.naar_utc_tijdstip`); de omzetting
naar de weergavezone Europe/Amsterdam gebeurt pas vlak voor het schrijven, in ``pijplijn.py`` (zie
``tijd.py`` voor de onderbouwing).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

from . import kolommen
from . import tijd


class DacsHwDataOntbreekt(FileNotFoundError):
    """Een van de twee bronarchieven ontbreekt op de verwachte plek.

    Geen stille lege DataFrame: een inleesstap die per ongeluk op een ontbrekende bron draait is
    erger dan een inleesstap die vroeg en luid faalt.
    """


#: Standaardpaden: de twee archieven staan in `data/raw/`, zie GEBRUIKSVOORWAARDEN.md voor herkomst
#: en sha256.
DATA_RAW_DIR: Path = Path(__file__).resolve().parents[2] / "data" / "raw"
DATASET_ZIP: Path = DATA_RAW_DIR / "dataset-dacs-hw.zip"
TRAFO_ZIP: Path = DATA_RAW_DIR / "wijktrafo_15min.zip"

_KWARTIER = pd.Timedelta(kolommen.KWARTIER)


def _lees_csv_uit_zip(zip_pad: Path, csv_naam: str, **kwargs) -> pd.DataFrame:
    """Leest één CSV rechtstreeks uit een ZIP-archief (zipfile + pandas), zonder uit te pakken."""
    zip_pad = Path(zip_pad)
    if not zip_pad.exists():
        raise DacsHwDataOntbreekt(
            f"{zip_pad} bestaat niet. De ruwe DACS-HW-data staat buiten versiebeheer (zie "
            ".gitignore); haal de twee archieven op zoals beschreven in GEBRUIKSVOORWAARDEN.md en "
            "zet ze in data/raw/."
        )
    with zipfile.ZipFile(zip_pad) as z:
        with z.open(csv_naam) as f:
            return pd.read_csv(f, **kwargs)


def lees_heatpump_15m(dataset_zip: Path = DATASET_ZIP) -> pd.DataFrame:
    """`heatpump_15m.csv`: 15-minutenaggregaat over warmtepompsystemen (ontwerp §1, §3).

    Begin-gelabeld: `tijdstip_start` beschrijft `[tijdstip_start, tijdstip_start + 15 min)`, en is
    dat al in de bron. Geen kwartierverschuiving nodig, in tegenstelling tot de wijktrafodata; zie
    :func:`lees_wijktrafo_15min` en ontwerp §4.1.
    """
    df = _lees_csv_uit_zip(dataset_zip, "heatpump_15m.csv")
    df = df.rename(columns=kolommen.HEATPUMP_15M_KOLOMMEN)
    df["tijdstip_start"] = tijd.naar_utc_tijdstip(df["tijdstip_start"])
    for kolom in kolommen.HEATPUMP_15M_TELKOLOMMEN:
        df[kolom] = df[kolom].astype("int32")
    waardekolommen = [c for c in df.columns if c not in ("tijdstip_start", *kolommen.HEATPUMP_15M_TELKOLOMMEN)]
    df[waardekolommen] = df[waardekolommen].astype("float32")
    return df


def lees_heatpump_steering_15m(dataset_zip: Path = DATASET_ZIP) -> pd.DataFrame:
    """`heatpump_steering_15m.csv`: kwartieren met minstens twee gestuurde warmtepompen (ontwerp §1).

    Alleen kwartieren mét aansturing staan erin; afwezige kwartieren betekenen "geen (of één)
    warmtepomp gestuurd", niet "waarde nul" (`README_dataset.md`).
    """
    df = _lees_csv_uit_zip(dataset_zip, "heatpump_steering_15m.csv")
    df = df.rename(columns=kolommen.HEATPUMP_STEERING_15M_KOLOMMEN)
    df["tijdstip_start"] = tijd.naar_utc_tijdstip(df["tijdstip_start"])
    df["n_wp_gestuurd"] = df["n_wp_gestuurd"].astype("int32")
    for kolom in kolommen.POWER_LIMIT_KW_KOLOMMEN:
        df[kolom] = (df[kolom] * 1000.0).astype("float32")  # kW -> W
    return df


def lees_smartmeters_gas_hourly(dataset_zip: Path = DATASET_ZIP) -> pd.DataFrame:
    """`smartmeters_gas_hourly.csv`: uuraggregaat gasgebruik over slimme meters (ontwerp §1, §3)."""
    df = _lees_csv_uit_zip(dataset_zip, "smartmeters_gas_hourly.csv")
    df = df.rename(columns=kolommen.SMARTMETERS_GAS_HOURLY_KOLOMMEN)
    df["tijdstip_start"] = tijd.naar_utc_tijdstip(df["tijdstip_start"])
    df["n_meter_gas"] = df["n_meter_gas"].astype("int32")
    waardekolommen = [c for c in df.columns if c not in ("tijdstip_start", "n_meter_gas")]
    df[waardekolommen] = df[waardekolommen].astype("float32")
    return df


def lees_household_monthly(dataset_zip: Path = DATASET_ZIP) -> pd.DataFrame:
    """`household_monthly.csv`: één rij per woning per kalendermaand (ontwerp §1, §3).

    Gebruikt `custom_id` als sleutel, niet `id`: `metadata.csv` noemt het veld `id`, maar de kolom
    in de data zelf heet `custom_id` (ontwerp §7). `custom_id__str` is stabiel binnen deze dataset,
    maar NIET te koppelen aan de kwartierbestanden (`README_dataset.md`, "Privacy").

    `maand_start` is GEEN tz-aware UTC-instant, in tegenstelling tot `tijdstip_start` in de andere
    vijf tabellen: zie `tijd.py` voor de onderbouwing.

    Lege velden betekenen "geen meting beschikbaar", geen nul (`README_dataset.md`); hier niet
    ingevuld, dus `NaN` blijft `NaN`.
    """
    df = _lees_csv_uit_zip(dataset_zip, "household_monthly.csv")
    df = df.rename(columns=kolommen.HOUSEHOLD_MONTHLY_KOLOMMEN)
    df["maand_start"] = tijd.naar_kalendermaand(df["maand_start"])
    waardekolommen = [c for c in df.columns if c not in ("maand_start", "custom_id__str")]
    df[waardekolommen] = df[waardekolommen].astype("float32")
    return df


def lees_wijktrafo_15min(trafo_zip: Path = TRAFO_ZIP) -> pd.DataFrame:
    """`wijktrafo_15min.csv`: Enexis-meetdata van één wijktransformator (ontwerp §1, §3).

    **Schuift één kwartier terug; dit is de enige plek in de hele inleesstap waar dat gebeurt**
    (ontwerp §4.1). De bron is EIND-gelabeld (`Toelichting DACS-HW Enexis Dataset.txt`: *"Het
    gemiddelde is het gemiddelde signaal in het kwartier (15 min) voorafgaand aan tijdstip waarop
    het gemiddeld is genoteerd"*), terwijl de rest van deze dataset BEGIN-labelt (`tijdstip_start`
    beschrijft `[tijdstip_start, tijdstip_start + 15 min)`). Wie de twee bronnen zonder correctie
    samenvoegt, schuift de trafodata een kwartier op ten opzichte van de warmtepompdata.

    Geen `P ~= U·I`-toets (ontwerp §4.2): stroom, spanning en belasting zijn onafhankelijk
    herbemonsterd, dus die controle hoort te falen en is geen kwaliteitsindicator.
    """
    df = _lees_csv_uit_zip(trafo_zip, "wijktrafo_15min.csv")
    df = df.rename(columns=kolommen.WIJKTRAFO_15MIN_KOLOMMEN)
    # Eind-gelabeld -> begin-gelabeld: één kwartier terug (ontwerp §4.1).
    df["tijdstip_start"] = tijd.naar_utc_tijdstip(df["tijdstip_start"]) - _KWARTIER
    waardekolommen = [c for c in df.columns if c != "tijdstip_start"]
    df[waardekolommen] = df[waardekolommen].astype("float32")
    for kolom in kolommen.BELASTING_KW_KOLOMMEN:
        df[kolom] = df[kolom] * 1000.0  # kW -> W
    return df


def lees_metadata(dataset_zip: Path = DATASET_ZIP) -> pd.DataFrame:
    """`metadata.csv`: kolomdefinities uit de bron zelf, ongewijzigd overgenomen.

    Geen kolomvertaling: dit is een opzoektabel over de brontabellen (`field`, `description`,
    `file`, ...), geen meetdata, dus `physiquant__unit` is hier niet van toepassing. Bevat zelf twee
    bekende fouten (ontwerp §7: niet-bestaande bestandsnamen, en het veld `id` waar de data
    `custom_id` heet); die worden hier niet gecorrigeerd, want het doel is het afgenomen artefact
    vast te leggen zoals het is. Gelezen als tekst (``dtype=str``, ``keep_default_na=False``): dit is
    een opzoektabel, geen meetdata, en een lege cel is hier letterlijk een lege tekst, geen `NaN`.
    """
    return _lees_csv_uit_zip(dataset_zip, "metadata.csv", dtype=str, keep_default_na=False)
