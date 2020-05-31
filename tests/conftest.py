from pathlib import Path
from typing import Dict

import pytest
import yaml


def _write_yaml(filepath: Path, config: Dict):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    yaml_str = yaml.dump(config)
    filepath.write_text(yaml_str)


def _get_local_logging_config():
    return {
        "version": 1,
        "formatters": {
            "simple": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
        },
        "root": {"level": "INFO", "handlers": ["console"]},
        "loggers": {
            "kedro": {"level": "INFO", "handlers": ["console"], "propagate": False}
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            }
        },
        "info_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": "logs/info.log",
        },
    }


@pytest.fixture
def config_dir(tmp_path):
    """This emulates the root of a kedro project.
    This function must be called before any instantiation of DummyContext

    """
    for env in ["base", "local"]:
        catalog = tmp_path / "conf" / env / "catalog.yml"
        credentials = tmp_path / "conf" / env / "credentials.yml"
        logging = tmp_path / "conf" / env / "logging.yml"
        parameters = tmp_path / "conf" / env / "parameters.yml"
        _write_yaml(catalog, dict())
        _write_yaml(parameters, dict())
        _write_yaml(credentials, dict())
        _write_yaml(logging, _get_local_logging_config())
