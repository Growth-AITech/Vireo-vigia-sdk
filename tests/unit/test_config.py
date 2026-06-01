"""Unit tests for VireoSettings configuration."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from vireo_vigia.config import VireoSettings, load_settings
from vireo_vigia.exceptions import ConfigurationError


class TestVireoSettings:
    def test_loads_with_required_keys(self) -> None:
        settings = VireoSettings(
            anthropic_api_key="sk-ant-test",  # type: ignore[arg-type]
        )
        assert settings.llm_model == "claude-sonnet-4-5"
        assert settings.environment == "development"
        assert settings.hl_network == "mainnet"

    def test_default_qdrant_url(self) -> None:
        settings = VireoSettings(
            anthropic_api_key="sk-ant-test",  # type: ignore[arg-type]
        )
        assert settings.qdrant_url == "http://localhost:6333"

    def test_secrets_not_leaked_in_repr(self) -> None:
        settings = VireoSettings(
            anthropic_api_key="sk-ant-supersecret",  # type: ignore[arg-type]
        )
        # SecretStr masks value in repr
        assert "supersecret" not in repr(settings)

    def test_blank_anthropic_key_raises(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            VireoSettings(
                anthropic_api_key="",  # type: ignore[arg-type]
            )
        assert "ANTHROPIC" in str(exc_info.value).upper()

    def test_openai_key_is_optional(self) -> None:
        # OpenAI key is optional — settings loads fine without explicitly providing it
        settings = VireoSettings(
            anthropic_api_key="sk-ant-test",  # type: ignore[arg-type]
        )
        # openai_api_key may be set from env/conftest — that is fine; the point
        # is that VireoSettings no longer requires it to be present.
        assert settings.embedding_provider == "local"

    def test_both_blank_keys_raises(self) -> None:
        # Only Anthropic key is required now
        with pytest.raises(ConfigurationError) as exc_info:
            VireoSettings(
                anthropic_api_key="",  # type: ignore[arg-type]
            )
        assert "ANTHROPIC" in str(exc_info.value).upper()

    def test_load_settings_uses_env(self) -> None:
        # conftest fixture injects VIREO_* env vars
        settings = load_settings()
        assert settings.anthropic_api_key.get_secret_value() == "test-anthropic-key"


class TestSettingsValidation:
    def test_invalid_log_level_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VireoSettings(
                anthropic_api_key="sk-ant-test",  # type: ignore[arg-type]
                log_level="VERBOSE",  # type: ignore[arg-type]
            )

    def test_invalid_network_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VireoSettings(
                anthropic_api_key="sk-ant-test",  # type: ignore[arg-type]
                hl_network="devnet",  # type: ignore[arg-type]
            )

    def test_max_tokens_upper_bound(self) -> None:
        with pytest.raises(ValidationError):
            VireoSettings(
                anthropic_api_key="sk-ant-test",  # type: ignore[arg-type]
                llm_max_tokens=99999,
            )
