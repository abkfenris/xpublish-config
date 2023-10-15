"""Dynamically generate Xpublish configs based on active plugins."""
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, create_model
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from xpublish.plugins import find_default_plugins

from xpublish_config.load_from_file import load_from_file
from xpublish_config.merge_configs import merge


class XpublishPluginSettings(BaseSettings):
    """Settings class for managing what plugins are loaded.

    Allows controlling which plugins are loaded or not before
    they are used for validating the full configuration.
    """

    disabled_plugins: List[str] = Field(
        default_factory=list,
        description=(
            "A list of plugins to disable. "
            "The name is what it would normally be automatically loaded as."
        ),
    )
    register_plugins: Dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Name and import path of plugins that are not automatically loaded. "
            "These plugins will be explicitly loaded and initialized."
        ),
    )

    model_config = SettingsConfigDict(env_prefix="xpublish_", extra="ignore")

    @classmethod
    def settings_customise_sources(  # noqa:PLR0913
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Configure order of priority.

        Environment variables should be most important,
        then dotenv, followed by secret files, and finally
        the directly passed in configuration.
        """
        return env_settings, dotenv_settings, file_secret_settings, init_settings


class XpublishBaseSettings(XpublishPluginSettings):
    """Disable allowing extra arguments for downstream classes."""

    model_config = SettingsConfigDict(env_prefix="xpublish_", extra="forbid")


class RestSettings(BaseModel):
    """Arguments to pass to xpublish.Rest."""

    # datasets: dict = Field(default_factory=dict)
    # routers:
    cache_kws: dict = Field(default_factory=dict)
    app_kws: dict = Field(default_factory=dict)


class XpublishRestSettings(XpublishBaseSettings):
    """Configure xpublish.Rest."""

    rest: RestSettings = Field(default_factory=RestSettings)

    def rest_kwargs(self) -> dict:
        """Keyword arguments for Xpublish.Rest()."""
        kwargs = self.rest.model_dump()
        try:
            kwargs["plugins"] = self.plugins.__dict__
        except AttributeError:
            pass
        return kwargs

    def to_rest(self):
        """Instantiate xpublish.Rest."""
        from xpublish import Rest

        kwargs = self.rest_kwargs()

        return Rest(**kwargs)


class ServeSettings(BaseModel):
    """Arguments to pass to uvicorn.run or similar servers."""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=9000)
    log_level: str = Field(default="info")
    debug: bool = Field(default=False)
    reload: bool = Field(default=False)


class XpublishServingSettings(XpublishRestSettings):
    """Configure uvicorn.run and other servers for Xpublish."""

    serve: ServeSettings = Field(default_factory=ServeSettings)

    def serve_kwargs(self) -> dict:
        """Keyword arguments for uvicorn.run."""
        kwargs = self.serve.model_dump()

        return kwargs

    unicorn_run_kwargs = serve_kwargs


class XpublishConfigManager:
    """Generate Xpublish settings classes and example configurations."""

    def __init__(self, settings_class: Optional[XpublishBaseSettings] = None) -> None:
        """Set a default settings class to build dynamic settings on top of."""
        if not settings_class:
            self.settings_class = XpublishServingSettings
        else:
            self.settings_class = settings_class

    def merged_config(
        self,
        initial_config: Optional[dict] = None,
        from_file: Optional[Union[str, Path]] = None,
    ) -> dict:
        """Merge a directly passed in config into the file config.

        The config values from the file should take precedence.
        """
        config = initial_config or {}

        if from_file:
            file_config = load_from_file(from_file)
            config = merge(file_config, config)

        return config

    def build_dynamic_settings(
        self,
        initial_config: Optional[dict] = None,
        from_file: Optional[Union[str, Path]] = None,
    ):
        """Creates a settings class based on loaded plugins.

        Uses the underlying default settings class, and
        the registered and disabled plugins from the
        directly loaded, file, and environment variable configs
        to create a settings class that can load an validate plugins.
        """
        config = self.merged_config(initial_config, from_file)

        plugin_settings = XpublishPluginSettings(**config)

        plugins = find_default_plugins(plugin_settings.disabled_plugins)

        for name, plugin_import_path in plugin_settings.register_plugins.items():
            try:
                lib_path, plugin_class_name = plugin_import_path.split(":")
            except ValueError as e:
                raise ValueError(
                    f"Unable to build import path `{plugin_import_path}` when "
                    f"attempting to load `register_plugins.{name}. "
                    "Is there a `:` missing?",
                ) from e

            plugin_lib = importlib.import_module(lib_path)

            try:
                plugin_class = getattr(plugin_lib, plugin_class_name)
            except AttributeError as e:
                raise AttributeError(
                    f"{lib_path} doesn't appear to have have {plugin_class_name}. "
                    f"Maybe you meant one of these instead:\n{dir(plugin_lib)}",
                ) from e

            plugins[name] = plugin_class

        PluginModel = create_model(
            "PluginModel",
            **{key: (value, Field(default_factory=value)) for key, value in plugins.items()},
        )

        class XpublishDynamicSettings(self.settings_class):
            plugins: PluginModel = Field(default_factory=PluginModel)

        return XpublishDynamicSettings

    def parse(
        self,
        initial_config: Optional[dict] = None,
        from_file: Optional[Union[str, Path]] = None,
    ):
        """Return a fully configured settings class."""
        settings_class = self.build_dynamic_settings(initial_config, from_file)
        config = self.merged_config(initial_config, from_file)

        settings = settings_class(**config)

        return settings
