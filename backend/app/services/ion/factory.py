from app.config import Settings, settings as default_settings
from app.services.ion.base import IonProvider
from app.services.ion.live_provider import LiveIonProvider
from app.services.ion.mock_provider import MockIonProvider


def get_ion_provider(settings: Settings = default_settings) -> IonProvider:
    if settings.ion_mode == "live":
        return LiveIonProvider(settings)
    return MockIonProvider()
