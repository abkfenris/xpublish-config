import importlib

from typing import Dict, List, Optional, Union
from pathlib import Path

from goodconf import GoodConf, Field
from pydantic import create_model, Extra, BaseModel

from xpublish.plugins import find_default_plugins

class XpublishPluginSettings(GoodConf):
    disabled_plugins: List[str] = Field(
        default_factory=list, 
        description=(
            "A list of plugins to disable. "
            "The name is what it would normally be automatically loaded as."
        )
    )
    register_plugins: Dict[str, str] = Field(default_factory=list)

    class Config:
        env_prefix = "xpublish_"
        extra=Extra.ignore
        # env_nested_delimiter = '__'

class XpublishBaseSettings(XpublishPluginSettings, extra=Extra.forbid):
    pass


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
            kwargs['plugins'] = self.plugins.__dict__
        except AttributeError:
            pass
        return kwargs


class XpublishConfigManager:
    def __init__(self, settings_class: Optional[XpublishBaseSettings] = None) -> None:
        if not settings_class:
            self.settings_class = XpublishServingSettings
        else:
            self.settings_class = settings_class

    def build_dynamic_settings(self, 
                               config: Optional[dict] = None, 
                               from_file: Optional[Union[str, Path]] = None):
        """Using the settings class, the included and excluded plugins
        return a settings class with plugins
        """
        plugin_settings = XpublishPluginSettings()
        plugin_settings.load(from_file)

        if config:
            plugin_settings = plugin_settings.copy(update=config)

        plugins = find_default_plugins(plugin_settings.disabled_plugins)

        for name, plugin_import_path in plugin_settings.register_plugins.items():
            try:
                lib_path, plugin_class_name = plugin_import_path.split(":")
            except ValueError as e:
                raise ValueError(f"Unable to build import path `{plugin_import_path}` when attempting to load `register_plugins.{name}. Is there a `:` missing?") from e
            
            plugin_lib = importlib.import_module(lib_path)

            try:
                plugin_class = getattr(plugin_lib, plugin_class_name)
            except AttributeError as e:
                raise AttributeError(f"{lib_path} doesn't appear to have have {plugin_class_name}. Maybe you meant one of these instead:\n{dir(plugin_lib)}") from e
        
            plugins[name] = plugin_class


        PluginModel = create_model(
            "PluginModel", 
            **{
                key: (value, Field(default_factory=value)) 
                for key, value in plugins.items()
                })

        class XpublishDynamicSettings(self.settings_class):
            plugins: PluginModel = Field(default_factory=PluginModel)

        return XpublishDynamicSettings

    def generate(self, type: str, config: Optional[dict] = None, from_file: Optional[Union[str, Path]] = None):
        """Create settings template files with initial config"""
        settings_class = self.build_dynamic_settings(config=config, from_file=from_file)

        if type.lower() in {"yaml", "yml"}:
            try:
                return settings_class.generate_yaml()
            except ImportError:
                raise ImportError("YAML generation requires ruamel to be installed.")
        
        if type.lower() == "json":
            return settings_class.generate_json()
        
        if type.lower() == "toml":
            try:
                return settings_class.generate_toml()
            except ImportError:
                raise ImportError("TOML generation requires tomlkit")
            
        if type.lower() in {"md", "markdown"}:
            return settings_class.generate_markdown()
        
        raise TypeError(f"{type} isn't a known type!")

    def parse(self, 
              config: Optional[dict] = None, 
              from_file: Optional[Union[str, Path]] = None
            ):
        """Return a fully configured settings class"""

        settings_class = self.build_dynamic_settings(config, from_file)
        settings = settings_class()

        settings.load(from_file)

        if config:
            settings = settings.copy(update=config)

        return settings
        

config = {
    # "disabled_plugins": ["info"]
    "register_plugins": {
        "test_local": "local_plugin:LocalPlugin"
    },
    "plugins": {
        "opendap": {
            "dataset_router_prefix": "/dap"
        }
    }
}


# print(XpublishConfigManager().generate("toml"))
# settings = XpublishConfigManager().parse(config=config)
# settings = XpublishConfigManager().parse(from_file="./test_config.yaml")

# print(settings)
# print(settings.rest_kwargs())