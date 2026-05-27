"""Service layer for supported device models."""
from app.core.cache import ttl_cache
from app.repositories.supported_models import SupportedModelRepository


_SUPPORTED_MODELS_TTL_SECONDS = 300


class SupportedModelService:
    """Business logic for supported model queries."""

    @staticmethod
    def list_models() -> list[dict]:
        cache_key = "supported_models:list"
        cached = ttl_cache.get(cache_key)
        if cached is not None:
            return cached
        models = SupportedModelRepository.list_models()
        ttl_cache.set(cache_key, models, _SUPPORTED_MODELS_TTL_SECONDS)
        return models
