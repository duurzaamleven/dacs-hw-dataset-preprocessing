"""Kolomvertaling (ontwerp-preprocessing.md §3).

Conform `physiquant__unit`: eenheid na de dubbele underscore. Omdat de bron aggregaten levert,
krijgt elke statistiekkolom een suffix vóór die dubbele underscore: `_mean` -> `_gem`,
`_median` -> `_med`, `_lower_quartile` -> `_q25`, `_upper_quartile` -> `_q75`, `_std` -> `_std`.
De coveragekolommen (`*_count`, hoeveel systemen/meters bijdroegen) krijgen een `n_`-naam; ze horen
bij iedere uitspraak over de bijbehorende statistiek.

Kolommen die het KITE-eindrapport niet noemt (alle `_median`/`_lower_quartile`/`_upper_quartile`-
varianten, de coveragekolommen en heel `household_monthly.csv`) zijn hier in dezelfde stijl bedacht.
"""

from __future__ import annotations

HEATPUMP_15M_KOLOMMEN: dict[str, str] = {
    "interval_start": "tijdstip_start",
    "hp_online_count": "n_wp_online",
    "boiler_thermal_hp_count": "n_wp_ketel",
    "boiler_thermal_energy_kwh_mean": "q_ketel_gem__kWh",
    "boiler_thermal_energy_kwh_median": "q_ketel_med__kWh",
    "boiler_thermal_energy_kwh_lower_quartile": "q_ketel_q25__kWh",
    "boiler_thermal_energy_kwh_upper_quartile": "q_ketel_q75__kWh",
    "heatpump_thermal_hp_count": "n_wp_warmtepomp",
    "heatpump_thermal_energy_kwh_mean": "q_warmtepomp_gem__kWh",
    "heatpump_thermal_energy_kwh_median": "q_warmtepomp_med__kWh",
    "heatpump_thermal_energy_kwh_lower_quartile": "q_warmtepomp_q25__kWh",
    "heatpump_thermal_energy_kwh_upper_quartile": "q_warmtepomp_q75__kWh",
    "electricity_hp_count": "n_wp_elektriciteit",
    "electricity_consumption_kwh_mean": "e_warmtepomp_gem__kWh",
    "electricity_consumption_kwh_median": "e_warmtepomp_med__kWh",
    "electricity_consumption_kwh_lower_quartile": "e_warmtepomp_q25__kWh",
    "electricity_consumption_kwh_upper_quartile": "e_warmtepomp_q75__kWh",
    "room_temperature_hp_count": "n_wp_temp_binnen",
    "room_temperature_c_mean": "temp_binnen_gem__degC",
    "room_temperature_c_median": "temp_binnen_med__degC",
    "room_temperature_c_lower_quartile": "temp_binnen_q25__degC",
    "room_temperature_c_upper_quartile": "temp_binnen_q75__degC",
    "room_setpoint_hp_count": "n_wp_setpoint",
    "room_setpoint_c_mean": "temp_setpoint_gem__degC",
    "room_setpoint_c_median": "temp_setpoint_med__degC",
    "room_setpoint_c_lower_quartile": "temp_setpoint_q25__degC",
    "room_setpoint_c_upper_quartile": "temp_setpoint_q75__degC",
    "room_setpoint_c_std": "temp_setpoint_std__degC",
    "inlet_water_temperature_hp_count": "n_wp_temp_retour",
    "inlet_water_temperature_c_mean": "temp_retour_gem__degC",
    "inlet_water_temperature_c_median": "temp_retour_med__degC",
    "inlet_water_temperature_c_lower_quartile": "temp_retour_q25__degC",
    "inlet_water_temperature_c_upper_quartile": "temp_retour_q75__degC",
    "outlet_water_temperature_hp_count": "n_wp_temp_aanvoer",
    "outlet_water_temperature_c_mean": "temp_aanvoer_gem__degC",
    "outlet_water_temperature_c_median": "temp_aanvoer_med__degC",
    "outlet_water_temperature_c_lower_quartile": "temp_aanvoer_q25__degC",
    "outlet_water_temperature_c_upper_quartile": "temp_aanvoer_q75__degC",
}
# Telkolommen (`n_wp_*`): getal, geen fysische eenheid, dus geen `__`-suffix.
HEATPUMP_15M_TELKOLOMMEN = tuple(v for v in HEATPUMP_15M_KOLOMMEN.values() if v.startswith("n_wp_"))

