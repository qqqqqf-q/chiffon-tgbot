"""Configuration loader for the Telegram bot project."""
from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict

import yaml


_CONFIG_DIR = Path(__file__).resolve().parent


class ConfigNamespace(SimpleNamespace):
    """Namespace wrapper that keeps attribute-style access for dict data."""

    def to_dict(self) -> Dict[str, Any]:
        return _namespace_to_dict(self)


def _namespace_to_dict(ns: Any) -> Any:
    if isinstance(ns, ConfigNamespace):
        return {key: _namespace_to_dict(getattr(ns, key)) for key in ns.__dict__}
    if isinstance(ns, list):
        return [_namespace_to_dict(item) for item in ns]
    return ns


def _expand_env(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_key = value[2:-1]
        return os.getenv(env_key, "")
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    return value


def _dict_to_namespace(data: Any) -> Any:
    if isinstance(data, dict):
        return ConfigNamespace(**{key: _dict_to_namespace(value) for key, value in data.items()})
    if isinstance(data, list):
        return [_dict_to_namespace(item) for item in data]
    return data


def _load_yaml_file(filename: str) -> ConfigNamespace:
    path = _CONFIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing configuration file: {path}")

    with path.open("r", encoding="utf-8") as config_file:
        data = yaml.safe_load(config_file) or {}

    return _dict_to_namespace(_expand_env(data))


def load_runtime_db_path() -> Path:
    """Expose the runtime DB path stored next to the configs."""
    return _CONFIG_DIR / "config_runtime.db"


config_logger = _load_yaml_file("config_logger.yaml")
config_database = _load_yaml_file("config_database.yaml")
config_secret = _load_yaml_file("config_secret.yaml")

__all__ = [
    "ConfigNamespace",
    "config_logger",
    "config_database",
    "config_secret",
    "load_runtime_db_path",
]
