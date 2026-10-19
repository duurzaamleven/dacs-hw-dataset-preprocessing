# SPDX-License-Identifier: EUPL-1.2
"""Schrijft ``docs/data-quality.md``: het kwaliteitsrapport dat de pijplijn zelf genereert.

Deze dataset heeft geen sentinelwaarden en geen plausibiliteitsvlaggen zoals de WarmingUP- of
IM3-preprocessing (de bron documenteert ontbrekende metingen al als lege CSV-velden, die als `NaN`
overkomen); dit rapport vat in plaats daarvan de dekking samen (hoeveel systemen/meters droegen per
tabel bij), telt de resterende dubbele sleutels (zou nul moeten zijn, zie ``tests/``) en voert de
zomertijdcontrole uit rond elke DST-wisseling in de gedekte periode (ontwerp-preprocessing.md §4.1,
"algemene werkwijze" in het bouwrecept van deze repo).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .manifest import UITVOER_CONTRACT_VERSIE

#: Drempel voor "een gat": minstens twee gemiste kwartieren (30 minuten) op een rij, om ruis van een
#: enkel toevallig ontbrekend kwartier niet als DST-vinding te tellen.
DST_GAT_DREMPEL__min = 30.0

#: (tabelnaam, resolutie in minuten, is_sparse) voor de vier tz-aware tijdreeksen. `is_sparse=True`
#: voor `heatpump_steering_15m`: die tabel bevat per ontwerp alleen kwartieren MET aansturing, dus
#: een "gat" daarin is normaal en geen DST-signaal.
TIJDREEKS_TABELLEN = [
    ("heatpump_15m", 15, False),
    ("heatpump_steering_15m", 15, True),
    ("smartmeters_gas_hourly", 60, False),
    ("wijktrafo_15min", 15, False),
]


def _laatste_zondag(jaar: int, maand: int) -> pd.Timestamp:
    """Laatste zondag van `maand` in `jaar` (de EU-DST-regel: wissel op de laatste zondag van maart
    en oktober, 01:00 UTC)."""
    dag = pd.Timestamp(year=jaar, month=maand, day=1) + pd.offsets.MonthEnd(0)
    while dag.weekday() != 6:  # 6 = zondag
        dag -= pd.Timedelta(days=1)
    return dag


def _dst_wissels(jaren: list[int]) -> list[tuple[pd.Timestamp, str]]:
    wissels = []
    for jaar in jaren:
        wissels.append((_laatste_zondag(jaar, 3).replace(hour=1, tzinfo=None), "maart (naar zomertijd)"))
        wissels.append((_laatste_zondag(jaar, 10).replace(hour=1, tzinfo=None), "oktober (naar wintertijd)"))
    return sorted(wissels)


def _zomertijdcontrole(uit_dir: Path) -> list[dict]:
    """Voor elke tijdreeks-tabel en elke DST-wisseling binnen de gedekte periode: gaten en dubbele
    tijdstempels in een venster van twee uur rond de wisseling (01:00 UTC, het instant waarop de
    EU-klok verspringt)."""
    resultaten = []
    for naam, resolutie_min, is_sparse in TIJDREEKS_TABELLEN:
        pad = uit_dir / f"{naam}.parquet"
        if not pad.is_file():
            continue
        s = pd.read_parquet(pad, columns=["tijdstip_start"])["tijdstip_start"]
        if s.empty:
            continue
        s_utc = s.dt.tz_convert("UTC").sort_values().reset_index(drop=True)
        jaren = list(range(s_utc.min().year, s_utc.max().year + 1))
        for wissel_naief, omschrijving in _dst_wissels(jaren):
            wissel = pd.Timestamp(wissel_naief, tz="UTC")
            begin = wissel - pd.Timedelta(hours=2)
            eind = wissel + pd.Timedelta(hours=2)
            venster = s_utc[(s_utc >= begin) & (s_utc < eind)]
            if venster.empty:
                continue
            diffs = venster.diff().dropna()
            grootste_gat__min = diffs.max().total_seconds() / 60.0 if len(diffs) else 0.0
            gat_gevonden = (not is_sparse) and grootste_gat__min >= max(DST_GAT_DREMPEL__min, 2 * resolutie_min)
            dubbel = int(s_utc.duplicated().loc[venster.index].sum()) if len(venster) else 0
            resultaten.append(
                {
                    "tabel": naam,
                    "wisseling": f"{wissel.date()} ({omschrijving})",
                    "grootste_stap_in_venster__min": grootste_gat__min,
                    "gat_gevonden": gat_gevonden,
                    "dubbele_tijdstippen_in_venster": dubbel,
                    "is_sparse": is_sparse,
                }
            )
    return resultaten


def _dekking(uit_dir: Path) -> list[dict]:
    """Coveragekolommen (`n_*`): min, mediaan, max, zodat een lezer meteen ziet hoeveel systemen of
    meters gemiddeld bijdroegen (ontwerp §1)."""
    resultaten = []
    for naam, kolommen in (
        ("heatpump_15m", ["n_wp_online"]),
        ("heatpump_steering_15m", ["n_wp_gestuurd"]),
        ("smartmeters_gas_hourly", ["n_meter_gas"]),
    ):
        pad = uit_dir / f"{naam}.parquet"
        if not pad.is_file():
            continue
        df = pd.read_parquet(pad, columns=kolommen)
        for kolom in kolommen:
            resultaten.append(
                {
                    "tabel": naam,
                    "kolom": kolom,
                    "min": int(df[kolom].min()),
                    "mediaan": float(df[kolom].median()),
                    "max": int(df[kolom].max()),
                }
            )
    return resultaten


def _sleutel_dubbelingen(uit_dir: Path) -> list[dict]:
    """Controleert de primaire sleutel van elke tabel (zie datapackage.py) op dubbelingen in de
    ECHTE uitvoer; hoort altijd nul te zijn, en anders is dat een bevinding, geen stille aanname."""
    from . import datapackage as datapackage_mod

    resultaten = []
    for naam, sleutel in datapackage_mod._PRIMARY_KEYS.items():
        pad = uit_dir / f"{naam}.parquet"
        if not pad.is_file():
            continue
        df = pd.read_parquet(pad, columns=sleutel)
        n_dubbel = int(df.duplicated().sum())
        resultaten.append({"tabel": naam, "sleutel": sleutel, "dubbele_sleutels": n_dubbel, "rijen": len(df)})
    return resultaten


def schrijf_rapport(uit_dir: Path, docs_pad: Path, toets_aanvoer_retour_resultaat: dict | None = None) -> None:
    uit_dir = Path(uit_dir)
    docs_pad = Path(docs_pad)
    regels: list[str] = []
    regels.append("# Datakwaliteit")
    regels.append("")
    regels.append(
        "Dit bestand wordt door de pijplijn zelf geschreven (`dacs_hw_preprocessing.kwaliteitsrapport`), "
        "niet met de hand bijgehouden."
    )
    regels.append("")
    regels.append(f"Uitvoercontractversie: `{UITVOER_CONTRACT_VERSIE}`.")
    regels.append("")

    regels.append("## Rijaantallen en sleutelcontrole")
    regels.append("")
    regels.append("Elke tabel heeft een primaire sleutel (zie `datapackage.json`); dit rapport controleert "
                   "die op de ECHTE uitvoer, in plaats van uniciteit aan te nemen.")
    regels.append("")
    regels.append("| tabel | sleutel | rijen | dubbele sleutels |")
    regels.append("|---|---|---:|---:|")
    for r in _sleutel_dubbelingen(uit_dir):
        rijen__str = f"{r['rijen']:,}".replace(",", ".")
        sleutel__str = " + ".join(r["sleutel"])
        regels.append(f"| `{r['tabel']}` | `{sleutel__str}` | {rijen__str} | {r['dubbele_sleutels']} |")
    regels.append("")

    regels.append("## Dekking (coveragekolommen)")
    regels.append("")
    regels.append("Hoeveel systemen of meters bijdroegen per interval; hoort bij elke uitspraak over de "
                   "bijbehorende statistiek (ontwerp-preprocessing.md §1).")
    regels.append("")
    regels.append("| tabel | kolom | min | mediaan | max |")
    regels.append("|---|---|---:|---:|---:|")
    for r in _dekking(uit_dir):
        regels.append(f"| `{r['tabel']}` | `{r['kolom']}` | {r['min']} | {r['mediaan']:.1f} | {r['max']} |")
    regels.append("")

    regels.append("## Zomertijdcontrole")
    regels.append("")
    regels.append(
        "Rond elke DST-wisseling (laatste zondag van maart/oktober, 01:00 UTC) binnen de gedekte "
        "periode van elke tijdreeks-tabel: de grootste stap tussen opeenvolgende tijdstempels in een "
        "venster van twee uur vóór en na de wisseling, en het aantal dubbele tijdstempels in dat "
        "venster. `heatpump_steering_15m` is sparse per ontwerp (alleen kwartieren met aansturing), "
        "dus een gat daarin is GEEN DST-signaal en wordt niet als zodanig gemarkeerd."
    )
    regels.append("")
    regels.append("| tabel | wisseling | grootste stap in venster (min) | gat gevonden | dubbel in venster |")
    regels.append("|---|---|---:|---|---:|")
    for r in _zomertijdcontrole(uit_dir):
        gat = "**ja**" if r["gat_gevonden"] else ("n.v.t. (sparse)" if r["is_sparse"] else "nee")
        regels.append(
            f"| `{r['tabel']}` | {r['wisseling']} | {r['grootste_stap_in_venster__min']:.0f} | {gat} | "
            f"{r['dubbele_tijdstippen_in_venster']} |"
        )
    regels.append("")
    regels.append(
        "**Geen correctie in de data**: een gevonden gat betekent dat de bron voor dat interval geen "
        "rij bevat (de bron zegt zelf: als alle metingen op een tijdstip ontbreken, ontbreekt de rij, "
        "zie `Toelichting DACS-HW Enexis Dataset.txt`); dit rapport telt alleen."
    )
    regels.append("")

    if toets_aanvoer_retour_resultaat is not None:
        regels.append("## Aanvoer/retour-toets (ontwerp-preprocessing.md §5)")
        regels.append("")
        regels.append(
            "Toetst de interpretatie dat `outlet_water_temperature` de aanvoer naar de woning is en "
            "`inlet_water_temperature` de retour: bij warmtelevering (`q_warmtepomp_gem__kWh > 0`) "
            "hoort de aanvoer boven de retour te liggen."
        )
        regels.append("")
        for k, v in toets_aanvoer_retour_resultaat.items():
            regels.append(f"- `{k}`: {v}")
        regels.append("")

    docs_pad.parent.mkdir(parents=True, exist_ok=True)
    tmp = docs_pad.with_suffix(docs_pad.suffix + ".tmp")
    tmp.write_text("\n".join(regels) + "\n", encoding="utf-8")
    tmp.replace(docs_pad)
