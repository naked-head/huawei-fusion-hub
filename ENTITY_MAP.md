# Entity correspondence map

Full mapping between Huawei Fusion Hub entities and their sources.

Legend: `—` = not provided by that integration. Source columns show the
pattern used for matching: **register name** (unique_id `{serial}_{register}`)
for Huawei Solar; **device model : signal id** (unique_id `{device_id}_{signal_id}`)
for FusionSolarPlus; **device model : attribute** (unique_id
`fusion_solar-{id}-{attribute}`) for FusionSolar — plant rows use the Kiosk
sensor ids, device rows use the Northbound/OpenAPI realtime device attributes
(model prefixes: `Residential inverter`, `String inverter`, `Battery`,
`Power Sensor`, `Grid meter`). FusionSolarPlus device models are the
device types of its config flow: `Inverter`, `Battery`, `Power Sensor`,
`Plant` and `SmartAssistant` (EMMA).

A hub entity is created when **at least one** configured source provides the
quantity; single-source entities have no failover but keep a stable name.
Entity categories follow the source layout: measurements are regular sensors,
statuses and identifiers are **Diagnostic**, writable proxies are **Configuration**.

## Inverter (38 entities)

| Hub entity (`sensor.hf_hub_…`) | Huawei Solar (Modbus) | FusionSolarPlus | FusionSolar |
|---|---|---|---|
| `inverter_rated_power` | `rated_power` | `Inverter:10006` | — |
| `inverter_p_max` | `p_max` | — | — |
| `pv_input_power` | `input_power` | `Plant:flow_solar_power` | `Residential inverter:mppt_power`, `String inverter:mppt_power` |
| `inverter_line_voltage_a_b` | `line_voltage_a_b` | — | `Residential inverter:ab_u`, `String inverter:ab_u` |
| `inverter_line_voltage_b_c` | `line_voltage_b_c` | — | `Residential inverter:bc_u`, `String inverter:bc_u` |
| `inverter_line_voltage_c_a` | `line_voltage_c_a` | — | `Residential inverter:ca_u`, `String inverter:ca_u` |
| `inverter_phase_a_voltage` | `phase_a_voltage` | `Inverter:10011`, `Inverter:10008` | `Residential inverter:a_u`, `String inverter:a_u` |
| `inverter_phase_b_voltage` | `phase_b_voltage` | `Inverter:10012` | `Residential inverter:b_u`, `String inverter:b_u` |
| `inverter_phase_c_voltage` | `phase_c_voltage` | `Inverter:10013` | `Residential inverter:c_u`, `String inverter:c_u` |
| `inverter_phase_a_current` | `phase_a_current` | `Inverter:10014` | `Residential inverter:a_i`, `String inverter:a_i` |
| `inverter_phase_b_current` | `phase_b_current` | `Inverter:10015` | `Residential inverter:b_i`, `String inverter:b_i` |
| `inverter_phase_c_current` | `phase_c_current` | `Inverter:10016` | `Residential inverter:c_i`, `String inverter:c_i` |
| `inverter_day_active_power_peak` | `day_active_power_peak` | — | — |
| `pv_active_power` | `active_power` | `Inverter:10018` | `Residential inverter:active_power`, `String inverter:active_power` |
| `inverter_reactive_power` | `reactive_power` | `Inverter:10019` | `Residential inverter:reactive_power`, `String inverter:reactive_power` |
| `inverter_power_factor` | `power_factor` | `Inverter:10020` | `Residential inverter:power_factor`, `String inverter:power_factor` |
| `inverter_grid_frequency` | `grid_frequency` | `Inverter:10021` | `Residential inverter:elec_freq`, `String inverter:elec_freq` |
| `inverter_efficiency` | `efficiency` | — | `Residential inverter:efficiency`, `String inverter:efficiency` |
| `inverter_temperature` | `internal_temperature` | `Inverter:10023` | `Residential inverter:temperature`, `String inverter:temperature` |
| `inverter_insulation_resistance` | `insulation_resistance` | `Inverter:10024` | — |
| `inverter_status` | `device_status` | `Inverter:10025` | `Residential inverter:inverter_state`, `String inverter:inverter_state` |
| `inverter_startup_time` | `startup_time` | `Inverter:10027` | `Residential inverter:open_time`, `String inverter:open_time` |
| `inverter_shutdown_time` | `shutdown_time` | `Inverter:10028` | `Residential inverter:close_time`, `String inverter:close_time` |
| `inverter_yield_total` | `accumulated_yield_energy` | `Inverter:10029` | `Residential inverter:total_cap`, `String inverter:total_cap` |
| `inverter_total_dc_input_energy` | `total_dc_input_power` | — | — |
| `inverter_statistics_time` | `current_electricity_generation_statistics_time` | — | — |
| `inverter_yield_hour` | `hourly_yield_energy` | — | — |
| `inverter_yield_today` | `daily_yield_energy` | `Inverter:10032` | `Residential inverter:day_cap`, `String inverter:day_cap` |
| `inverter_yield_month` | `monthly_yield_energy` | — | — |
| `inverter_yield_year` | `yearly_yield_energy` | — | — |
| `inverter_state_1` | `state_1` | — | — |
| `inverter_output_mode` | — | `Inverter:21029` | — |
| `pv_1_voltage` | `pv_01_voltage` | `Inverter:11001` | `Residential inverter:pv1_u`, `String inverter:pv1_u` |
| `pv_1_current` | `pv_01_current` | `Inverter:11002` | `Residential inverter:pv1_i`, `String inverter:pv1_i` |
| `pv_1_power` | — | `Inverter:11003` | — |
| `pv_2_voltage` | `pv_02_voltage` | `Inverter:11004` | `Residential inverter:pv2_u`, `String inverter:pv2_u` |
| `pv_2_current` | `pv_02_current` | `Inverter:11005` | `Residential inverter:pv2_i`, `String inverter:pv2_i` |
| `pv_2_power` | — | `Inverter:11006` | — |

