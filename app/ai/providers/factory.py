import logging

from app.ai.providers.base import SignGenerationProvider
from app.ai.providers.flux import FluxLocalProvider


logger = logging.getLogger(__name__)
_provider: SignGenerationProvider = FluxLocalProvider()
logger.info("Using signature provider: %s", _provider.name)


def get_sign_provider() -> SignGenerationProvider:
    return _provider
