"""End-to-end tests voor `pijplijn.py`, op de synthetische fixtures uit conftest.py."""

from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
import pytest

from dacs_hw_preprocessing import pijplijn
from dacs_hw_preprocessing.manifest import UITVOER_CONTRACT_VERSIE
from tests.conftest import bouw_dataset_zip, bouw_trafo_zip


@pytest.fixture()
def raw_dir(tmp_path: Path) -> Path:
    raw = tmp_path / "raw"
    raw.mkdir()
    bouw_dataset_zip(raw / "dataset-dacs-hw.zip")
    bouw_trafo_zip(raw / "wijktrafo_15min.zip")
    return raw


def test_run_schrijft_alle_zes_tabellen(raw_dir: Path, tmp_path: Path, monkeypatch):
    uit_dir = tmp_path / "processed"
    docs_dir = tmp_path / "docs"
    # datapackage.json belandt standaard in de repo-root (parents[2] vanaf pijplijn.py); voor de
    # test verplaatsen we dat naar een eigen tijdelijke werkdirectory zodat een testrun nooit de
    # ECHTE datapackage.json van deze repo overschrijft.
    monkeypatch.chdir(tmp_path)
    resultaten = pijplijn.run(raw_dir, uit_dir, docs_dir=docs_dir)

    for naam in (
        "heatpump_15m", "heatpump_steering_15m", "smartmeters_gas_hourly",
        "household_monthly", "wijktrafo_15min", "metadata",
    ):
        pad = uit_dir / f"{naam}.parquet"
        assert pad.is_file(), f"{naam}.parquet ontbreekt"
        assert pq.ParquetFile(pad).metadata.num_rows > 0

    assert (uit_dir / "_manifest.jsonl").is_file()
    assert (docs_dir / "data-quality.md").is_file()
    assert "toets_aanvoer_retour" in resultaten


def test_run_hervat_een_eerdere_run(raw_dir: Path, tmp_path: Path, monkeypatch):
    uit_dir = tmp_path / "processed"
    docs_dir = tmp_path / "docs"
    monkeypatch.chdir(tmp_path)

    pijplijn.run(raw_dir, uit_dir, docs_dir=docs_dir)
    manifest_inhoud_voor = (uit_dir / "_manifest.jsonl").read_text(encoding="utf-8")

    # tweede aanroep: alles staat al in het manifest, dus er wordt niets herschreven (de
    # manifestregels, met hun sha256 en tijdstip, blijven ongewijzigd)
    pijplijn.run(raw_dir, uit_dir, docs_dir=docs_dir)
    manifest_inhoud_na = (uit_dir / "_manifest.jsonl").read_text(encoding="utf-8")
    assert manifest_inhoud_voor == manifest_inhoud_na


def test_tijdstip_kolommen_staan_in_europe_amsterdam(raw_dir: Path, tmp_path: Path, monkeypatch):
    uit_dir = tmp_path / "processed"
    monkeypatch.chdir(tmp_path)
    pijplijn.run(raw_dir, uit_dir, docs_dir=tmp_path / "docs")

    for naam in ("heatpump_15m", "heatpump_steering_15m", "smartmeters_gas_hourly", "wijktrafo_15min"):
        schema = pq.ParquetFile(uit_dir / f"{naam}.parquet").schema_arrow
        veld = schema.field("tijdstip_start")
        assert str(veld.type.tz) == "Europe/Amsterdam", f"{naam}.tijdstip_start staat niet in Europe/Amsterdam"

    # household_monthly.maand_start blijft NAIEF (geen tijdzone)
    schema = pq.ParquetFile(uit_dir / "household_monthly.parquet").schema_arrow
    assert schema.field("maand_start").type.tz is None


def test_droogloop_schrijft_niets(raw_dir: Path, tmp_path: Path):
    uit_dir = tmp_path / "processed"
    resultaat = pijplijn.run(raw_dir, uit_dir, droogloop=True)
    assert resultaat == {"droogloop": True}
    assert not uit_dir.exists()


def test_manifest_bevat_contractversie(raw_dir: Path, tmp_path: Path, monkeypatch):
    uit_dir = tmp_path / "processed"
    monkeypatch.chdir(tmp_path)
    pijplijn.run(raw_dir, uit_dir, docs_dir=tmp_path / "docs")
    regel = (uit_dir / "_manifest.jsonl").read_text(encoding="utf-8").splitlines()[0]
    assert UITVOER_CONTRACT_VERSIE in regel
