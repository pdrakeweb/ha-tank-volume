"""Custom types for ha_integration_domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import IntegrationBlueprintApiClient
    from .coordinator import IntegrationBlueprintDataUpdateCoordinator


type IntegrationBlueprintConfigEntry = ConfigEntry[IntegrationBlueprintData]


@dataclass
class IntegrationBlueprintData:
    """Data for ha_integration_domain."""

    client: IntegrationBlueprintApiClient
    coordinator: IntegrationBlueprintDataUpdateCoordinator
    integration: Integration
