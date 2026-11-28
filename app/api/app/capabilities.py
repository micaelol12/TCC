"""Describe analysis modes and Lab options without calling providers."""

from .analysis_defaults import configured_scales
from .experiment_config import CONFIG_VERSION, config_ranges
from .lab_credentials import model_catalog
from .settings import Settings


def build_capabilities(settings: Settings, provider_keys: dict[str, str]) -> dict:
    """Descreve limites e modos disponíveis a partir das chaves, sem consultar provedores."""
    defaults = settings.algorithm_defaults()
    model_providers = model_catalog(settings)
    jev_available = bool(provider_keys["typesafe"])
    llm_available = (
        bool(provider_keys["maritaca"] or provider_keys["gemini"])
        if settings.app_env == "lab"
        else bool(provider_keys[model_providers[defaults.llm_model]])
    )
    high_available = llm_available and (
        jev_available or not defaults.semantic_evidence_check or settings.app_env == "lab"
    )
    capabilities = {
        "max_chars": settings.max_chars,
        "max_tokens": settings.max_tokens,
        "max_chunks": settings.max_chunks,
        "modes": {"low": jev_available, "medium": jev_available and llm_available, "high": high_available},
        "timeout_seconds": settings.timeout_seconds,
        "analysis_defaults": defaults.model_dump(mode="json"),
        "model_providers": model_providers,
        "environment": settings.app_env,
        "experimental": {"enabled": settings.experimental_config_enabled},
    }

    if settings.experimental_config_enabled:
        capabilities["experimental"].update(
            build_experimental_capabilities(settings, provider_keys, model_providers)
        )

    return capabilities


def build_experimental_capabilities(
    settings: Settings, provider_keys: dict[str, str], model_providers: dict[str, str]
) -> dict:
    """Expõe opções do Lab e prioriza um modelo cujo provedor tenha chave na sessão."""
    defaults = settings.algorithm_defaults().model_dump()

    if not provider_keys[model_providers[defaults["llm_model"]]]:
        defaults["llm_model"] = next(
            (model for model, provider in model_providers.items() if provider_keys[provider]),
            defaults["llm_model"],
        )

    return {
        "config_version": CONFIG_VERSION,
        "defaults": defaults,
        "ranges": config_ranges(settings.max_tokens, settings.max_chunks),
        "allowed_models": {"jev": list(settings.allowed_jev_models), "llm": list(model_providers)},
        "model_providers": model_providers,
        "providers": {provider: bool(key) for provider, key in provider_keys.items()},
        "execution_storage": True,
        "scales": [scale.model_dump(mode="json") for scale in configured_scales(settings.escala)],
    }