## Power Meter (28 entities)

| Hub entity (`sensor.hf_hub_…`) | Huawei Solar (Modbus) | FusionSolarPlus | FusionSolar |
|---|---|---|---|
| `meter_status` | `meter_status` | `Power Sensor:10001` | `Power Sensor:meter_status` |
| `meter_active_power` | `power_meter_active_power` | `Power Sensor:10004`, `Power Sensor:11207`, `Power Sensor:2101271`, `SmartAssistant:11207` | `Power Sensor:active_power`, `Grid meter:active_power` |
| `meter_reactive_power` | `power_meter_reactive_power` | `Power Sensor:10005`, `Power Sensor:11208`, `Power Sensor:2101272`, `SmartAssistant:11208` | `Power Sensor:reactive_power`, `Grid meter:reactive_power` |
| `meter_power_factor` | `active_grid_power_factor` | `Power Sensor:10006`, `Power Sensor:10014`, `Power Sensor:2101280`, `SmartAssistant:10014` | `Power Sensor:power_factor`, `Grid meter:power_factor` |
| `meter_frequency` | `active_grid_frequency` | `Power Sensor:10007` | `Power Sensor:grid_frequency`, `Grid meter:grid_frequency`, `Residential inverter:elec_freq` |
| `grid_exported_energy` | `grid_exported_energy` | `Power Sensor:10008`, `Power Sensor:11116`, `SmartAssistant:11116` | `Power Sensor:reverse_active_cap`, `Grid meter:reverse_active_cap` |
| `grid_imported_energy` | `grid_accumulated_energy` | `Power Sensor:10009`, `Power Sensor:11115`, `SmartAssistant:11115` | `Power Sensor:active_cap`, `Grid meter:active_cap` |
| `meter_reactive_energy` | `grid_accumulated_reactive_power` | — | — |
| `meter_phase_a_voltage` | `grid_a_voltage` | `Power Sensor:10002`, `Power Sensor:11204`, `Power Sensor:2101256`, `SmartAssistant:11204` | `Power Sensor:a_u`, `Grid meter:a_u` |
| `meter_phase_a_current` | `active_grid_a_current` | `Power Sensor:10003`, `Power Sensor:2101268`, `SmartAssistant:10009` | `Power Sensor:a_i`, `Grid meter:a_i` |
| `meter_phase_a_active_power` | `active_grid_a_power` | `Power Sensor:10019`, `Power Sensor:2101281`, `SmartAssistant:11209` | `Power Sensor:active_power_a`, `Grid meter:active_power_a` |
| `meter_phase_b_voltage` | `grid_b_voltage` | `Power Sensor:10010`, `Power Sensor:11205`, `Power Sensor:2101257`, `SmartAssistant:11205` | `Power Sensor:b_u`, `Grid meter:b_u` |
| `meter_phase_b_current` | `active_grid_b_current` | `Power Sensor:10012`, `Power Sensor:2101269`, `SmartAssistant:10010` | `Power Sensor:b_i`, `Grid meter:b_i` |
| `meter_phase_b_active_power` | `active_grid_b_power` | `Power Sensor:10020`, `Power Sensor:2101282`, `SmartAssistant:11210` | `Power Sensor:active_power_b`, `Grid meter:active_power_b` |
| `meter_phase_c_voltage` | `grid_c_voltage` | `Power Sensor:10011`, `Power Sensor:11206`, `Power Sensor:2101264`, `SmartAssistant:11206` | `Power Sensor:c_u`, `Grid meter:c_u` |
| `meter_phase_c_current` | `active_grid_c_current` | `Power Sensor:10013`, `Power Sensor:2101270`, `SmartAssistant:10011` | `Power Sensor:c_i`, `Grid meter:c_i` |
| `meter_phase_c_active_power` | `active_grid_c_power` | `Power Sensor:10021`, `Power Sensor:2101283`, `SmartAssistant:11211` | `Power Sensor:active_power_c`, `Grid meter:active_power_c` |
| `meter_line_voltage_a_b` | `active_grid_a_b_voltage` | `Power Sensor:2101252` | `Power Sensor:ab_u`, `Grid meter:ab_u` |
| `meter_line_voltage_b_c` | `active_grid_b_c_voltage` | `Power Sensor:2101253` | `Power Sensor:bc_u`, `Grid meter:bc_u` |
| `meter_line_voltage_c_a` | `active_grid_c_a_voltage` | `Power Sensor:2101254` | `Power Sensor:ca_u`, `Grid meter:ca_u` |
| `meter_rs485_port_mode` | — | `Power Sensor:230700283` | — |
| `meter_wifi_signal_strength` | — | `Power Sensor:15101` | — |
| `meter_signal_strength` | — | `Power Sensor:15102` | — |
| `meter_communication_status` | — | `Power Sensor:2101249`, `Power Sensor:2101602` | — |
| `meter_iacmeter` | — | `Power Sensor:2101600` | — |
| `meter_iacmeter_ip` | — | `Power Sensor:2101601` | — |
| `meter_iacmeter_mode` | — | `Power Sensor:2101605` | — |
| `meter_data_source` | — | `Power Sensor:2101606` | — |

