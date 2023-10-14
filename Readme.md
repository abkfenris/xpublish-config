# Xpublish-config

Xpublish-config helps to standardize how Xpublish based servers dynamically manage configuration handling.



## CLI

```sh
python -m xpublish_config generate [yaml,json,toml,md] -f <input_config_path> <output_path>
```

Generate an initial config file in YAML, JSON, or TOML, or document the config in markdown.

`-f` points to an existing YAML, JSON, or TOML config which will be used to find included and excluded plugins.

```sh
python -m xpublish_config parse -f <input_config_path>
```

Pretty prints the fully parsed config or shows validation errors.
