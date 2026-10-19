# SPDX-License-Identifier: EUPL-1.2
"""Tijdzones (ontwerp-preprocessing.md §3, §4.1).

**Intern UTC, in de uitvoer Europe/Amsterdam.** Elke tz-aware tijdstempel (`tijdstip_start` in
``heatpump_15m``, ``heatpump_steering_15m``, ``smartmeters_gas_hourly`` en ``wijktrafo_15min``) wordt
eerst met :func:`naar_utc_tijdstip` naar UTC geparsed (dat is ook meteen wat de bron al draagt: alle
vier bestanden gebruiken een ISO-8601-tijdstempel met een expliciete UTC-offset) en pas als laatste
stap, vlak voor het schrijven, met :func:`naar_weergave_tijdzone` omgezet naar de weergavezone
:data:`TIJDZONE_WEERGAVE` (Europe/Amsterdam). Dat is een zuivere weergavezone-omzetting: het instant
zelf verandert niet, alleen de tz-metadata. Zelfde patroon als de WarmingUP- en
IM3-preprocessingrepo's.

**`household_monthly`'s `maand_start` is hierop de uitzondering.** De bron zegt expliciet dat dit een
Europe/Amsterdam-KALENDERLABEL is, geen instant (`README_dataset.md`, "Time interpretation": *"Monthly
`month` values are Europe/Amsterdam calendar labels ... not an instant or UTC timestamp"*). Deze
kolom wordt daarom bewust NAÏEF (zonder tijdzone) geparsed en blijft dat ook in de uitvoer: een
kalendermaand die naar UTC omgerekend zou worden, zou van maand kunnen verschuiven.
"""

from __future__ import annotations

import pandas as pd

#: Weergavezone van alle tz-aware `tijdstip_start`-kolommen in de uitvoer (elke tabel behalve
#: `household_monthly` en `metadata`). Onderbouwing (eindrapport Bisschop et al., *Digitale
#: Aggregatie en Collectieve Sturing van Hybride Warmtepompen, Openbare versie*, 23 januari 2026,
#: p. 10: "Een fysieke pilot heeft plaatsgevonden in het dorp Dalen (gemeente Coevorden)"; p. 8: "In
#: totaal zijn 97 toestellen in Dalen geplaatst en getest"): de meting is één fysieke veldproef in
#: Dalen, gemeente Coevorden, provincie Drenthe, dus Europees Nederland. Bevestigd door de
#: KITE-projectpagina (zie GEBRUIKSVOORWAARDEN.md): "een uitgebreide veldtest met 100 hybride
#: warmtepompen in woningen ... aangesloten op één wijktransformator". **Het instant zelf verandert
#: niet**: dit is een weergavezone-omzetting op een kolom die al correct als UTC is geparsed
#: (:func:`naar_utc_tijdstip` blijft de eerste, interne stap), geen herinterpretatie van een naïeve
#: tijdstempel.
TIJDZONE_WEERGAVE = "Europe/Amsterdam"


def naar_utc_tijdstip(kolom: pd.Series) -> pd.Series:
    """Parseer een tz-aware ISO-8601-kolom (met `+00:00`- of `Z`-offset, beide vormen komen in de
    bron voor, zie ontwerp-preprocessing.md §3) naar tz-aware ``datetime64[ns, UTC]``. Faalt hard op
    een niet-parseerbare waarde: een stille ``NaT`` zou een gat in de dekking maskeren als een echte
    meting."""
    return pd.to_datetime(kolom, utc=True, format="ISO8601", errors="raise")


def naar_weergave_tijdzone(kolom: pd.Series) -> pd.Series:
    """Zet een tz-aware kolom (intern al correct als UTC geparsed, zie :func:`naar_utc_tijdstip`) om
    naar de weergavezone :data:`TIJDZONE_WEERGAVE` (Europe/Amsterdam). ``Series.dt.tz_convert``
    verandert het instant NIET, alleen de tz-metadata waarmee het getoond wordt."""
    return kolom.dt.tz_convert(TIJDZONE_WEERGAVE)


def naar_kalendermaand(kolom: pd.Series) -> pd.Series:
    """`household_monthly`'s `month`-kolom: een Europe/Amsterdam-kalenderlabel, GEEN instant (zie de
    moduledocstring). Gevalideerd als datum (faalt hard op een onparseerbare waarde) maar bewust
    NAÏEF (zonder tijdzone) opgeslagen; een omzetting naar UTC zou de maand zelf kunnen laten
    verschuiven."""
    return pd.to_datetime(kolom, format="%Y-%m-%d", errors="raise")
