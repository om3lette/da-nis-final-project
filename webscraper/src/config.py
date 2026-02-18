from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict, YamlConfigSettingsSource

from constants import CONFIG_PATH
from logger import setup_logger


class Config(BaseSettings):
    max_concurrent_tasks: int = Field(default=5)
    force_timestamps_refetch: bool = Field(default=False)
    dev_mode: bool = Field(default=False)

    model_config = SettingsConfigDict(
        yaml_file=CONFIG_PATH,
        extra="forbid"
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple:
        return (
            YamlConfigSettingsSource(settings_cls),
        )

    @staticmethod
    def ensure_config_file() -> Config:
        if CONFIG_PATH.exists():
            return Config()

        setup_logger(__name__).warning("No config file found. Using default values")
        config: Config = Config()

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config.model_dump(), f)

        return config
