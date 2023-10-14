"""Load a configuration from YAML, TOML, or JSON."""
from pathlib import Path
from typing import Union


def load_from_file(file_path: Union[Path, str]) -> dict:
    """Load a configuration from YAML, TOML, or JSON."""
    if isinstance(file_path, str):
        file_path = Path(file_path)

    if file_path.suffix in [".yml", ".yaml"]:
        import ruamel.yaml

        with file_path.open() as f:
            yaml = ruamel.yaml.YAML(typ="safe", pure=True).load(f)
            return yaml

    if file_path.suffix in [".toml"]:
        import tomlkit

        with file_path.open() as f:
            return tomlkit.load(f).unwrap()

    import json

    with file_path.open() as f:
        return json.load(f)
