from xpublish_config.load_from_file import load_from_file


def test_load_yaml(snapshot):
    path = "./tests/test_config.yaml"

    config = load_from_file(path)

    assert config["register_plugins"] == {
        "test_local": "a_local_plugin:TestLocalPlugin",
        "gfs_datasets": "xpublish_intake_provider:IntakeDatasetProviderPlugin",
    }

    assert config == snapshot
