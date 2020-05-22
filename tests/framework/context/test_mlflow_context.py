from pathlib import Path
from typing import Dict

import pytest
import yaml

from kedro_mlflow.framework.context import get_mlflow_conf


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


@pytest.fixture
def config_with_base_mlflow_conf(config_dir, tmp_path):
    _write_yaml(
        tmp_path / "conf" / "base" / "mlflow.yml",
        dict(
            mlflow_tracking_uri="mlruns",
            experiment=dict(name="fake_package", create=True),
            run=dict(id="123456789", name="my_run", nested=True),
            ui=dict(port="5151", host="localhost"),
        ),
    )


# def test_get_mlflow_conf_outside_kedro_project(tmp_path, config_with_base_mlflow_conf):
#     with pytest.raises(KedroMlflowConfigError, match="not a valid path to a kedro project"):
#         get_mlflow_conf(project_path=tmp_path,env="local")


def test_get_mlflow_conf(mocker, tmp_path, config_with_base_mlflow_conf):
    mocker.patch("kedro_mlflow.utils._is_kedro_project", return_value=True)
    expected = {
        "mlflow_tracking_uri": (tmp_path / "mlruns").as_uri(),
        "experiments": {"name": "fake_package", "create": True},
        "run": {"id": "123456789", "name": "my_run", "nested": True},
        "ui": {"port": "5151", "host": "localhost"},
    }
    assert get_mlflow_conf(project_path=tmp_path, env="local").to_dict() == expected