## Battery (system) (14 entities)

| Hub entity (`sensor.hf_hub_…`) | Huawei Solar (Modbus) | FusionSolarPlus | FusionSolar |
|---|---|---|---|
| `battery_soc` | `storage_state_of_capacity` | `Battery:10006` | `Battery:battery_soc` |
| `battery_power` | `storage_charge_discharge_power` | `Battery:10004` | `Battery:ch_discharge_power` |
| `battery_charged_today` | `storage_current_day_charge_capacity` | `Battery:10001` | `Battery:charge_cap` |
| `battery_discharged_today` | `storage_current_day_discharge_capacity` | `Battery:10002` | `Battery:discharge_cap` |
| `battery_total_charge` | `storage_total_charge` | — | — |
| `battery_total_discharge` | `storage_total_discharge` | — | — |
| `battery_status` | `storage_running_status` | `Battery:10003` | `Battery:battery_status` |
| `battery_bus_voltage` | `storage_bus_voltage` | `Battery:10005` | `Battery:busbar_u` |
| `battery_bus_current` | `storage_bus_current` | — | — |
| `battery_rated_capacity` | `storage_rated_capacity` | `Battery:10013` | — |
| `battery_max_charge_power` | `storage_maximum_charge_power` | — | `Battery:max_charge_power` |
| `battery_max_discharge_power` | `storage_maximum_discharge_power` | — | `Battery:max_discharge_power` |
| `battery_working_mode` | — | `Battery:10008` | `Battery:ch_discharge_model` |
| `battery_backup_time` | — | `Battery:10015` | — |

## Battery Unit 1 (huawei_solar unit 1 ↔ FSP Module 1) (62 entities)

