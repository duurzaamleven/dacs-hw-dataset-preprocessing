"""Tests voor `tijd.py`: UTC-parsing, de weergavezone-omzetting, en het kalenderlabel."""

from __future__ import annotations

import pandas as pd

from dacs_hw_preprocessing import tijd


def test_naar_utc_tijdstip_parseert_offset_en_z_vorm():
    kolom = pd.Series(["2024-08-31 22:00:00+00:00", "2023-12-04T23:15:00Z"])
    resultaat = tijd.naar_utc_tijdstip(kolom)
    assert str(resultaat.dt.tz) == "UTC"
    assert resultaat.iloc[0] == pd.Timestamp("2024-08-31 22:00:00", tz="UTC")
    assert resultaat.iloc[1] == pd.Timestamp("2023-12-04 23:15:00", tz="UTC")


def test_naar_weergave_tijdzone_verandert_instant_niet():
    utc = tijd.naar_utc_tijdstip(pd.Series(["2024-08-31 22:00:00+00:00"]))
    weergave = tijd.naar_weergave_tijdzone(utc)
    assert str(weergave.dt.tz) == "Europe/Amsterdam"
    # zelfde instant: terugconverteren naar UTC geeft exact dezelfde waarde
    assert weergave.dt.tz_convert("UTC").iloc[0] == utc.iloc[0]
    # in de zomer is Europe/Amsterdam UTC+2, dus de lokale klok wijst 00:00 op 2024-09-01
    assert weergave.iloc[0] == pd.Timestamp("2024-09-01 00:00:00", tz="Europe/Amsterdam")


def test_naar_weergave_tijdzone_wintertijd():
    # 4 december: wintertijd, Europe/Amsterdam is dan UTC+1
    utc = tijd.naar_utc_tijdstip(pd.Series(["2023-12-04 23:15:00+00:00"]))
    weergave = tijd.naar_weergave_tijdzone(utc)
    assert weergave.iloc[0] == pd.Timestamp("2023-12-05 00:15:00", tz="Europe/Amsterdam")
    assert weergave.dt.tz_convert("UTC").iloc[0] == utc.iloc[0]


def test_naar_kalendermaand_blijft_naief():
    kolom = pd.Series(["2024-09-01", "2024-10-01"])
    resultaat = tijd.naar_kalendermaand(kolom)
    assert resultaat.dt.tz is None
    assert resultaat.iloc[0] == pd.Timestamp("2024-09-01")


def test_naar_kalendermaand_faalt_hard_op_onparseerbare_waarde():
    import pytest

    kolom = pd.Series(["geen-datum"])
    with pytest.raises(ValueError):
        tijd.naar_kalendermaand(kolom)
