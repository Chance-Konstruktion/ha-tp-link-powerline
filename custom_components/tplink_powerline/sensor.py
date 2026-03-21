"""Sensor platform for Powerline Network.

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

from .const import DOMAIN, MANUFACTURER, NETWORK_DEVICE_ID, NETWORK_DEVICE_NAME, get_mac
from .coordinator import TpLinkPowerlineCoordinator

_LOGGER = logging.getLogger(__name__)


def _device_info(mac: str, firmware: str) -> DeviceInfo:
    """Build DeviceInfo for a single Powerline adapter."""
    return DeviceInfo(
        identifiers={(DOMAIN, mac)},
        name=f"Powerline {mac[-8:]}",
        manufacturer=MANUFACTURER,
        model="Powerline Adapter",
        sw_version=firmware or None,
    )


def _network_device_info() -> DeviceInfo:
    """Build DeviceInfo for the network-wide virtual device."""
    return DeviceInfo(
        identifiers={(DOMAIN, NETWORK_DEVICE_ID)},
        name=NETWORK_DEVICE_NAME,
        manufacturer=MANUFACTURER,
        model="Powerline Network",
    )


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
            mac = get_mac(dev)
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

    # Network-wide aggregate sensors (English names, translated via strings.json)
    entities.append(TotalSensor(coordinator, "total_tx_rate", "TX Total",
                                UnitOfDataRate.MEGABITS_PER_SECOND, "mdi:upload-network"))
    entities.append(TotalSensor(coordinator, "total_rx_rate", "RX Total",
                                UnitOfDataRate.MEGABITS_PER_SECOND, "mdi:download-network"))
    entities.append(TotalSensor(coordinator, "plc_device_count", "Adapters Online",
                                None, "mdi:lan"))
    entities.append(TotalSensor(coordinator, "plc_device_count_total", "Adapters Total",
                                None, "mdi:lan-check"))

    # Per-device sensors for already-known devices
    if coordinator.data:
        devs = coordinator.data.get("plc_devices", {})
        device_list = list(devs.values()) if isinstance(devs, dict) else devs
        _create_entities_for_devices(device_list)

    async_add_entities(entities)


# ─── Network-wide sensors ─────────────────────────────────────────────

class TotalSensor(CoordinatorEntity[TpLinkPowerlineCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: TpLinkPowerlineCoordinator, key: str,
                 name: str, unit: str | None, icon: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"tplink_plc_{key}"
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        if unit:
            self._attr_device_class = SensorDeviceClass.DATA_RATE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_info = _network_device_info()

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

    def __init__(self, coordinator: TpLinkPowerlineCoordinator, mac: str, firmware: str) -> None:
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

    def __init__(self, coordinator: TpLinkPowerlineCoordinator, mac: str, firmware: str) -> None:
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

    def __init__(self, coordinator: TpLinkPowerlineCoordinator, mac: str, firmware: str) -> None:
        super().__init__(coordinator)
        self._mac = mac
        self._attr_unique_id = f"plc_{mac}_online"
        self._attr_name = "Status"
        self._attr_device_info = _device_info(mac, firmware)

    @property
    def native_value(self) -> str | None:
        devs = (self.coordinator.data or {}).get("plc_devices", {})
        dev = devs.get(self._mac) if isinstance(devs, dict) else None
        if dev:
            return "Online" if dev.get("_online", True) else "Offline"
        return "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        devs = (self.coordinator.data or {}).get("plc_devices", {})
        dev = devs.get(self._mac) if isinstance(devs, dict) else None
        if dev:
            return {
                "mac": self._mac,
                "firmware": dev.get("firmware_ver", ""),
                "same_network": dev.get("same_network", True),
            }
        return {"mac": self._mac}