| Hub entity (`sensor.hf_hub_…`) | Huawei Solar (Modbus) | FusionSolarPlus | FusionSolar |
|---|---|---|---|
| `battery_unit_1_working_mode` | `storage_unit_1_working_mode_b` | — | — |
| `battery_unit_1_charged_today` | `storage_unit_1_current_day_charge_capacity` | `Battery:230320469` | — |
| `battery_unit_1_discharged_today` | `storage_unit_1_current_day_discharge_capacity` | `Battery:230320470` | — |
| `battery_unit_1_bus_current` | `storage_unit_1_bus_current` | `Battery:230320461` | — |
| `battery_unit_1_bus_voltage` | `storage_unit_1_bus_voltage` | `Battery:230320460` | — |
| `battery_unit_1_temperature` | `storage_unit_1_battery_temperature` | `Battery:230320462` | — |
| `battery_unit_1_remaining_time` | `storage_unit_1_remaining_charge_dis_charge_time` | — | — |
| `battery_unit_1_total_charge` | `storage_unit_1_total_charge` | `Battery:230320107` | — |
| `battery_unit_1_total_discharge` | `storage_unit_1_total_discharge` | `Battery:230320108` | — |
| `battery_unit_1_soc` | `storage_unit_1_state_of_capacity` | `Battery:230320463` | — |
| `battery_unit_1_status` | `storage_unit_1_running_status` | `Battery:230320459` | — |
| `battery_unit_1_power` | `storage_unit_1_charge_discharge_power` | `Battery:230320473` | — |
| `battery_unit_1_no` | `storage_unit_1_no` | `Battery:230320252` | — |
| `battery_unit_1_sn` | — | `Battery:230320275` | — |
| `battery_unit_1_software_version` | `storage_unit_1_software_version` | `Battery:230320146` | — |
| `battery_unit_1_fe_connection` | — | `Battery:230320514` | — |
| `battery_unit_1_soh_calibration` | `storage_unit_soh_calibration_status` | — | — |
| `battery_unit_1_pack_1_no` | — | `Battery:230320265` | — |
| `battery_unit_1_pack_1_status` | `storage_unit_1_battery_pack_1_working_status` | `Battery:230320151` | — |
| `battery_unit_1_pack_1_firmware_version` | `storage_unit_1_battery_pack_1_firmware_version` | `Battery:230320148` | — |
| `battery_unit_1_pack_1_serial_number` | `storage_unit_1_battery_pack_1_serial_number` | `Battery:230320147` | — |
| `battery_unit_1_pack_1_voltage` | `storage_unit_1_battery_pack_1_voltage` | `Battery:230320159` | — |
| `battery_unit_1_pack_1_power` | `storage_unit_1_battery_pack_1_charge_discharge_power` | `Battery:230320158` | — |
| `battery_unit_1_pack_1_soc` | `storage_unit_1_battery_pack_1_state_of_capacity` | `Battery:230320152` | — |
| `battery_unit_1_pack_1_max_temperature` | `storage_unit_1_battery_pack_1_maximum_temperature` | `Battery:230320446` | — |
| `battery_unit_1_pack_1_min_temperature` | `storage_unit_1_battery_pack_1_minimum_temperature` | `Battery:230320447` | — |
| `battery_unit_1_pack_1_total_discharge` | `storage_unit_1_battery_pack_1_total_discharge` | `Battery:230320163` | — |
| `battery_unit_1_pack_1_health_check` | — | `Battery:230320492` | — |
| `battery_unit_1_pack_1_heating_status` | — | `Battery:230320498` | — |
| `battery_unit_1_pack_1_current` | `storage_unit_1_battery_pack_1_current` | — | — |
| `battery_unit_1_pack_1_soh_calibration` | `storage_unit_1_battery_pack_1_soh_calibration_status` | — | — |
| `battery_unit_1_pack_1_total_charge` | `storage_unit_1_battery_pack_1_total_charge` | — | — |
| `battery_unit_1_pack_2_no` | — | `Battery:230320266` | — |
| `battery_unit_1_pack_2_status` | `storage_unit_1_battery_pack_2_working_status` | `Battery:230320168` | — |
| `battery_unit_1_pack_2_firmware_version` | `storage_unit_1_battery_pack_2_firmware_version` | `Battery:230320165` | — |
| `battery_unit_1_pack_2_serial_number` | `storage_unit_1_battery_pack_2_serial_number` | `Battery:230320164` | — |
| `battery_unit_1_pack_2_voltage` | `storage_unit_1_battery_pack_2_voltage` | `Battery:230320174` | — |
| `battery_unit_1_pack_2_power` | `storage_unit_1_battery_pack_2_charge_discharge_power` | `Battery:230320173` | — |
| `battery_unit_1_pack_2_soc` | `storage_unit_1_battery_pack_2_state_of_capacity` | `Battery:230320169` | — |
| `battery_unit_1_pack_2_max_temperature` | `storage_unit_1_battery_pack_2_maximum_temperature` | `Battery:230320448` | — |
| `battery_unit_1_pack_2_min_temperature` | `storage_unit_1_battery_pack_2_minimum_temperature` | `Battery:230320449` | — |
| `battery_unit_1_pack_2_total_discharge` | `storage_unit_1_battery_pack_2_total_discharge` | `Battery:230320179` | — |
| `battery_unit_1_pack_2_health_check` | — | `Battery:230320493` | — |
| `battery_unit_1_pack_2_heating_status` | — | `Battery:230320499` | — |
| `battery_unit_1_pack_2_current` | `storage_unit_1_battery_pack_2_current` | — | — |
| `battery_unit_1_pack_2_soh_calibration` | `storage_unit_1_battery_pack_2_soh_calibration_status` | — | — |
| `battery_unit_1_pack_2_total_charge` | `storage_unit_1_battery_pack_2_total_charge` | — | — |
| `battery_unit_1_pack_3_no` | — | `Battery:230320267` | — |
| `battery_unit_1_pack_3_status` | `storage_unit_1_battery_pack_3_working_status` | `Battery:230320184` | — |
| `battery_unit_1_pack_3_firmware_version` | `storage_unit_1_battery_pack_3_firmware_version` | `Battery:230320181` | — |
| `battery_unit_1_pack_3_serial_number` | `storage_unit_1_battery_pack_3_serial_number` | `Battery:230320180` | — |
| `battery_unit_1_pack_3_voltage` | `storage_unit_1_battery_pack_3_voltage` | `Battery:230320190` | — |
| `battery_unit_1_pack_3_power` | `storage_unit_1_battery_pack_3_charge_discharge_power` | `Battery:230320189` | — |
| `battery_unit_1_pack_3_soc` | `storage_unit_1_battery_pack_3_state_of_capacity` | `Battery:230320185` | — |
| `battery_unit_1_pack_3_max_temperature` | `storage_unit_1_battery_pack_3_maximum_temperature` | `Battery:230320450` | — |
| `battery_unit_1_pack_3_min_temperature` | `storage_unit_1_battery_pack_3_minimum_temperature` | `Battery:230320451` | — |
| `battery_unit_1_pack_3_total_discharge` | `storage_unit_1_battery_pack_3_total_discharge` | `Battery:230320194` | — |
| `battery_unit_1_pack_3_health_check` | — | `Battery:230320494` | — |
| `battery_unit_1_pack_3_heating_status` | — | `Battery:230320500` | — |
| `battery_unit_1_pack_3_current` | `storage_unit_1_battery_pack_3_current` | — | — |
| `battery_unit_1_pack_3_soh_calibration` | `storage_unit_1_battery_pack_3_soh_calibration_status` | — | — |
| `battery_unit_1_pack_3_total_charge` | `storage_unit_1_battery_pack_3_total_charge` | — | — |

