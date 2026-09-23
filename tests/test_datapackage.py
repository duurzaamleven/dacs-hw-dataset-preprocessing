"""datapackage.json wordt UIT DE CODE gebouwd (datapackage.py); deze test bewaakt dat het niet uit
de pas kan lopen met de Parquet-schema's die de code zelf gebruikt: elk veld in een schema moet in
het bijbehorende datapackage-resource staan, en omgekeerd."""

from __future__ import annotations

import json

import pytest

from dacs_hw_preprocessing import datapackage, tabellen


def test_datapackage_bouwt_zonder_fouten():
    pakket = datapackage.bouw_datapackage()
    assert pakket["resources"]
    json.dumps(pakket)  # moet JSON-serialiseerbaar zijn


def test_elke_resource_heeft_precies_de_velden_van_zijn_schema():
    pakket = datapackage.bouw_datapackage()
    resources = {r["name"]: r for r in pakket["resources"]}
    assert set(resources) == set(tabellen.SCHEMAS)

    for naam, schema in tabellen.SCHEMAS.items():
        schema_velden = set(schema.names)
        package_velden = {v["name"] for v in resources[naam]["schema"]["fields"]}
        assert schema_velden == package_velden, (
            f"{naam}: schema en datapackage lopen uit de pas.\n"
            f"alleen in schema: {schema_velden - package_velden}\n"
            f"alleen in datapackage: {package_velden - schema_velden}"
        )


def test_elk_veld_heeft_een_beschrijving():
    pakket = datapackage.bouw_datapackage()
    for resource in pakket["resources"]:
        for veld in resource["schema"]["fields"]:
            assert veld.get("description"), f"{resource['name']}.{veld['name']} heeft geen description"


def test_elke_tabel_heeft_een_primary_key():
    # Alle zes tabellen hebben, anders dan bij WarmingUP, een geverifieerd unieke sleutel op de
    # echte volledige dataset (zie datapackage.py-moduledocstring).
    pakket = datapackage.bouw_datapackage()
    for resource in pakket["resources"]:
        assert resource["schema"]["primaryKey"], f"{resource['name']} heeft geen primaryKey"


def test_licentie_verwijst_naar_gebruiksvoorwaarden_geen_open_licentienaam():
    pakket = datapackage.bouw_datapackage()
    licentie = pakket["licenses"][0]
    assert licentie["path"] == "GEBRUIKSVOORWAARDEN.md"
    assert licentie["name"] not in ("cc-by-4.0", "cc0-1.0", "odbl-1.0", "mit")


def test_version_is_de_uitvoer_contract_versie():
    from dacs_hw_preprocessing.manifest import UITVOER_CONTRACT_VERSIE

    pakket = datapackage.bouw_datapackage()
    assert pakket["version"] == UITVOER_CONTRACT_VERSIE


def test_twee_verschillende_data_eigenaren_genoemd_in_sources():
    pakket = datapackage.bouw_datapackage()
    titels = " ".join(s["title"] for s in pakket["sources"])
    assert "dataset-dacs-hw.zip" in titels
    assert "wijktrafo_15min.zip" in titels


def test_frictionless_structurele_validatie():
    """Structurele validatie (het JSON Schema-profiel van Data Package v1), zonder de Parquet-data
    zelf te lezen. Slaat zichzelf over als frictionless niet geïnstalleerd is (optionele
    dev-afhankelijkheid, zie pyproject.toml)."""
    frictionless = pytest.importorskip("frictionless")
    pakket = datapackage.bouw_datapackage()
    fouten = list(frictionless.Package.metadata_validate(pakket))
    assert fouten == []
