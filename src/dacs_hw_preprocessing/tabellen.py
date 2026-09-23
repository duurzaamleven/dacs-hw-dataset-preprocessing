"""Parquet-schema's per uitvoertabel: bron van waarheid voor zowel het schrijven (``pijplijn.py``)
als de machineleesbare beschrijving (``datapackage.py``). Zie ontwerp-preprocessing.md §2, §3.
"""

from __future__ import annotations

import pyarrow as pa

from . import kolommen
from . import tijd

_TS = pa.timestamp("ns", tz=tijd.TIJDZONE_WEERGAVE)


def _floats(namen: tuple[str, ...] | list[str]) -> list[tuple[str, pa.DataType]]:
    return [(n, pa.float32()) for n in namen]


HEATPUMP_15M_WAARDEKOLOMMEN = [
    v
    for v in kolommen.HEATPUMP_15M_KOLOMMEN.values()
    if v not in ("tijdstip_start", *kolommen.HEATPUMP_15M_TELKOLOMMEN)
]

HEATPUMP_15M_SCHEMA = pa.schema(
    [("tijdstip_start", _TS)]
    + [(n, pa.int32()) for n in kolommen.HEATPUMP_15M_TELKOLOMMEN]
    + _floats(HEATPUMP_15M_WAARDEKOLOMMEN)
)

HEATPUMP_STEERING_15M_SCHEMA = pa.schema(
    [
        ("tijdstip_start", _TS),
        ("n_wp_gestuurd", pa.int32()),
        ("p_limiet_gem__W", pa.float32()),
        ("p_limiet_med__W", pa.float32()),
    ]
)

SMARTMETERS_GAS_HOURLY_SCHEMA = pa.schema(
    [
        ("tijdstip_start", _TS),
        ("n_meter_gas", pa.int32()),
    ]
    + _floats(["g_gebruik_gem__m3", "g_gebruik_med__m3", "g_gebruik_q25__m3", "g_gebruik_q75__m3"])
)

#: `maand_start` is bewust GEEN tz-aware timestamp (zie tijd.py): naïeve timestamp, kalenderlabel.
HOUSEHOLD_MONTHLY_SCHEMA = pa.schema(
    [
        ("maand_start", pa.timestamp("ns")),
        ("custom_id__str", pa.string()),
    ]
    + _floats(
        [
            "e_geleverd_tot__kWh",
            "e_teruglevering_tot__kWh",
            "e_net_tot__kWh",
            "g_geleverd_tot__m3",
            "e_warmtepomp_tot__kWh",
            "g_warmtepomp_tot__m3",
        ]
    )
)

WIJKTRAFO_15MIN_SCHEMA = pa.schema(
    [("tijdstip_start", _TS)]
    + _floats(
        [
            "i_trafo_L1__A",
            "i_trafo_L2__A",
            "i_trafo_L3__A",
            "u_trafo_L1__V",
            "u_trafo_L2__V",
            "u_trafo_L3__V",
            "p_trafo_L1__W",
            "p_trafo_L2__W",
            "p_trafo_L3__W",
        ]
    )
)

#: Opzoektabel, letterlijk overgenomen (lezers.lees_metadata): alle velden tekst.
METADATA_SCHEMA = pa.schema(
    [
        ("field", pa.string()),
        ("description", pa.string()),
        ("file", pa.string()),
        ("unit_name", pa.string()),
        ("unit_symbol", pa.string()),
        ("resolution", pa.string()),
        ("decimals", pa.string()),
        ("notes", pa.string()),
    ]
)

SCHEMAS: dict[str, pa.Schema] = {
    "heatpump_15m": HEATPUMP_15M_SCHEMA,
    "heatpump_steering_15m": HEATPUMP_STEERING_15M_SCHEMA,
    "smartmeters_gas_hourly": SMARTMETERS_GAS_HOURLY_SCHEMA,
    "household_monthly": HOUSEHOLD_MONTHLY_SCHEMA,
    "wijktrafo_15min": WIJKTRAFO_15MIN_SCHEMA,
    "metadata": METADATA_SCHEMA,
}
