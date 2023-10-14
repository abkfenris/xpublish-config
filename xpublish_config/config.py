import importlib

from typing import Dict, List, Optional, Union
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
)
from pydantic import create_model, BaseModel, Field

from xpublish.plugins import find_default_plugins

from xpublish_config.load_from_file import load_from_file
from xpublish_config.merge_configs import merge


class XpublishPluginSettings(BaseSettings):
    """Settings class for managing what plugins are loaded,
    before loading and validating plugin configs."""

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
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Make environment variables, dotenv, or file secret setting sources
        override directly passed in or config file sources"""
        return env_settings, dotenv_settings, file_secret_settings, init_settings


class XpublishBaseSettings(XpublishPluginSettings):
    model_config = SettingsConfigDict(env_prefix="xpublish_", extra="forbid")


class RestSettings(BaseModel):
    # datasets: dict = Field(default_factory=dict)
    # routers:
    cache_kws: dict = Field(default_factory=dict)
    app_kws: dict = Field(default_factory=dict)


class ServeSettings(BaseModel):
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=9000)
    log_level: str = Field(default="info")
    debug: bool = Field(default=False)
    reload: bool = Field(default=False)


class XpublishServingSettings(XpublishBaseSettings):
    rest: RestSettings = Field(default_factory=RestSettings)
    serve: ServeSettings = Field(default_factory=ServeSettings)

    def rest_kwargs(self):
        kwargs = self.rest.dict()
        try:
            kwargs["plugins"] = self.plugins.__dict__
        except AttributeError:
            pass
        return kwargs


class XpublishConfigManager:
    def __init__(self, settings_class: Optional[XpublishBaseSettings] = None) -> None:
        if not settings_class:
            self.settings_class = XpublishServingSettings
        else:
            self.settings_class = settings_class

    def merged_config(
        self,
        initial_config: Optional[dict] = None,
        from_file: Optional[Union[str, Path]] = None,
    ) -> dict:
        """Merge a directly passed in config into the file config,
        so the config values coming from the file take precedence."""
        config = initial_config or {}

        if from_file:
            file_config = load_from_file(from_file)
            config = merge(config, file_config)

        return config

    def build_dynamic_settings(
        self,
        initial_config: Optional[dict] = None,
        from_file: Optional[Union[str, Path]] = None,
    ):
        """Using the settings class, the included and excluded plugins
        return a settings class with plugins
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
            **{
                key: (value, Field(default_factory=value))
                for key, value in plugins.items()
            },
        )

        class XpublishDynamicSettings(self.settings_class):
            plugins: PluginModel = Field(default_factory=PluginModel)

        return XpublishDynamicSettings

    def parse(
        self,
        initial_config: Optional[dict] = None,
        from_file: Optional[Union[str, Path]] = None,
    ):
        """Return a fully configured settings class"""

        settings_class = self.build_dynamic_settings(initial_config, from_file)
        config = self.merged_config(initial_config, from_file)

        settings = settings_class(**config)

        return settings
