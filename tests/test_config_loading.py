from xpublish_config import XpublishConfigManager


def test_load_settings_from_yaml_file(snapshot):
    settings = XpublishConfigManager().parse(from_file="./tests/test_config.yaml")

    assert settings.disabled_plugins == ["cf_edr"]
    assert settings.register_plugins == {
        "test_local": "a_local_plugin:TestLocalPlugin",
        "gfs_datasets": "xpublish_intake_provider:IntakeDatasetProviderPlugin",
    }

    assert settings.rest.cache_kws == {}
    assert settings.rest.app_kws == {}

    assert settings.serve.host == "0.0.0.0"
    assert settings.serve.port == 9000
    assert settings.serve.log_level == "info"
    assert settings.serve.debug is False
    assert settings.serve.reload is False

    assert settings.model_dump() == snapshot


def test_load_settings_from_json_file(snapshot):
    settings = XpublishConfigManager().parse(from_file="./tests/test_config.json")

    assert settings.disabled_plugins == ["cf_edr"]
    assert settings.register_plugins == {
        "test_local": "a_local_plugin:TestLocalPlugin",
        "gfs_datasets": "xpublish_intake_provider:IntakeDatasetProviderPlugin",
    }

    assert settings.rest.cache_kws == {}
    assert settings.rest.app_kws == {}

    assert settings.serve.host == "0.0.0.0"
    assert settings.serve.port == 9000
    assert settings.serve.log_level == "info"
    assert settings.serve.debug is False
    assert settings.serve.reload is False

    assert settings.model_dump() == snapshot


def test_load_settings_from_toml_file(snapshot):
    settings = XpublishConfigManager().parse(from_file="./tests/test_config.toml")

    assert settings.disabled_plugins == ["cf_edr"]
    assert settings.register_plugins == {
        "test_local": "a_local_plugin:TestLocalPlugin",
        "gfs_datasets": "xpublish_intake_provider:IntakeDatasetProviderPlugin",
    }

    assert settings.rest.cache_kws == {}
    assert settings.rest.app_kws == {}

    assert settings.serve.host == "0.0.0.0"
    assert settings.serve.port == 9000
    assert settings.serve.log_level == "info"
    assert settings.serve.debug is False
    assert settings.serve.reload is False

    assert settings.model_dump() == snapshot


def test_disable_plugins_with_environment_variables(monkeypatch, snapshot):
    monkeypatch.setenv("XPUBLISH_DISABLED_PLUGINS", '["zarr"]')

    settings = XpublishConfigManager().parse(from_file="./tests/test_config.yaml")

    assert settings.disabled_plugins == ["zarr"]
    assert settings.register_plugins == {
        "test_local": "a_local_plugin:TestLocalPlugin",
        "gfs_datasets": "xpublish_intake_provider:IntakeDatasetProviderPlugin",
    }

    assert settings.rest.cache_kws == {}
    assert settings.rest.app_kws == {}

    assert settings.serve.host == "0.0.0.0"
    assert settings.serve.port == 9000
    assert settings.serve.log_level == "info"
    assert settings.serve.debug is False
    assert settings.serve.reload is False

    assert settings.model_dump() == snapshot


def test_load_settings_from_dict(snapshot):
    dict_config = {
        "register_plugins": {
            "test_local": "a_local_plugin:TestLocalPlugin",
            "gfs_datasets": "xpublish_intake_provider:IntakeDatasetProviderPlugin",
        },
        "plugins": {
            "opendap": {"dataset_router_prefix": "/opendap"},
            "test_local": {"invalid_config": True},  # doesn't error but gets ignored
            "gfs_datasets": {
                "uri": "https://raw.githubusercontent.com/axiom-data-science/mc-goods/main/mc_goods/gfs-1-4deg.yaml",
            },
        },
    }
    
    settings = XpublishConfigManager().parse(initial_config=dict_config)

    assert settings.disabled_plugins == []
    assert settings.register_plugins == {
        "test_local": "a_local_plugin:TestLocalPlugin",
        "gfs_datasets": "xpublish_intake_provider:IntakeDatasetProviderPlugin",
    }

    assert settings.rest.cache_kws == {}
    assert settings.rest.app_kws == {}

    assert settings.serve.host == "0.0.0.0"
    assert settings.serve.port == 9000
    assert settings.serve.log_level == "info"
    assert settings.serve.debug is False
    assert settings.serve.reload is False

    assert settings.model_dump() == snapshot


def test_load_merge_configs(snapshot):
    dict_config = {
        "register_plugins": {
            "dbofs_datasets": "xpublish_intake_provider:IntakeDatasetProviderPlugin",
        },
        "plugins": {
            "opendap": {"dataset_router_prefix": "/dap"},  # should be overriden by file
            "dbofs_datasets": {
                "uri": "https://raw.githubusercontent.com/axiom-data-science/mc-goods/main/mc_goods/dbofs.yaml",
            },
        },
    }
    

    settings = XpublishConfigManager().parse(from_file="./tests/test_config.json")

    assert settings.disabled_plugins == ["cf_edr"]
    assert settings.register_plugins == {
        "test_local": "a_local_plugin:TestLocalPlugin",
        "gfs_datasets": "xpublish_intake_provider:IntakeDatasetProviderPlugin",
        "dbofs_datasets": "xpublish_intake_provider:IntakeDatasetProviderPlugin",
    }

    assert settings.rest.cache_kws == {}
    assert settings.rest.app_kws == {}

    assert settings.serve.host == "0.0.0.0"
    assert settings.serve.port == 9000
    assert settings.serve.log_level == "info"
    assert settings.serve.debug is False
    assert settings.serve.reload is False

    assert settings.model_dump() == snapshot