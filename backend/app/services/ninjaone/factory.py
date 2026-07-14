from app.config import Settings, settings as default_settings
from app.services.ninjaone.base import NinjaOneProvider
from app.services.ninjaone.live_provider import LiveNinjaOneProvider
from app.services.ninjaone.mock_provider import MockNinjaOneProvider


def get_ninjaone_provider(settings: Settings = default_settings) -> NinjaOneProvider:
    if settings.ninjaone_mode == "live":
        return LiveNinjaOneProvider(settings)
    return MockNinjaOneProvider()