## Battery Unit 2 (huawei_solar unit 2 ↔ FSP Module 2) (61 entities)

| Hub entity (`sensor.hf_hub_…`) | Huawei Solar (Modbus) | FusionSolarPlus | FusionSolar |
|---|---|---|---|
| `battery_unit_2_working_mode` | `storage_unit_2_working_mode_b` | — | — |
| `battery_unit_2_charged_today` | `storage_unit_2_current_day_charge_capacity` | `Battery:230320471` | — |
| `battery_unit_2_discharged_today` | `storage_unit_2_current_day_discharge_capacity` | `Battery:230320472` | — |
| `battery_unit_2_bus_current` | `storage_unit_2_bus_current` | `Battery:230320466` | — |
| `battery_unit_2_bus_voltage` | `storage_unit_2_bus_voltage` | `Battery:230320465` | — |
| `battery_unit_2_temperature` | `storage_unit_2_battery_temperature` | `Battery:230320467` | — |
| `battery_unit_2_remaining_time` | `storage_unit_2_remaining_charge_dis_charge_time` | — | — |
| `battery_unit_2_total_charge` | `storage_unit_2_total_charge` | `Battery:230320114` | — |
| `battery_unit_2_total_discharge` | `storage_unit_2_total_discharge` | `Battery:230320115` | — |
| `battery_unit_2_soc` | `storage_unit_2_state_of_capacity` | `Battery:230320468` | — |
| `battery_unit_2_status` | `storage_unit_2_running_status` | `Battery:230320464` | — |
| `battery_unit_2_power` | `storage_unit_2_charge_discharge_power` | `Battery:230320474` | — |
| `battery_unit_2_no` | `storage_unit_2_no` | `Battery:230320253` | — |
| `battery_unit_2_sn` | — | `Battery:230320276` | — |
| `battery_unit_2_software_version` | `storage_unit_2_software_version` | `Battery:230320145` | — |
| `battery_unit_2_fe_connection` | — | `Battery:230320515` | — |
| `battery_unit_2_pack_1_no` | — | `Battery:230320268` | — |
| `battery_unit_2_pack_1_status` | `storage_unit_2_battery_pack_1_working_status` | `Battery:230320199` | — |
| `battery_unit_2_pack_1_firmware_version` | `storage_unit_2_battery_pack_1_firmware_version` | `Battery:230320196` | — |
| `battery_unit_2_pack_1_serial_number` | `storage_unit_2_battery_pack_1_serial_number` | `Battery:230320195` | — |
| `battery_unit_2_pack_1_voltage` | `storage_unit_2_battery_pack_1_voltage` | `Battery:230320205` | — |
| `battery_unit_2_pack_1_power` | `storage_unit_2_battery_pack_1_charge_discharge_power` | `Battery:230320204` | — |
| `battery_unit_2_pack_1_soc` | `storage_unit_2_battery_pack_1_state_of_capacity` | `Battery:230320200` | — |
| `battery_unit_2_pack_1_max_temperature` | `storage_unit_2_battery_pack_1_maximum_temperature` | `Battery:230320452` | — |
| `battery_unit_2_pack_1_min_temperature` | `storage_unit_2_battery_pack_1_minimum_temperature` | `Battery:230320453` | — |
| `battery_unit_2_pack_1_total_discharge` | `storage_unit_2_battery_pack_1_total_discharge` | `Battery:230320209` | — |
| `battery_unit_2_pack_1_health_check` | — | `Battery:230320495` | — |
| `battery_unit_2_pack_1_heating_status` | — | `Battery:230320501` | — |
| `battery_unit_2_pack_1_current` | `storage_unit_2_battery_pack_1_current` | — | — |
| `battery_unit_2_pack_1_soh_calibration` | `storage_unit_2_battery_pack_1_soh_calibration_status` | — | — |
| `battery_unit_2_pack_1_total_charge` | `storage_unit_2_battery_pack_1_total_charge` | — | — |
| `battery_unit_2_pack_2_no` | — | `Battery:230320269` | — |
| `battery_unit_2_pack_2_status` | `storage_unit_2_battery_pack_2_working_status` | `Battery:230320214` | — |
| `battery_unit_2_pack_2_firmware_version` | `storage_unit_2_battery_pack_2_firmware_version` | `Battery:230320211` | — |
| `battery_unit_2_pack_2_serial_number` | `storage_unit_2_battery_pack_2_serial_number` | `Battery:230320210` | — |
| `battery_unit_2_pack_2_voltage` | `storage_unit_2_battery_pack_2_voltage` | `Battery:230320220` | — |
| `battery_unit_2_pack_2_power` | `storage_unit_2_battery_pack_2_charge_discharge_power` | `Battery:230320219` | — |
| `battery_unit_2_pack_2_soc` | `storage_unit_2_battery_pack_2_state_of_capacity` | `Battery:230320215` | — |
| `battery_unit_2_pack_2_max_temperature` | `storage_unit_2_battery_pack_2_maximum_temperature` | `Battery:230320454` | — |
| `battery_unit_2_pack_2_min_temperature` | `storage_unit_2_battery_pack_2_minimum_temperature` | `Battery:230320455` | — |
| `battery_unit_2_pack_2_total_discharge` | `storage_unit_2_battery_pack_2_total_discharge` | `Battery:230320224` | — |
| `battery_unit_2_pack_2_health_check` | — | `Battery:230320496` | — |
| `battery_unit_2_pack_2_heating_status` | — | `Battery:230320502` | — |
| `battery_unit_2_pack_2_current` | `storage_unit_2_battery_pack_2_current` | — | — |
| `battery_unit_2_pack_2_soh_calibration` | `storage_unit_2_battery_pack_2_soh_calibration_status` | — | — |
| `battery_unit_2_pack_2_total_charge` | `storage_unit_2_battery_pack_2_total_charge` | — | — |
| `battery_unit_2_pack_3_no` | — | `Battery:230320270` | — |
| `battery_unit_2_pack_3_status` | `storage_unit_2_battery_pack_3_working_status` | `Battery:230320229` | — |
| `battery_unit_2_pack_3_firmware_version` | `storage_unit_2_battery_pack_3_firmware_version` | `Battery:230320226` | — |
| `battery_unit_2_pack_3_serial_number` | `storage_unit_2_battery_pack_3_serial_number` | `Battery:230320225` | — |
| `battery_unit_2_pack_3_voltage` | `storage_unit_2_battery_pack_3_voltage` | `Battery:230320235` | — |
| `battery_unit_2_pack_3_power` | `storage_unit_2_battery_pack_3_charge_discharge_power` | `Battery:230320234` | — |
| `battery_unit_2_pack_3_soc` | `storage_unit_2_battery_pack_3_state_of_capacity` | `Battery:230320230` | — |
| `battery_unit_2_pack_3_max_temperature` | `storage_unit_2_battery_pack_3_maximum_temperature` | `Battery:230320456` | — |
| `battery_unit_2_pack_3_min_temperature` | `storage_unit_2_battery_pack_3_minimum_temperature` | `Battery:230320457` | — |
| `battery_unit_2_pack_3_total_discharge` | `storage_unit_2_battery_pack_3_total_discharge` | `Battery:230320239` | — |
| `battery_unit_2_pack_3_health_check` | — | `Battery:230320497` | — |
| `battery_unit_2_pack_3_heating_status` | — | `Battery:230320503` | — |
| `battery_unit_2_pack_3_current` | `storage_unit_2_battery_pack_3_current` | — | — |
| `battery_unit_2_pack_3_soh_calibration` | `storage_unit_2_battery_pack_3_soh_calibration_status` | — | — |
| `battery_unit_2_pack_3_total_charge` | `storage_unit_2_battery_pack_3_total_charge` | — | — |

