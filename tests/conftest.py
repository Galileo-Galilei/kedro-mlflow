import os
from pathlib import Path
from typing import Dict

import mlflow
import pytest
import yaml


@pytest.fixture(autouse=True)
def cleanup_mlflow_after_runs():
    # A test function will be run at this point
    yield
    while mlflow.active_run():
        mlflow.end_run()


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
        "root": {"level": "ERROR", "handlers": ["console"]},
        "loggers": {
            "kedro": {"level": "ERROR", "handlers": ["console"], "propagate": False}
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            }
        },
        "info_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
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
        globals_yaml = tmp_path / "conf" / env / "globals.yml"
        kedro_yaml = tmp_path / ".kedro.yml"
        _write_yaml(catalog, dict())
        _write_yaml(parameters, dict())
        _write_yaml(globals_yaml, dict())
        _write_yaml(credentials, dict())
        _write_yaml(logging, _get_local_logging_config()),

    _write_yaml(
        kedro_yaml,
        dict(
            {
                "context_path": "dummy_package.run.ProjectContext",
                "project_name": "dummy_package",
                "project_version": "0.16.5",
                "package_name": "dummy_package",
            }
        ),
    )

    os.mkdir(tmp_path / "src")
    os.mkdir(tmp_path / "src" / "dummy_package")
    with open(tmp_path / "src" / "dummy_package" / "run.py", "w") as f:
        f.writelines(
            [
                "from kedro.framework.context import KedroContext\n",
                "from kedro.config import TemplatedConfigLoader \n"
                "class ProjectContext(KedroContext):\n",
                "    project_name = 'dummy_package'\n",
                "    project_version = '0.16.5'\n",
                "    package_name = 'dummy_package'\n",
            ]
        )
        f.writelines(
            [
                "    def _create_config_loader(self, conf_paths):\n",
                "        return TemplatedConfigLoader(\n",
                "        conf_paths,\n",
                "        globals_pattern='globals.yml'\n",
                "        )\n",
            ]
        )
