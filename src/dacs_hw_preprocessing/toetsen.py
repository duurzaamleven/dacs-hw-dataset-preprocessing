# SPDX-License-Identifier: EUPL-1.2
"""De inlet/outlet-toets (ontwerp-preprocessing.md §5): een losse functie, geen onderdeel van de
kolomvertaling zelf.

Gebruik::

    python -m dacs_hw_preprocessing.toetsen
    # met eigen paden:
    python -m dacs_hw_preprocessing.toetsen --dataset-zip pad/naar/dataset-dacs-hw.zip
"""

from __future__ import annotations

import argparse
from pathlib import Path

from . import lezers


def toets_aanvoer_retour(dataset_zip: Path = lezers.DATASET_ZIP) -> dict:
    """Toetst de interpretatie uit ontwerp §5: ligt `temp_aanvoer` structureel boven `temp_retour`
    wanneer er warmte wordt geleverd?

    De toewijzing van `inlet`/`outlet` aan retour/aanvoer is een INTERPRETATIE, geen bronclaim:
    `outlet` is het water dat de warmtepomp verlaat (de aanvoer naar de woning), `inlet` is het
    water dat de warmtepomp binnenkomt (de retour van de woning). Bij een draaiende warmtepomp hoort
    aanvoer dus boven retour te liggen. Dit is met deze data te toetsen.

    "Warmte geleverd" = `q_warmtepomp_gem__kWh > 0`: er is in dat kwartier gemeten thermische energie
    door de elektrische warmtepomp geleverd.

    **Dit is een bevinding, geen oordeel**: de uitkomst wordt hier gerapporteerd zoals gemeten, niet
    gebruikt om de kolomnamen of de interpretatie met terugwerkende kracht aan te passen.
    """
    df = lezers.lees_heatpump_15m(dataset_zip)
    levert_warmte = df["q_warmtepomp_gem__kWh"] > 0
    subset = df.loc[levert_warmte, ["temp_aanvoer_gem__degC", "temp_retour_gem__degC"]].dropna()
    verschil = subset["temp_aanvoer_gem__degC"] - subset["temp_retour_gem__degC"]
    return {
        "n_kwartieren_met_warmtelevering": int(levert_warmte.sum()),
        "n_kwartieren_met_beide_temperaturen": int(len(subset)),
        "aandeel_aanvoer_boven_retour": float((verschil > 0).mean()) if len(verschil) else None,
        "verschil_mediaan__degC": float(verschil.median()) if len(verschil) else None,
        "verschil_q25__degC": float(verschil.quantile(0.25)) if len(verschil) else None,
        "verschil_q75__degC": float(verschil.quantile(0.75)) if len(verschil) else None,
    }


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset-zip", type=Path, default=lezers.DATASET_ZIP)
    return ap.parse_args()


def main() -> int:
    args = _parse_args()
    resultaat = toets_aanvoer_retour(args.dataset_zip)
    print("Aanvoer/retour-toets (ontwerp-preprocessing.md §5):")
    for sleutel, waarde in resultaat.items():
        print(f"  {sleutel}: {waarde}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