## Plant (18 entities)

| Hub entity (`sensor.hf_hub_…`) | Huawei Solar (Modbus) | FusionSolarPlus | FusionSolar |
|---|---|---|---|
| `plant_power` | — | `Plant:flow_solar_power` | `realtime_power` |
| `plant_energy_today` | — | `Plant:dailyEnergy` | `total_current_day_energy` |
| `plant_energy_month` | — | `Plant:monthEnergy` | `total_current_month_energy` |
| `plant_energy_year` | — | `Plant:yearEnergy` | `total_current_year_energy` |
| `plant_energy_total` | — | `Plant:cumulativeEnergy` | `total_lifetime_energy` |
| `plant_income_today` | — | `Plant:dailyIncome` | — |
| `self_used_energy_today` | — | `Plant:totalSelfUseEnergy` | — |
| `consumption_today` | — | `Plant:dailyUseEnergy` | — |
| `pv_self_consumption_energy` | — | `Plant:pvSelfConsumptionEnergy` | — |
| `pv_feed_in_energy_today` | — | `Plant:totalFeedInEnergy` | — |
| `imported_grid_energy_today` | — | `Plant:totalGridImportEnergy` | — |
| `total_consumption` | — | `Plant:totalConsumptionEnergy` | — |
| `grid_import_ratio` | — | `Plant:gridImportRatio` | — |
| `self_consumption_ratio` | — | `Plant:pvSelfConsumptionRatio` | — |
| `self_consumption_ratio_by_production` | — | `Plant:pvSelfConsumptionRatioByProduction` | — |
| `flow_battery_power` | — | `Plant:flow_battery_power` | — |
| `flow_load_power` | — | `Plant:flow_load_power` | — |
| `flow_grid_power` | — | `Plant:flow_grid_power` | — |

