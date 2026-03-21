"""Unit tests for coordinator LED executor handling."""

import sys
import types
from typing import Generic, TypeVar
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock


# Minimal stubs so the coordinator module can be imported without Home Assistant.
if "homeassistant" not in sys.modules:
    homeassistant = types.ModuleType("homeassistant")
    sys.modules["homeassistant"] = homeassistant

if "homeassistant.config_entries" not in sys.modules:
    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = object
    sys.modules["homeassistant.config_entries"] = config_entries

if "homeassistant.core" not in sys.modules:
    core = types.ModuleType("homeassistant.core")

    class HomeAssistant:  # pragma: no cover - runtime stub
        pass

    def callback(func):
        return func

    core.HomeAssistant = HomeAssistant
    core.callback = callback
    sys.modules["homeassistant.core"] = core

if "homeassistant.helpers.update_coordinator" not in sys.modules:
    helpers_uc = types.ModuleType("homeassistant.helpers.update_coordinator")
    _T = TypeVar("_T")

    class DataUpdateCoordinator(Generic[_T]):  # pragma: no cover - runtime stub
        def __init__(self, hass, logger, name=None, update_interval=None):
            self.hass = hass

    class UpdateFailed(Exception):
        pass

    helpers_uc.DataUpdateCoordinator = DataUpdateCoordinator
    helpers_uc.UpdateFailed = UpdateFailed
    sys.modules["homeassistant.helpers.update_coordinator"] = helpers_uc

from custom_components.tplink_powerline.coordinator import TpLinkPowerlineCoordinator


class _FakeHass:
    def __init__(self, result=None, exc: Exception | None = None):
        self._result = result
        self._exc = exc

    async def async_add_executor_job(self, func, *args):
        if self._exc:
            raise self._exc
        return self._result


class TestCoordinatorLed(IsolatedAsyncioTestCase):
    async def test_async_set_led_uses_executor_job_result(self):
        fake = types.SimpleNamespace(
            hass=_FakeHass(result=True),
            hp=types.SimpleNamespace(set_led=MagicMock(return_value=True)),
        )

        result = await TpLinkPowerlineCoordinator.async_set_led(fake, "AA:BB:CC:DD:EE:FF", True)

        self.assertTrue(result)

    async def test_async_set_led_returns_false_on_exception(self):
        fake = types.SimpleNamespace(
            hass=_FakeHass(exc=RuntimeError("executor failed")),
            hp=types.SimpleNamespace(set_led=MagicMock(return_value=True)),
        )

        result = await TpLinkPowerlineCoordinator.async_set_led(fake, "AA:BB:CC:DD:EE:FF", False)

        self.assertFalse(result)
