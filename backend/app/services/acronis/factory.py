from app.config import Settings, settings as default_settings
from app.services.acronis.base import AcronisProvider
from app.services.acronis.live_provider import LiveAcronisProvider
from app.services.acronis.mock_provider import MockAcronisProvider


def get_acronis_provider(settings: Settings = default_settings) -> AcronisProvider:
    if settings.acronis_mode == "live":
        return LiveAcronisProvider(settings)
    return MockAcronisProvider()
