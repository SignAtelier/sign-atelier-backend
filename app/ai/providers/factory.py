import logging

from app.ai.providers.base import SignGenerationProvider
from app.ai.providers.flux_local import FluxLocalProvider


logger = logging.getLogger(__name__)
_provider: SignGenerationProvider | None = None


def get_sign_provider() -> SignGenerationProvider:
    global _provider

    if _provider is not None:
        return _provider

    _provider = FluxLocalProvider()

    logger.info("Using signature provider: %s", _provider.name)
    return _provider