HEATPUMP_STEERING_15M_KOLOMMEN: dict[str, str] = {
    "interval_start": "tijdstip_start",
    "steered_hwp_count": "n_wp_gestuurd",
    "power_limit_kw_mean": "p_limiet_gem__W",  # x 1000
    "power_limit_kw_median": "p_limiet_med__W",  # x 1000, zelfde stijl als _mean
}
POWER_LIMIT_KW_KOLOMMEN = ("p_limiet_gem__W", "p_limiet_med__W")

SMARTMETERS_GAS_HOURLY_KOLOMMEN: dict[str, str] = {
    "interval_start": "tijdstip_start",
    "gas_meter_count": "n_meter_gas",
    "gas_delivered_m3_mean": "g_gebruik_gem__m3",
    "gas_delivered_m3_median": "g_gebruik_med__m3",
    "gas_delivered_m3_lower_quartile": "g_gebruik_q25__m3",
    "gas_delivered_m3_upper_quartile": "g_gebruik_q75__m3",
}

# household_monthly.csv: sleutel is `custom_id`, niet `id` zoals metadata.csv abusievelijk beweert
# (ontwerp §7). LET OP, afwijking van README_dataset.md: de lopende tekst noemt de laatste twee
# velden `hwp_electricity_kwh`/`hwp_gas_m3`, maar zowel de CSV-header als metadata.csv gebruiken
# `hp_electricity_kwh`/`hp_gas_m3` (zonder de "w"). De data en metadata.csv zijn hier leidend.
HOUSEHOLD_MONTHLY_KOLOMMEN: dict[str, str] = {
    "month": "maand_start",
    "custom_id": "custom_id__str",
    "total_electricity_delivered_kwh": "e_geleverd_tot__kWh",
    "total_electricity_returned_kwh": "e_teruglevering_tot__kWh",
    "total_net_electricity_consumption_kwh": "e_net_tot__kWh",
    "total_gas_delivered_m3": "g_geleverd_tot__m3",
    "hp_electricity_kwh": "e_warmtepomp_tot__kWh",
    "hp_gas_m3": "g_warmtepomp_tot__m3",
}

# wijktrafo_15min.csv (Enexis): stroom en spanning behoeven geen eenheidsconversie (al A resp. V);
# belasting wel (kW -> W, x 1000).
WIJKTRAFO_15MIN_KOLOMMEN: dict[str, str] = {
    "timestamp": "tijdstip_start",
    "stroom_L1": "i_trafo_L1__A",
    "stroom_L2": "i_trafo_L2__A",
    "stroom_L3": "i_trafo_L3__A",
    "spanning_L1": "u_trafo_L1__V",
    "spanning_L2": "u_trafo_L2__V",
    "spanning_L3": "u_trafo_L3__V",
    "belasting_L1": "p_trafo_L1__W",  # x 1000
    "belasting_L2": "p_trafo_L2__W",  # x 1000, zelfde stijl als L1
    "belasting_L3": "p_trafo_L3__W",  # x 1000, zelfde stijl als L1
}
BELASTING_KW_KOLOMMEN = ("p_trafo_L1__W", "p_trafo_L2__W", "p_trafo_L3__W")

#: Kwartierverschuiving wijktrafodata (ontwerp §4.1): de bron is EIND-gelabeld, de rest van deze
#: dataset is BEGIN-gelabeld. Dit gebeurt op precies één plek: in `lezers.lees_wijktrafo_15min`.
KWARTIER = "15min"
