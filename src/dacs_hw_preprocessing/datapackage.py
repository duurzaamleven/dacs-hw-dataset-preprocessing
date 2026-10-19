# SPDX-License-Identifier: EUPL-1.2
"""Bouwt ``datapackage.json`` (Frictionless Data Package v1, met een Table Schema per resource) UIT
DE CODE, niet met de hand bijgehouden.

**Bron van waarheid.** De velden per resource komen uit de ``pyarrow.Schema``-objecten in
``tabellen.SCHEMAS``, dezelfde schema's die de pijplijn gebruikt om te schrijven (``pijplijn.py``).
Een test (``tests/test_datapackage.py``) borgt dat elk veld in een schema in het datapackage staat en
omgekeerd, dus de twee kunnen niet uit de pas lopen zonder dat een test rood wordt.

**`primaryKey`: alleen waar geverifieerd uniek.** Op de echte, volledige dataset (17-09-2026, zie
GEBRUIKSVOORWAARDEN.md voor de sha256's) is ``tijdstip_start`` uniek binnen ``heatpump_15m``,
``heatpump_steering_15m``, ``smartmeters_gas_hourly`` en ``wijktrafo_15min``; ``(maand_start,
custom_id__str)`` is uniek binnen ``household_monthly``; ``(field, file)`` is uniek binnen
``metadata`` (``field`` alleen niet: dezelfde veldnaam, bijvoorbeeld ``interval_start``, wordt voor
meerdere brontabellen gedocumenteerd).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyarrow as pa

from . import tabellen
from .manifest import UITVOER_CONTRACT_VERSIE

DATAPACKAGE_BESTANDSNAAM = "datapackage.json"
#: Standaardplek van datapackage.json: de repo-root, naast README en GEBRUIKSVOORWAARDEN.md.
STANDAARD_DATAPACKAGE_PAD = Path(__file__).resolve().parents[2] / DATAPACKAGE_BESTANDSNAAM

KITE_PAGINA_URL = "https://kennisdelen.rvo.nl/"  # community "Kennis- en Dataplatform Individuele Technieken", projectpagina DACS-HW
WONINGDATA_URL = "https://data.inversable.cloud/dacs-hw/dataset-dacs-hw.zip"
WONINGDATA_SHA256 = "f251e66129f3eae25490d799f2e0cf7dae2290adcd7527476c05fb28aefc2bcf"
WONINGDATA_OMVANG__B = 2_140_045
TRAFODATA_SHA256 = "23b1d080d57f5fbb950f82885a8455826a1e5a134989dae4a32184785ef87c93"
TRAFODATA_OMVANG__B = 1_991_982

_ARROW_NAAR_TYPE = {
    pa.types.is_string: "string",
    pa.types.is_boolean: "boolean",
    pa.types.is_integer: "integer",
    pa.types.is_floating: "number",
    pa.types.is_timestamp: "datetime",
}


def _table_schema_type(arrow_type: pa.DataType) -> tuple[str, dict]:
    for test, naam in _ARROW_NAAR_TYPE.items():
        if test(arrow_type):
            extra = {}
            if naam == "datetime":
                extra["format"] = "default"  # ISO 8601; pyarrow schrijft dit al zo naar Parquet
            return naam, extra
    raise ValueError(f"Geen Table Schema-type bekend voor Arrow-type {arrow_type!r}")


#: Beschrijving per (resourcenaam, veldnaam), overgenomen uit docs/datacatalogus.md. Een veld dat
#: hier niet in staat, krijgt een generieke tekst (zie ``_veld`` hieronder).
VELD_BESCHRIJVINGEN: dict[str, dict[str, str]] = {
    "heatpump_15m": {
        "tijdstip_start": "Begin van het kwartierinterval [tijdstip_start, tijdstip_start + 15 min), "
        "tz-aware Europe/Amsterdam (bron: UTC, verliesvrij omgezet).",
        "n_wp_online": "Aantal warmtepompsystemen dat in dit kwartier minstens één metriek meldde.",
        "n_wp_ketel": "Aantal systemen dat een geldige ketel-warmtewaarde leverde in dit kwartier.",
        "q_ketel_gem__kWh": "Gemiddelde door de ketel geleverde warmte per bijdragend systeem (geen gasvolume).",
        "q_ketel_med__kWh": "Mediane door de ketel geleverde warmte per bijdragend systeem.",
        "q_ketel_q25__kWh": "Onderkwartiel van de door de ketel geleverde warmte.",
        "q_ketel_q75__kWh": "Bovenkwartiel van de door de ketel geleverde warmte.",
        "n_wp_warmtepomp": "Aantal systemen dat een geldige warmtepomp-warmtewaarde leverde.",
        "q_warmtepomp_gem__kWh": "Gemiddelde door de warmtepomp (elektrisch) geleverde warmte.",
        "q_warmtepomp_med__kWh": "Mediane door de warmtepomp geleverde warmte.",
        "q_warmtepomp_q25__kWh": "Onderkwartiel van de door de warmtepomp geleverde warmte.",
        "q_warmtepomp_q75__kWh": "Bovenkwartiel van de door de warmtepomp geleverde warmte.",
        "n_wp_elektriciteit": "Aantal systemen dat een geldige elektriciteitswaarde leverde.",
        "e_warmtepomp_gem__kWh": "Gemiddeld elektrisch verbruik van de warmtepompsystemen in dit kwartier.",
        "e_warmtepomp_med__kWh": "Mediaan elektrisch verbruik.",
        "e_warmtepomp_q25__kWh": "Onderkwartiel elektrisch verbruik.",
        "e_warmtepomp_q75__kWh": "Bovenkwartiel elektrisch verbruik.",
        "n_wp_temp_binnen": "Aantal systemen dat een geldige binnentemperatuur leverde.",
        "temp_binnen_gem__degC": "Gemiddelde gemeten binnentemperatuur.",
        "temp_binnen_med__degC": "Mediane gemeten binnentemperatuur.",
        "temp_binnen_q25__degC": "Onderkwartiel binnentemperatuur.",
        "temp_binnen_q75__degC": "Bovenkwartiel binnentemperatuur.",
        "n_wp_setpoint": "Aantal systemen dat een geldig setpoint leverde.",
        "temp_setpoint_gem__degC": "Gemiddelde ingestelde (gewenste) temperatuur.",
        "temp_setpoint_med__degC": "Mediane ingestelde temperatuur.",
        "temp_setpoint_q25__degC": "Onderkwartiel ingestelde temperatuur.",
        "temp_setpoint_q75__degC": "Bovenkwartiel ingestelde temperatuur.",
        "temp_setpoint_std__degC": "Standaarddeviatie van de ingestelde temperatuur over de bijdragende systemen.",
        "n_wp_temp_retour": "Aantal systemen dat een geldige inlet-temperatuur (retour) leverde.",
        "temp_retour_gem__degC": "Gemiddelde retourtemperatuur (bron: inlet_water_temperature; interpretatie, zie ontwerp §5).",
        "temp_retour_med__degC": "Mediane retourtemperatuur.",
        "temp_retour_q25__degC": "Onderkwartiel retourtemperatuur.",
        "temp_retour_q75__degC": "Bovenkwartiel retourtemperatuur.",
        "n_wp_temp_aanvoer": "Aantal systemen dat een geldige outlet-temperatuur (aanvoer) leverde.",
        "temp_aanvoer_gem__degC": "Gemiddelde aanvoertemperatuur (bron: outlet_water_temperature; interpretatie, zie ontwerp §5).",
        "temp_aanvoer_med__degC": "Mediane aanvoertemperatuur.",
        "temp_aanvoer_q25__degC": "Onderkwartiel aanvoertemperatuur.",
        "temp_aanvoer_q75__degC": "Bovenkwartiel aanvoertemperatuur.",
    },
    "heatpump_steering_15m": {
        "tijdstip_start": "Begin van het kwartierinterval, tz-aware Europe/Amsterdam. Alleen kwartieren met "
        "minstens twee gestuurde warmtepompen staan in deze tabel.",
        "n_wp_gestuurd": "Aantal distincte warmtepompen dat in dit kwartier werd aangestuurd.",
        "p_limiet_gem__W": "Gemiddeld opgelegd vermogenslimiet over de gestuurde warmtepompen (bron in kW, x1000).",
        "p_limiet_med__W": "Mediaan opgelegd vermogenslimiet.",
    },
    "smartmeters_gas_hourly": {
        "tijdstip_start": "Begin van het uurinterval, tz-aware Europe/Amsterdam.",
        "n_meter_gas": "Aantal slimme meters dat een geldige gaswaarde leverde in dit uur.",
        "g_gebruik_gem__m3": "Gemiddeld gasgebruik per bijdragende meter.",
        "g_gebruik_med__m3": "Mediaan gasgebruik.",
        "g_gebruik_q25__m3": "Onderkwartiel gasgebruik.",
        "g_gebruik_q75__m3": "Bovenkwartiel gasgebruik.",
    },
    "household_monthly": {
        "maand_start": "Kalendermaand (Europe/Amsterdam-label), GEEN tz-aware instant; zie tijd.py.",
        "custom_id__str": "Gepseudonimiseerde woningsleutel, stabiel binnen deze dataset; NIET koppelbaar "
        "aan de kwartierbestanden.",
        "e_geleverd_tot__kWh": "Totaal aan het net onttrokken elektriciteit in deze maand.",
        "e_teruglevering_tot__kWh": "Totaal aan het net teruggeleverde elektriciteit in deze maand.",
        "e_net_tot__kWh": "Netto elektriciteitsverbruik (geleverd min teruglevering) in deze maand.",
        "g_geleverd_tot__m3": "Totaal geleverd gasvolume in deze maand.",
        "e_warmtepomp_tot__kWh": "Elektriciteitsverbruik van het warmtepompsysteem in deze maand (bron: hp_electricity_kwh).",
        "g_warmtepomp_tot__m3": "Gasgebruik gerapporteerd door het hybride warmtepompsysteem in deze maand (bron: hp_gas_m3).",
    },
    "wijktrafo_15min": {
        "tijdstip_start": "Begin van het kwartierinterval, tz-aware Europe/Amsterdam. Bron is eind-gelabeld "
        "en is bij het inlezen één kwartier teruggeschoven (ontwerp §4.1).",
        "i_trafo_L1__A": "Stroom op fase L1 van de wijktransformator.",
        "i_trafo_L2__A": "Stroom op fase L2.",
        "i_trafo_L3__A": "Stroom op fase L3.",
        "u_trafo_L1__V": "Spanning op fase L1.",
        "u_trafo_L2__V": "Spanning op fase L2.",
        "u_trafo_L3__V": "Spanning op fase L3.",
        "p_trafo_L1__W": "Belasting op fase L1 (bron in kW, x1000). Let op: stroom x spanning is NIET "
        "gelijk aan belasting, zie ontwerp §4.2.",
        "p_trafo_L2__W": "Belasting op fase L2.",
        "p_trafo_L3__W": "Belasting op fase L3.",
    },
    "metadata": {
        "field": "Veldnaam zoals gedocumenteerd door de bron; komt voor meerdere brontabellen dezelfde "
        "naam voor (bijvoorbeeld interval_start), dus dit veld alleen is GEEN sleutel.",
        "description": "Beschrijving van het veld, letterlijk overgenomen.",
        "file": "Brontabel waar dit veld bij hoort, letterlijk overgenomen (bevat twee niet-bestaande "
        "bestandsnamen, zie ontwerp §7).",
        "unit_name": "Eenheidsnaam, letterlijk overgenomen.",
        "unit_symbol": "Eenheidssymbool, letterlijk overgenomen.",
        "resolution": "Tijdresolutie, letterlijk overgenomen.",
        "decimals": "Aantal decimalen, letterlijk overgenomen.",
        "notes": "Toelichting, letterlijk overgenomen.",
    },
}

_PRIMARY_KEYS: dict[str, list[str]] = {
    "heatpump_15m": ["tijdstip_start"],
    "heatpump_steering_15m": ["tijdstip_start"],
    "smartmeters_gas_hourly": ["tijdstip_start"],
    "household_monthly": ["maand_start", "custom_id__str"],
    "wijktrafo_15min": ["tijdstip_start"],
    "metadata": ["field", "file"],
}

_RESOURCE_TITELS: dict[str, str] = {
    "heatpump_15m": "15-minutenaggregaat over warmtepompsystemen (energie, temperatuur)",
    "heatpump_steering_15m": "Kwartieren met minstens twee aangestuurde warmtepompen",
    "smartmeters_gas_hourly": "Uuraggregaat gasgebruik over slimme meters",
    "household_monthly": "Maandtotalen elektriciteit en gas per (gepseudonimiseerde) woning",
    "wijktrafo_15min": "Stroom, spanning en belasting van de wijktransformator in Dalen",
    "metadata": "Kolomdefinities uit de bron zelf, ongewijzigd",
}


def _veld(schema_veld: pa.Field, resourcenaam: str) -> dict:
    type_naam, extra = _table_schema_type(schema_veld.type)
    veld = {"name": schema_veld.name, "type": type_naam}
    beschrijving = VELD_BESCHRIJVINGEN.get(resourcenaam, {}).get(schema_veld.name)
    veld["description"] = beschrijving or "Zie docs/datacatalogus.md voor de volledige beschrijving van dit veld."
    veld.update(extra)
    return veld


def _resource(naam: str, schema: pa.Schema) -> dict:
    resource = {
        "name": naam,
        "title": _RESOURCE_TITELS[naam],
        "format": "parquet",
        "path": f"{naam}.parquet",
        "schema": {
            "fields": [_veld(f, naam) for f in schema],
            "missingValues": [""],
            "primaryKey": _PRIMARY_KEYS[naam],
        },
    }
    return resource


def bouw_datapackage(contract_versie: str = UITVOER_CONTRACT_VERSIE) -> dict:
    """Bouw het datapackage-object (een gewone ``dict``, direct naar JSON te schrijven)."""
    resources = [_resource(naam, schema) for naam, schema in tabellen.SCHEMAS.items()]

    return {
        "name": "dacs-hw-processed",
        "title": "DACS-HW: voorbewerkte meetdata (getypeerde Parquet-tabellen)",
        "description": (
            "Voorbewerkte meetdata van DACS-HW (Digitale Aggregatie en Collectieve Sturing van "
            "Hybride Warmtepompen, MOOI322001). Deze repo is niet de data-eigenaar; zie "
            "GEBRUIKSVOORWAARDEN.md voor licentie, meldplicht en herkomst van de twee archieven, en "
            "docs/datacatalogus.md voor de volledige beschrijving van elke tabel. Gegenereerd door "
            "dacs_hw_preprocessing.datapackage, niet met de hand bijgehouden."
        ),
        "version": contract_versie,
        "licenses": [
            {
                "name": "andere",
                "title": (
                    "Geen open licentie: geen van beide data-eigenaren (Projectgroep DACS-HW/"
                    "Inversable voor de woningdata, Enexis voor de onderstationdata) noemt een "
                    "licentienaam. Gebruik is toegestaan voor onderzoek en analyse met een "
                    "maatschappelijk doel, met een meldplicht (woningdata) respectievelijk een "
                    "downloadformulier met doel en inzicht (Enexis-data). Herverspreiding van de "
                    "ruwe dataset is niet toegestaan. Zie GEBRUIKSVOORWAARDEN.md in deze repo."
                ),
                "path": "GEBRUIKSVOORWAARDEN.md",
            }
        ],
        "sources": [
            {
                "title": "DACS-HW, KITE-projectpagina (Kennis- en Dataplatform Individuele Technieken)",
                "path": KITE_PAGINA_URL,
            },
            {
                "title": "dataset-dacs-hw.zip (woningdata: warmtepompen en slimme meters)",
                "path": WONINGDATA_URL,
                "sha256": WONINGDATA_SHA256,
                "bytes": WONINGDATA_OMVANG__B,
            },
            {
                "title": "wijktrafo_15min.zip (Enexis-onderstationdata; alleen via downloadformulier "
                "te verkrijgen, geen vaste URL, zie GEBRUIKSVOORWAARDEN.md)",
                "sha256": TRAFODATA_SHA256,
                "bytes": TRAFODATA_OMVANG__B,
            },
        ],
        "contributors": [
            {"title": "Projectgroep DACS-HW (Inversable, Voorstroom, Samen Energie Neutraal, Enablemi, Intergas, TU/e)", "role": "author"},
            {"title": "Enexis", "role": "author", "organization": "Enexis"},
            {"title": "Kenniscentrum Duurzaam Leven", "role": "processor"},
        ],
        "resources": resources,
    }


def schrijf_datapackage(pad: Path, contract_versie: str = UITVOER_CONTRACT_VERSIE) -> None:
    """Schrijf ``datapackage.json`` atomisch naar ``pad`` (``<pad>.tmp`` + hernoeming, zie manifest.py)."""
    pakket = bouw_datapackage(contract_versie)
    pad = Path(pad)
    pad.parent.mkdir(parents=True, exist_ok=True)
    tmp = pad.with_suffix(pad.suffix + ".tmp")
    tmp.write_text(json.dumps(pakket, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(pad)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--pad", type=Path, default=STANDAARD_DATAPACKAGE_PAD,
        help="Waar datapackage.json geschreven wordt (standaard: de repo-root).",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    schrijf_datapackage(args.pad)
    print(f"Geschreven: {args.pad}")


if __name__ == "__main__":
    main()