## EMMA / Smart Assistant (11 entities)

Configuration parameters published by FusionSolarPlus 2.3.5 and later for
devices of model `SmartAssistant`. They come from a separate endpoint that
FusionSolarPlus refreshes at most every five minutes, and they are read-only:
there is no failover and no write-through proxy. `huawei_solar` offers the
comparable settings as writable `number` and `select` controls (see the
Controls section below), while FusionSolar does not expose them at all.

The device group is created only when an EMMA is present. Every entity is
Diagnostic except `emma_peak_power`, the only one that changes on its own as
the peak shaving schedule moves from one period to the next. Enumerations are
published as plain text, because the hub does not carry the source option list.
The schedule details of the peak power setting (`periods`, `period_count`,
`config_updated_at`) remain attributes of the FusionSolarPlus entity and are
not copied to the hub entity.

> **Unverified.** These rows were derived from the FusionSolarPlus source
> code and have never been tested against a real EMMA installation.

| Hub entity (`sensor.hf_hub_…`) | Huawei Solar (Modbus) | FusionSolarPlus | FusionSolar |
|---|---|---|---|
| `emma_peak_power` | — | `SmartAssistant:230700179` | — |
| `emma_peak_shaving_mode` | — | `SmartAssistant:230700177` | — |
| `emma_peak_shaving_backup_soc` | — | `SmartAssistant:230700178` | — |
| `emma_working_mode` | — | `SmartAssistant:21021` | — |
| `emma_active_power_control_mode` | — | `SmartAssistant:21115` | — |
| `emma_max_grid_feed_in_power` | — | `SmartAssistant:21098` | — |
| `emma_max_mains_power` | — | `SmartAssistant:230700200` | — |
| `emma_allowed_ac_charge_power` | — | `SmartAssistant:21110` | — |
| `emma_charge_from_ac` | — | `SmartAssistant:230700278` | — |
| `emma_grid_charge_cutoff_soc` | — | `SmartAssistant:230700279` | — |
| `emma_pv_power_priority` | — | `SmartAssistant:230700180` | — |

