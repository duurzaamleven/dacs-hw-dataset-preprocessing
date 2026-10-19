# SPDX-License-Identifier: EUPL-1.2
"""Tests voor `kwaliteitsrapport.py`: de zomertijdcontrole en de sleutelcontrole."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from dacs_hw_preprocessing import kwaliteitsrapport, tabellen


def _schrijf_tijdreeks(pad: Path, tijden: pd.Series) -> None:
    df = pd.DataFrame({"tijdstip_start": tijden})
    for kolom in ("n_wp_online",):
        df[kolom] = 10
    tabel = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(tabel, pad)


def test_zomertijdcontrole_vindt_een_echt_gat(tmp_path: Path):
    # 15-minutenreeks rond de oktoberwissel 2024 (laatste zondag = 27-10-2024, 01:00 UTC), met het
    # tweede dubbelzinnige uur (01:00-01:59 UTC) volledig ontbrekend: exact het patroon dat bij
    # WarmingUP is gevonden en dat deze controle moet herkennen.
    voor = pd.date_range("2024-10-26 22:00", "2024-10-27 00:45", freq="15min", tz="UTC")
    na = pd.date_range("2024-10-27 02:00", "2024-10-27 04:00", freq="15min", tz="UTC")
    tijden = voor.append(na)
    uit_dir = tmp_path
    _schrijf_tijdreeks(uit_dir / "heatpump_15m.parquet", pd.Series(tijden))

    resultaten = kwaliteitsrapport._zomertijdcontrole(uit_dir)
    oktober = [r for r in resultaten if "oktober" in r["wisseling"]]
    assert len(oktober) == 1
    assert oktober[0]["gat_gevonden"] is True
    assert oktober[0]["grootste_stap_in_venster__min"] >= 60.0


def test_zomertijdcontrole_geen_gat_bij_continue_utc_reeks(tmp_path: Path):
    tijden = pd.date_range("2024-10-26 22:00", "2024-10-27 04:00", freq="15min", tz="UTC")
    uit_dir = tmp_path
    _schrijf_tijdreeks(uit_dir / "heatpump_15m.parquet", pd.Series(tijden))

    resultaten = kwaliteitsrapport._zomertijdcontrole(uit_dir)
    oktober = [r for r in resultaten if "oktober" in r["wisseling"]]
    assert len(oktober) == 1
    assert oktober[0]["gat_gevonden"] is False


def test_sleutel_dubbelingen_signaleert_een_echte_dubbeling(tmp_path: Path):
    tijden = pd.to_datetime(["2024-09-01 00:00+02:00"] * 2, utc=False)
    df = pd.DataFrame({"tijdstip_start": pd.DatetimeIndex(tijden).tz_convert("Europe/Amsterdam")})
    for kolom in tabellen.SCHEMAS["heatpump_15m"].names:
        if kolom not in df.columns:
            df[kolom] = 0.0
    tabel = pa.Table.from_pandas(df, preserve_index=False)
    kolommen = [tabel.column(f.name).cast(f.type) for f in tabellen.SCHEMAS["heatpump_15m"]]
    tabel = pa.Table.from_arrays(kolommen, schema=tabellen.SCHEMAS["heatpump_15m"])
    pq.write_table(tabel, tmp_path / "heatpump_15m.parquet")

    resultaten = kwaliteitsrapport._sleutel_dubbelingen(tmp_path)
    heatpump = [r for r in resultaten if r["tabel"] == "heatpump_15m"][0]
    assert heatpump["dubbele_sleutels"] == 1
