"""Tests voor `lezers.py`: kolomvertaling, typen, en de kwartierverschuiving (ontwerp §3, §4.1)."""

from __future__ import annotations

import pandas as pd
import pytest

from dacs_hw_preprocessing import lezers


# ── Kolomvertaling ────────────────────────────────────────────────────────

def test_heatpump_15m_kolomvertaling_en_types(dataset_zip):
    df = lezers.lees_heatpump_15m(dataset_zip)
    assert "tijdstip_start" in df.columns
    assert "interval_start" not in df.columns
    assert str(df["tijdstip_start"].dt.tz) == "UTC"
    assert "e_warmtepomp_gem__kWh" in df.columns
    assert "q_warmtepomp_gem__kWh" in df.columns
    assert "temp_retour_gem__degC" in df.columns
    assert "temp_aanvoer_gem__degC" in df.columns
    assert "n_wp_online" in df.columns
    assert df["n_wp_online"].dtype == "int32"
    assert list(df["n_wp_online"]) == [10, 12, 11]
    assert df["e_warmtepomp_gem__kWh"].dtype == "float32"
    assert df["temp_aanvoer_gem__degC"].tolist() == pytest.approx([40.0, 26.0, 42.0])
    assert "temp_setpoint_std__degC" in df.columns


def test_heatpump_steering_kw_naar_w(dataset_zip):
    df = lezers.lees_heatpump_steering_15m(dataset_zip)
    assert "n_wp_gestuurd" in df.columns
    assert list(df["n_wp_gestuurd"]) == [2, 3, 5]
    assert df["p_limiet_gem__W"].tolist() == pytest.approx([1000.0, 933.0, 800.0])
    assert df["p_limiet_med__W"].tolist() == pytest.approx([1000.0, 900.0, 750.0])


def test_smartmeters_gas_hourly_kolomvertaling(dataset_zip):
    df = lezers.lees_smartmeters_gas_hourly(dataset_zip)
    assert "g_gebruik_gem__m3" in df.columns
    assert df["g_gebruik_gem__m3"].tolist() == pytest.approx([0.0075, 0.0070, 0.0050])
    assert df["n_meter_gas"].dtype == "int32"


def test_household_monthly_gebruikt_custom_id_niet_id(dataset_zip):
    df = lezers.lees_household_monthly(dataset_zip)
    assert "custom_id__str" in df.columns
    assert "id" not in df.columns
    assert set(df["custom_id__str"]) == {"aaa111", "bbb222"}
    assert "e_warmtepomp_tot__kWh" in df.columns
    assert df["e_warmtepomp_tot__kWh"].tolist() == pytest.approx([20.4, 7.1, 33.0])


def test_household_monthly_maand_start_is_geen_utc_instant(dataset_zip):
    # De bron: `month` is een Europe/Amsterdam-kalenderlabel, geen UTC-tijdstip. In tegenstelling
    # tot `tijdstip_start` elders hoort dit dus GEEN tz-aware kolom te zijn.
    df = lezers.lees_household_monthly(dataset_zip)
    assert df["maand_start"].dt.tz is None
    assert df["maand_start"].iloc[0] == pd.Timestamp("2024-09-01")


def test_metadata_letterlijk_overgenomen(dataset_zip):
    df = lezers.lees_metadata(dataset_zip)
    assert "field" in df.columns
    assert "custom_id" in set(df["field"])
    # dtype=str/keep_default_na=False: lege velden zijn lege tekst, geen NaN
    assert (df["unit_symbol"] == "").all()


# ── De kwartierverschuiving (ontwerp §4.1) ───────────────────────────────────

def test_wijktrafo_schuift_een_kwartier_terug(trafo_zip):
    df = lezers.lees_wijktrafo_15min(trafo_zip)
    verwacht = pd.to_datetime(
        ["2023-12-04 23:00:00+00:00", "2023-12-04 23:15:00+00:00"], utc=True
    )
    assert list(df["tijdstip_start"]) == list(verwacht)


