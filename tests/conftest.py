"""Gedeelde testfixtures: kleine, zelfgebouwde ZIP's met exact de kolomnamen van de echte bron
(geverifieerd tegen `dataset-dacs-hw.zip`/`wijktrafo_15min.zip` op 17-09-2026), gevuld met
synthetische data. Geen netwerk, geen afhankelijkheid van de echte DACS-HW-data."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from dacs_hw_preprocessing import kolommen
from dacs_hw_preprocessing.datapackage import STANDAARD_DATAPACKAGE_PAD


def _vingerafdruk(pad: Path) -> tuple[str, int] | None:
    """sha256 en mtime van ``pad``, of None als het bestand niet bestaat. De mtime telt mee omdat
    de pijplijn byte-identieke inhoud kan herschrijven; ook dat mag een test niet doen."""
    if not pad.exists():
        return None
    return hashlib.sha256(pad.read_bytes()).hexdigest(), pad.stat().st_mtime_ns


@pytest.fixture(scope="session", autouse=True)
def echte_datapackage_blijft_onaangeroerd():
    """Faalt als een testrun de echte datapackage.json in de repo-root aanraakt: de pijplijn
    schrijft daar standaard naartoe, dus elke test moet ``datapackage_pad`` expliciet zetten."""
    voor = _vingerafdruk(STANDAARD_DATAPACKAGE_PAD)
    yield
    na = _vingerafdruk(STANDAARD_DATAPACKAGE_PAD)
    assert voor == na, (
        f"Een test heeft {STANDAARD_DATAPACKAGE_PAD} gewijzigd; geef pijplijn.run een "
        "datapackage_pad in tmp_path of None mee."
    )


def _kolom_fixture(kolommen_dict: dict[str, str], n: int, overrides: dict[str, list]) -> pd.DataFrame:
    """Bouwt een DataFrame met exact de bronkolommen van `kolommen_dict` (de keys), gevuld met
    `overrides` waar gegeven en anders met 0.0, zodat elke `lees_*`-functie een compleet fixture
    krijgt (ontbrekende kolommen zouden een KeyError geven bij het typeren)."""
    data = {}
    for bronkolom in kolommen_dict:
        if bronkolom in overrides:
            data[bronkolom] = overrides[bronkolom]
        else:
            data[bronkolom] = [0.0] * n
    return pd.DataFrame(data)


def _schrijf_zip(pad: Path, bestanden: dict[str, pd.DataFrame | str]) -> None:
    with zipfile.ZipFile(pad, "w") as z:
        for naam, inhoud in bestanden.items():
            if isinstance(inhoud, pd.DataFrame):
                z.writestr(naam, inhoud.to_csv(index=False))
            else:
                z.writestr(naam, inhoud)


def bouw_dataset_zip(pad: Path) -> Path:
    n = 3
    tijden = [
        "2024-08-31 22:00:00+00:00",
        "2024-08-31 22:15:00+00:00",
        "2024-08-31 22:30:00+00:00",
    ]
    heatpump_15m = _kolom_fixture(
        kolommen.HEATPUMP_15M_KOLOMMEN, n,
        {
            "interval_start": tijden,
            "hp_online_count": [10, 12, 11],
            "heatpump_thermal_energy_kwh_mean": [0.5, 0.0, 0.8],
            "electricity_consumption_kwh_mean": [0.2, 0.0, 0.3],
            # outlet (aanvoer) ruim boven inlet (retour) in de twee kwartieren met warmtelevering
            "inlet_water_temperature_c_mean": [30.0, 25.0, 31.0],
            "outlet_water_temperature_c_mean": [40.0, 26.0, 42.0],
            "room_setpoint_c_std": [0.1, 0.2, 0.15],
        },
    )
    steering = _kolom_fixture(
        kolommen.HEATPUMP_STEERING_15M_KOLOMMEN, n,
        {
            "interval_start": tijden,
            "steered_hwp_count": [2, 3, 5],
            "power_limit_kw_mean": [1.0, 0.933, 0.8],
            "power_limit_kw_median": [1.0, 0.9, 0.75],
        },
    )
    gas = _kolom_fixture(
        kolommen.SMARTMETERS_GAS_HOURLY_KOLOMMEN, n,
        {
            "interval_start": tijden,
            "gas_meter_count": [20, 21, 19],
            "gas_delivered_m3_mean": [0.0075, 0.0070, 0.0050],
        },
    )
    household = _kolom_fixture(
        kolommen.HOUSEHOLD_MONTHLY_KOLOMMEN, n,
        {
            "month": ["2024-09-01", "2024-10-01", "2024-11-01"],
            "custom_id": ["aaa111", "bbb222", "aaa111"],
            "hp_electricity_kwh": [20.4, 7.1, 33.0],
            "hp_gas_m3": [0.0, 0.0, 0.19],
        },
    )
    metadata = pd.DataFrame(
        {
            "field": ["interval_start", "custom_id"],
            "description": ["Timestamp labelling the 15-minute row in UTC", "Household key"],
            "file": ["heatpump_15m.csv", "household_monthly.csv"],
            "unit_name": ["datetime", ""],
            "unit_symbol": ["", ""],
            "resolution": ["15 min", ""],
            "decimals": ["", ""],
            "notes": ["", ""],
        }
    )
    readme = "# DACS-HW open dataset (testfixture, geen echte bron)\n"
    _schrijf_zip(pad, {
        "heatpump_15m.csv": heatpump_15m,
        "heatpump_steering_15m.csv": steering,
        "smartmeters_gas_hourly.csv": gas,
        "household_monthly.csv": household,
        "metadata.csv": metadata,
        "README_dataset.md": readme,
    })
    return pad


def bouw_trafo_zip(pad: Path) -> Path:
    wijktrafo = _kolom_fixture(
        kolommen.WIJKTRAFO_15MIN_KOLOMMEN, 2,
        {
            "timestamp": ["2023-12-04T23:15:00Z", "2023-12-04T23:30:00Z"],
            "belasting_L1": [1.234, 2.5],  # kW
            "belasting_L2": [0.5, 0.6],
            "belasting_L3": [0.3, 0.4],
            "stroom_L1": [168.34, 194.28],
            "spanning_L1": [230.1, 229.8],
        },
    )
    toelichting = (
        "Toelichting op de Enexis Dataset horende bij de DACS-HW openbare data (testfixture).\n"
        "Het gemiddelde is het gemiddelde signaal in het kwartier (15 min) voorafgaand aan "
        "tijdstip waarop het gemiddeld is genoteerd.\n"
    )
    _schrijf_zip(pad, {
        "Toelichting DACS-HW Enexis Dataset.txt": toelichting,
        "wijktrafo_15min.csv": wijktrafo,
    })
    return pad


@pytest.fixture()
def dataset_zip(tmp_path: Path) -> Path:
    return bouw_dataset_zip(tmp_path / "dataset-dacs-hw.zip")


@pytest.fixture()
def trafo_zip(tmp_path: Path) -> Path:
    return bouw_trafo_zip(tmp_path / "wijktrafo_15min.zip")
