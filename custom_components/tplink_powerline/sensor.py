"""Sensor platform for TP-Link Powerline.

Creates TX/RX sensors per adapter. Dynamically adds entities
when new devices are discovered during polling.
"""

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass, SensorEntity, SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfDataRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import TpLinkPowerlineCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from config entry."""
    coordinator: TpLinkPowerlineCoordinator = hass.data[DOMAIN][entry.entry_id]
    tracked_macs: set[str] = set()

    def _create_entities_for_devices(devices: list[dict[str, Any]]) -> None:
        """Create sensor entities for a list of devices."""
        new_entities: list[SensorEntity] = []
        for dev in devices:
            mac = (dev.get("mac") or dev.get("plcmac") or "").upper()
            if not mac or mac in tracked_macs:
                continue
            tracked_macs.add(mac)
            fw = dev.get("firmware_ver", "")
            new_entities.append(PlcDeviceTxSensor(coordinator, mac, fw))
            new_entities.append(PlcDeviceRxSensor(coordinator, mac, fw))
            new_entities.append(PlcDeviceOnlineSensor(coordinator, mac, fw))
            _LOGGER.info("Creating sensors for adapter %s", mac)
        if new_entities:
            async_add_entities(new_entities)

    # Register callback for dynamically discovered devices
    coordinator.register_new_device_callback(_create_entities_for_devices)

    entities: list[SensorEntity] = []

    # Network-wide aggregate sensors
    entities.append(TotalSensor(coordinator, "total_tx_rate", "Powerline TX Gesamt",
                                UnitOfDataRate.MEGABITS_PER_SECOND, "mdi:upload-network"))
    entities.append(TotalSensor(coordinator, "total_rx_rate", "Powerline RX Gesamt",
                                UnitOfDataRate.MEGABITS_PER_SECOND, "mdi:download-network"))
    entities.append(TotalSensor(coordinator, "plc_device_count", "Powerline Adapter Online",
                                None, "mdi:lan"))
    entities.append(TotalSensor(coordinator, "plc_device_count_total", "Powerline Adapter Gesamt",
                                None, "mdi:lan-check"))

    # Per-device sensors for already-known devices
    if coordinator.data:
        initial_devs = coordinator.data.get("plc_devices", [])
        _create_entities_for_devices(initial_devs)

    async_add_entities(entities)


# ─── Network-wide sensors ─────────────────────────────────────────────

class TotalSensor(CoordinatorEntity[TpLinkPowerlineCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key: str, name: str,
                 unit: str | None, icon: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"tplink_plc_{key}"
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        if unit:
            self._attr_device_class = SensorDeviceClass.DATA_RATE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "tplink_powerline_network")},
            name="TP-Link Powerline Netzwerk",
            manufacturer=MANUFACTURER, model="Powerline Network")

    @property
    def native_value(self) -> Any:
        return (self.coordinator.data or {}).get(self._key)


# ─── Per-device sensors ───────────────────────────────────────────────

class PlcDeviceTxSensor(CoordinatorEntity[TpLinkPowerlineCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfDataRate.MEGABITS_PER_SECOND
    _attr_device_class = SensorDeviceClass.DATA_RATE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:upload-network"

    def __init__(self, coordinator, mac: str, firmware: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        self._attr_unique_id = f"plc_{mac}_tx"
        self._attr_name = "TX Rate"
        self._attr_device_info = _device_info(mac, firmware)

    @property
    def native_value(self) -> int | None:
        rates = (self.coordinator.data or {}).get("plc_rates", {})
        r = rates.get(self._mac)
        return r["tx"] if r else None


class PlcDeviceRxSensor(CoordinatorEntity[TpLinkPowerlineCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfDataRate.MEGABITS_PER_SECOND
    _attr_device_class = SensorDeviceClass.DATA_RATE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:download-network"

    def __init__(self, coordinator, mac: str, firmware: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        self._attr_unique_id = f"plc_{mac}_rx"
        self._attr_name = "RX Rate"
        self._attr_device_info = _device_info(mac, firmware)

    @property
    def native_value(self) -> int | None:
        rates = (self.coordinator.data or {}).get("plc_rates", {})
        r = rates.get(self._mac)
        return r["rx"] if r else None


class PlcDeviceOnlineSensor(CoordinatorEntity[TpLinkPowerlineCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:lan-connect"

    def __init__(self, coordinator, mac: str, firmware: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        self._attr_unique_id = f"plc_{mac}_online"
        self._attr_name = "Status"
        self._attr_device_info = _device_info(mac, firmware)

    @property
    def native_value(self) -> str | None:
        devs = (self.coordinator.data or {}).get("plc_devices", [])
        for d in devs:
            m = (d.get("mac") or d.get("plcmac") or "").upper()
            if m == self._mac:
                return "Online" if d.get("_online", True) else "Offline"
        return "Unbekannt"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        devs = (self.coordinator.data or {}).get("plc_devices", [])
        for d in devs:
            m = (d.get("mac") or d.get("plcmac") or "").upper()
            if m == self._mac:
                return {
                    "mac": self._mac,
                    "firmware": d.get("firmware_ver", ""),
                    "same_network": d.get("same_network", True),
                }
        return {"mac": self._mac}


def _device_info(mac: str, firmware: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, mac)},
        name=f"Powerline {mac[-8:]}",
        manufacturer=MANUFACTURER, model="Powerline Adapter",
        sw_version=firmware or None)
