# 10 Real Questions My User Will Ask

These questions represent real research inquiries from IoT engineers at smart-energy startups and developers building or comparing Home Assistant integrations.

| # | Question | Where the answer is (document, source) | Needs more than one file/document? |
|---|---|---|---|
| 1 | How many integrations in Home Assistant Core declare `local_polling` versus `cloud_polling` as their `iot_class`? | `data/processed/integrations.csv` (`iot_class` column) | No (single dataset query) |
| 2 | Which integrations require external Modbus or serial communication libraries in their `requirements`? | `data/processed/integrations.json` (`requirements` field) | No (single dataset query) |
| 3 | How does the `fronius` integration handle connection timeouts and reconnection when the solar inverter is unreachable? | `homeassistant/components/fronius/coordinator.py`, `sensor.py` | Yes (multi-file source analysis) |
| 4 | How many integrations implement a UI configuration flow (`has_config_flow_py` = true or manifest `config_flow` = true)? | `data/processed/integrations.csv` | No (single dataset query) |
| 5 | What patterns do smart-meter and energy integrations use to define `device_class = sensor.SensorDeviceClass.ENERGY` and `state_class = SensorStateClass.TOTAL_INCREASING`? | `homeassistant/components/envoy/sensor.py`, `homeassistant/components/homewizard/sensor.py` | Yes (multi-integration source comparison) |
| 6 | What are the top 10 largest integrations by Python source file count? | `data/processed/integrations.csv` (`python_file_count`), `source_inventory.csv` | Yes (cross-referencing integration records and source inventory) |
| 7 | How does the `enphase_envoy` integration authenticate with Envoy firmware tokens in modern versions? | `homeassistant/components/enphase_envoy/coordinator.py`, `config_flow.py` | Yes (multi-file code analysis) |
| 8 | Which integrations declare `gold` or `platinum` in their `quality_scale` metadata? | `data/processed/integrations.csv` (`quality_scale`) | No (single dataset query) |
| 9 | How many integrations have `coordinator.py` for centralized DataUpdateCoordinator polling? | `data/processed/integrations.csv` (`has_coordinator_py`) | No (single dataset query) |
| 10 | What is the real-time wholesale electricity spot price for the Texas ERCOT grid right now? | None (cannot be answered from repository code or manifests) | No (external real-time query) |

