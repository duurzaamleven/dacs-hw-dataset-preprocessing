"""Orchestratie en CLI: bouwt alle uitvoer uit de twee ruwe zips (ontwerp-preprocessing.md).

Gebruik: ``python -m dacs_hw_preprocessing --raw-dir data/raw --uit data/processed``.

* ``--droogloop``: laat zien wat er zou gebeuren zonder iets te schrijven.

De set is klein (17 MB uitgepakt, ontwerp §1), dus in tegenstelling tot de WarmingUP-/
IM3-preprocessing is er geen ``--test``-modus, geen chunking en geen voortgangsbestand nodig: elke
tabel wordt in één keer gelezen en geschreven. Zonder ``--droogloop`` hervat de pijplijn een eerder
afgebroken run automatisch (``manifest.py``): een tabel die al een geldige manifestregel heeft, wordt
overgeslagen.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import time
from pathlib import Path

import pyarrow as pa

from . import datapackage as datapackage_mod
from . import kwaliteitsrapport
from . import lezers
from . import tabellen
from . import tijd
from . import toetsen
from .manifest import Manifest, UITVOER_CONTRACT_VERSIE, schrijf_arrow_atomisch

log = logging.getLogger(__name__)

#: (tabelnaam, leesfunctie, heeft_tz_aware_tijdstip) in de volgorde waarin ze verwerkt worden.
TABELLEN: list[tuple[str, object, bool]] = [
    ("heatpump_15m", lezers.lees_heatpump_15m, True),
    ("heatpump_steering_15m", lezers.lees_heatpump_steering_15m, True),
    ("smartmeters_gas_hourly", lezers.lees_smartmeters_gas_hourly, True),
    ("household_monthly", lezers.lees_household_monthly, False),
    ("wijktrafo_15min", lezers.lees_wijktrafo_15min, True),
    ("metadata", lezers.lees_metadata, False),
]


def _naar_arrow_tabel(df, schema: pa.Schema, naam: str, heeft_tz_aware_tijdstip: bool) -> pa.Table:
    """Zet de laatste stap: tz-aware tijdstempels naar de weergavezone (``tijd.py``), daarna casten
    naar het EXPLICIETE schema (``tabellen.py``). Dit is de enige plek waar
    ``tijd.naar_weergave_tijdzone`` wordt aangeroepen, zodat alle tussenliggende logica (in
    ``lezers.py``) op UTC blijft werken."""
    df = df.copy()
    if heeft_tz_aware_tijdstip:
        df["tijdstip_start"] = tijd.naar_weergave_tijdzone(df["tijdstip_start"])
    tabel = pa.Table.from_pandas(df, preserve_index=False)
    # Kolomvolgorde en -types expliciet naar het gedeclareerde schema; from_pandas leidt zelf een
    # schema af dat qua volgorde en precisie (bijvoorbeeld timestampresolutie) kan afwijken.
    kolommen = [tabel.column(schema.field(i).name).cast(schema.field(i).type) for i in range(len(schema))]
    return pa.Table.from_arrays(kolommen, schema=schema)


def run(
    raw_dir: str | Path = lezers.DATA_RAW_DIR,
    uit_dir: str | Path = "data/processed",
    docs_dir: str | Path | None = "docs",
    droogloop: bool = False,
    datapackage_pad: str | Path | None = datapackage_mod.STANDAARD_DATAPACKAGE_PAD,
) -> dict:
    """Bouw alle uitvoer. ``datapackage_pad`` is waar datapackage.json komt (standaard de
    repo-root); ``None`` slaat het over. Tests geven ``None`` of een pad in ``tmp_path`` mee, zodat
    een testrun nooit de echte datapackage.json van deze repo overschrijft."""
    raw_dir = Path(raw_dir)
    uit_dir = Path(uit_dir)
    dataset_zip = raw_dir / "dataset-dacs-hw.zip"
    trafo_zip = raw_dir / "wijktrafo_15min.zip"

    if droogloop:
        return _droogloop(dataset_zip, trafo_zip, uit_dir)

    uit_dir.mkdir(parents=True, exist_ok=True)
    manifest = Manifest(uit_dir)
    start = time.monotonic()
    resultaten: dict[str, object] = {}

    for naam, leesfn, heeft_tz in TABELLEN:
        pad = uit_dir / f"{naam}.parquet"
        if manifest.is_voltooid(naam, naam, uit_dir):
            resultaten[f"{naam}_rijen"] = manifest.totaal_rijen(naam)
            log.info("%s: al voltooid, overgeslagen (manifest)", naam)
            continue
        bron_zip = trafo_zip if naam == "wijktrafo_15min" else dataset_zip
        df = leesfn(bron_zip)
        tabel = _naar_arrow_tabel(df, tabellen.SCHEMAS[naam], naam, heeft_tz)
        schrijf_arrow_atomisch(pad, tabel)
        manifest.voeg_toe(naam, naam, pad, uit_dir, tabel.num_rows)
        resultaten[f"{naam}_rijen"] = tabel.num_rows
        log.info("%s: %d rijen geschreven", naam, tabel.num_rows)

    toets_resultaat = toetsen.toets_aanvoer_retour(dataset_zip)
    resultaten["toets_aanvoer_retour"] = toets_resultaat

    if docs_dir is not None:
        kwaliteitsrapport.schrijf_rapport(uit_dir, Path(docs_dir) / "data-quality.md", toets_resultaat)

    # datapackage.json komt standaard in de repo-root te staan, naast README/GEBRUIKSVOORWAARDEN.md,
    # net als in de WarmingUP-preprocessing; zie datapackage.py voor het standaardpad.
    if datapackage_pad is not None:
        datapackage_mod.schrijf_datapackage(Path(datapackage_pad), UITVOER_CONTRACT_VERSIE)
        resultaten["datapackage"] = str(datapackage_pad)

    resultaten["duur__s"] = time.monotonic() - start
    log.info("Klaar in %.2f s", resultaten["duur__s"])
    return resultaten


def _droogloop(dataset_zip: Path, trafo_zip: Path, uit_dir: Path) -> dict:
    print("\nDroogloop: er wordt niets geschreven.\n")
    for naam, pad in (("woningdata", dataset_zip), ("Enexis-trafodata", trafo_zip)):
        if pad.exists():
            print(f"  {naam}: {pad} ({pad.stat().st_size:,} bytes gecomprimeerd)".replace(",", "."))
        else:
            print(f"  {naam}: {pad} ONTBREEKT (zie GEBRUIKSVOORWAARDEN.md)")

    if uit_dir.exists():
        manifest = Manifest(uit_dir)
        for naam, _, _ in TABELLEN:
            n = len(manifest.voltooide_sleutels(naam))
            print(f"  {naam}: {'al voltooid' if n else 'nog te doen'} volgens het manifest")
    else:
        print(f"\nUitvoerpad {uit_dir} bestaat nog niet; een echte run zou vanaf nul beginnen.")

    bestaand_pad = uit_dir if uit_dir.exists() else uit_dir.parent
    if bestaand_pad.exists():
        vrij__GB = shutil.disk_usage(bestaand_pad).free / 1e9
        print(f"\nVrije schijfruimte op {bestaand_pad}: {vrij__GB:.1f} GB (deze set vraagt slechts enkele MB's).")
    return {"droogloop": True}


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw-dir", type=Path, default=lezers.DATA_RAW_DIR, help="Map met de twee ruwe zips")
    p.add_argument("--uit", "--out-dir", dest="uit", type=Path, default=Path("data/processed"))
    p.add_argument("--docs-dir", type=Path, default=Path("docs"))
    p.add_argument("--droogloop", action="store_true", help="Toon wat er zou gebeuren; schrijf niets")
    p.add_argument(
        "--datapackage-pad", type=Path, default=datapackage_mod.STANDAARD_DATAPACKAGE_PAD,
        help="Waar datapackage.json geschreven wordt (standaard: de repo-root).",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    resultaten = run(
        args.raw_dir, args.uit, docs_dir=args.docs_dir, droogloop=args.droogloop,
        datapackage_pad=args.datapackage_pad,
    )
    if not resultaten.get("droogloop"):
        for k, v in resultaten.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