## Controls — write-through proxies (18 entities, opt-in)

Created only when "Aggregate control entities" is enabled in the config
flow. These proxies mirror the source state and forward every command to
the source entity (switch, select, number setpoints and buttons). Controls
exist only on the Modbus connection, so there is no failover — see the
configuration step for why leaving them disabled is recommended.

| Hub entity | Platform | Huawei Solar (Modbus) | FusionSolarPlus | FusionSolar |
|---|---|---|---|---|
| `inverter_power` | `switch` | `startup` | — | — |
| `battery_charge_from_grid` | `switch` | `storage_charge_from_grid_function` | — | — |
| `mppt_multimodal_scanning` | `switch` | `mppt_multimodal_scanning` | — | — |
| `battery_working_mode_select` | `select` | `storage_working_mode_settings` | — | — |
| `battery_excess_pv_energy_use_in_tou` | `select` | `storage_excess_pv_energy_use_in_tou` | — | — |
| `battery_capacity_control_mode` | `select` | `storage_capacity_control_mode` | — | — |
| `inverter_power_derating_percent` | `number` | `active_power_percentage_derating` | — | — |
| `inverter_power_derating_watt` | `number` | `active_power_fixed_value_derating` | — | — |
| `mppt_scanning_interval` | `number` | `mppt_scanning_interval` | — | — |
| `battery_maximum_charging_power` | `number` | `storage_maximum_charging_power` | — | — |
| `battery_maximum_discharging_power` | `number` | `storage_maximum_discharging_power` | — | — |
| `battery_end_of_charge_soc` | `number` | `storage_charging_cutoff_capacity` | — | — |
| `battery_end_of_discharge_soc` | `number` | `storage_discharging_cutoff_capacity` | — | — |
| `battery_backup_power_soc` | `number` | `storage_backup_power_state_of_charge` | — | — |
| `battery_grid_charge_cutoff_soc` | `number` | `storage_grid_charge_cutoff_state_of_charge` | — | — |
| `battery_grid_charge_maximum_power` | `number` | `storage_power_of_charge_from_grid` | — | — |
| `battery_peak_shaving_soc` | `number` | `storage_capacity_control_soc_peak_shaving` | — | — |
| `battery_stop_forcible_charge` | `button` | `stop_forcible_charge` | — | — |

**Total hub entities: 232 sensors + 18 optional controls**
