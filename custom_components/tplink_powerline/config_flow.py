"""Config flow for TP-Link Powerline integration.

Discovery uses HomePlug AV raw Ethernet (Layer 2) — no IP needed.
The user just clicks 'Add' and all Powerline adapters are found automatically.
"""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .homeplug import HomeplugAV, find_interface, is_available

_LOGGER = logging.getLogger(__name__)


class TpLinkPowerlineConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for TP-Link Powerline."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered: list[dict[str, Any]] = []
        self._interface: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1: Check permissions and discover devices."""
        errors: dict[str, str] = {}

        available = await self.hass.async_add_executor_job(is_available)
        if not available:
            return self.async_abort(reason="raw_socket_unavailable")

        if user_input is not None:
            # User confirmed — run discovery
            self._interface = await self.hass.async_add_executor_job(
                    find_interface)
            if not self._interface:
                errors["base"] = "no_interface"
            else:
                hp = HomeplugAV(self._interface)
                self._discovered = await self.hass.async_add_executor_job(
                    hp.discover, 8.0
                )

                if self._discovered:
                    return await self.async_step_confirm()
                errors["base"] = "no_devices_found"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            errors=errors,
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2: Show discovered devices, user confirms."""
        if user_input is not None:
            # Build unique ID from all discovered MACs
            all_macs = sorted(
                d.get("mac", d.get("plcmac", "")).upper()
                for d in self._discovered
                if d.get("mac") or d.get("plcmac")
            )
            unique_id = "_".join(all_macs) if all_macs else "tplink_plc"

            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # Build title from device count
            count = len(self._discovered)
            title = f"TP-Link Powerline ({count} Adapter)"

            return self.async_create_entry(
                title=title,
                data={
                    "interface": self._interface,
                    "devices": self._discovered,
                    "device_count": count,
                },
            )

        # Show what we found
        device_lines = []
        for dev in self._discovered:
            mac = dev.get("mac", dev.get("plcmac", "?"))
            fw = dev.get("firmware_ver", "")
            tx = dev.get("tx_rate", 0)
            rx = dev.get("rx_rate", 0)
            info = f"MAC: {mac}"
            if fw:
                info += f" | FW: {fw}"
            if tx or rx:
                info += f" | TX:{tx} RX:{rx} Mbps"
            device_lines.append(info)

        description = "\n".join(device_lines) if device_lines else "?"

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "devices": description,
                "count": str(len(self._discovered)),
            },
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> "TpLinkPowerlineOptionsFlow":
        """Return options flow for this handler."""
        return TpLinkPowerlineOptionsFlow(config_entry)


class TpLinkPowerlineOptionsFlow(OptionsFlow):
    """Handle TP-Link Powerline options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = int(
            self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    )
                }
            ),
        )
