from enterprise_ai.core.config import Settings


def test_settings_use_default_values() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "Enterprise AI Knowledge Platform"
    assert settings.app_env == "development"
    assert settings.debug is False


def test_settings_can_be_overridden_by_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DEBUG", "true")

    settings = Settings(_env_file=None)

    assert settings.app_env == "testing"
    assert settings.debug is True