def test_wijktrafo_belasting_kw_naar_w(trafo_zip):
    df = lezers.lees_wijktrafo_15min(trafo_zip)
    assert df["p_trafo_L1__W"].tolist() == pytest.approx([1234.0, 2500.0])
    assert df["p_trafo_L2__W"].tolist() == pytest.approx([500.0, 600.0])


def test_wijktrafo_stroom_en_spanning_niet_geschaald(trafo_zip):
    df = lezers.lees_wijktrafo_15min(trafo_zip)
    assert df["i_trafo_L1__A"].tolist() == pytest.approx([168.34, 194.28])
    assert df["u_trafo_L1__V"].tolist() == pytest.approx([230.1, 229.8])


def test_geen_P_is_U_maal_I_toets_gebouwd():
    # ontwerp §4.2: bewust NIET gebouwd. Bewaakt dat niemand die later per ongeluk toevoegt onder
    # een voor de hand liggende naam.
    from dacs_hw_preprocessing import lezers as d

    verboden_namen = {"toets_vermogen", "controleer_p_is_u_i", "toets_p_ui", "controleer_vermogen"}
    aanwezig = verboden_namen & set(dir(d))
    assert not aanwezig, f"Onverwachte P=U*I-toets gevonden: {aanwezig} (ontwerp §4.2 verbiedt dit)"


# ── Ontbrekende data ─────────────────────────────────────────────────────────

def test_ontbrekend_archief_geeft_duidelijke_foutmelding(tmp_path):
    with pytest.raises(lezers.DacsHwDataOntbreekt) as exc_info:
        lezers.lees_heatpump_15m(tmp_path / "bestaat-niet.zip")
    assert "GEBRUIKSVOORWAARDEN.md" in str(exc_info.value)


# ── Tegen de echte data, als die er is (skip anders) ─────────────────────────

_echte_data_aanwezig = lezers.DATASET_ZIP.exists() and lezers.TRAFO_ZIP.exists()


@pytest.mark.skipif(not _echte_data_aanwezig, reason="Echte DACS-HW-data niet aanwezig (gitignored)")
def test_echte_data_rijaantallen_en_periode_heatpump_15m():
    # ontwerp §1: 43.962 rijen, 2024-08-31 22:00 .. 2025-12-04 10:45 UTC
    df = lezers.lees_heatpump_15m()
    assert len(df) == 43_962
    assert df["tijdstip_start"].min() == pd.Timestamp("2024-08-31 22:00:00", tz="UTC")
    assert df["tijdstip_start"].max() == pd.Timestamp("2025-12-04 10:45:00", tz="UTC")


@pytest.mark.skipif(not _echte_data_aanwezig, reason="Echte DACS-HW-data niet aanwezig (gitignored)")
def test_echte_data_rijaantallen_heatpump_steering():
    df = lezers.lees_heatpump_steering_15m()
    assert len(df) == 2_763


@pytest.mark.skipif(not _echte_data_aanwezig, reason="Echte DACS-HW-data niet aanwezig (gitignored)")
def test_echte_data_rijaantallen_gas_hourly():
    df = lezers.lees_smartmeters_gas_hourly()
    assert len(df) == 11_018


@pytest.mark.skipif(not _echte_data_aanwezig, reason="Echte DACS-HW-data niet aanwezig (gitignored)")
def test_echte_data_household_monthly_93_woningen():
    df = lezers.lees_household_monthly()
    assert len(df) == 1_334
    assert df["custom_id__str"].nunique() == 93


@pytest.mark.skipif(not _echte_data_aanwezig, reason="Echte DACS-HW-data niet aanwezig (gitignored)")
def test_echte_data_wijktrafo_verschoven_periode():
    df = lezers.lees_wijktrafo_15min()
    assert len(df) == 69_320
    assert df["tijdstip_start"].min() == pd.Timestamp("2023-12-04 23:00:00", tz="UTC")
    assert df["tijdstip_start"].max() == pd.Timestamp("2025-12-04 10:45:00", tz="UTC")


@pytest.mark.skipif(not _echte_data_aanwezig, reason="Echte DACS-HW-data niet aanwezig (gitignored)")
def test_echte_data_metadata_66_rijen():
    df = lezers.lees_metadata()
    assert len(df) == 66
