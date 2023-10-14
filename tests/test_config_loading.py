from xpublish_config import XpublishConfigManager

def test_load_settings_from_file(snapshot):
    settings = XpublishConfigManager().parse(from_file="./tests/test_config.yaml")

    assert settings.disabled_plugins == []
    assert settings.register_plugins == {
        "test_local": "a_local_plugin:TestLocalPlugin", 
        'gfs_datasets': 'xpublish_intake_provider:IntakeDatasetProviderPlugin'
    }

    assert settings.rest.cache_kws == {}
    assert settings.rest.app_kws == {}

    assert settings.serve.host == '0.0.0.0'
    assert settings.serve.port == 9000
    assert settings.serve.log_level == 'info'
    assert settings.serve.debug == False
    assert settings.serve.reload == False

    assert settings == snapshot


def test_disable_plugins_with_environment_variables(monkeypatch, snapshot):
    monkeypatch.setenv("XPUBLISH_DISABLED_PLUGINS", '["zarr"]')

    settings = XpublishConfigManager().parse(from_file="./tests/test_config.yaml")

    assert settings.disabled_plugins == ["zarr"]
    assert settings.register_plugins == {
        "test_local": "a_local_plugin:TestLocalPlugin", 
        'gfs_datasets': 'xpublish_intake_provider:IntakeDatasetProviderPlugin'
    }

    assert settings.rest.cache_kws == {}
    assert settings.rest.app_kws == {}

    assert settings.serve.host == '0.0.0.0'
    assert settings.serve.port == 9000
    assert settings.serve.log_level == 'info'
    assert settings.serve.debug == False
    assert settings.serve.reload == False

    assert settings == snapshot
