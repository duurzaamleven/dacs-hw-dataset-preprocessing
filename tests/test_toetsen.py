# SPDX-License-Identifier: EUPL-1.2
"""Tests voor de aanvoer/retour-toets (ontwerp-preprocessing.md §5)."""

from __future__ import annotations

import pandas as pd
import pytest

from dacs_hw_preprocessing import lezers, toetsen


def test_toets_aanvoer_retour(dataset_zip):
    resultaat = toetsen.toets_aanvoer_retour(dataset_zip)
    # in de fixture leveren kwartier 1 en 3 warmte (heatpump_thermal_energy_kwh_mean > 0), en daar
    # ligt outlet (aanvoer) ruim boven inlet (retour)
    assert resultaat["n_kwartieren_met_warmtelevering"] == 2
    assert resultaat["aandeel_aanvoer_boven_retour"] == pytest.approx(1.0)
    assert resultaat["verschil_mediaan__degC"] > 0


_echte_data_aanwezig = lezers.DATASET_ZIP.exists() and lezers.TRAFO_ZIP.exists()


@pytest.mark.skipif(not _echte_data_aanwezig, reason="Echte DACS-HW-data niet aanwezig (gitignored)")
def test_echte_data_aanvoer_retour_toets_eerder_gerapporteerde_uitkomst():
    # Eerder gerapporteerde uitkomst op de volledige set: 99,16% van 39.103 kwartieren, mediaan
    # 1,29 graden C. Dit is een bevinding, geen oordeel over de interpretatie zelf; de exacte
    # getallen worden hier gecontroleerd zodat een toekomstige wijziging aan de leesroute opvalt.
    resultaat = toetsen.toets_aanvoer_retour()
    assert resultaat["n_kwartieren_met_warmtelevering"] == 39_103
    assert resultaat["n_kwartieren_met_beide_temperaturen"] == 39_103
    assert resultaat["aandeel_aanvoer_boven_retour"] == pytest.approx(0.9916, abs=1e-4)
    assert resultaat["verschil_mediaan__degC"] == pytest.approx(1.29, abs=1e-2)
