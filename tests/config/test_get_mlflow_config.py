import json
from pathlib import Path

import pytest
import toml
import yaml
from dynaconf.validator import Validator
from kedro import __version__ as kedro_version
from kedro.config import TemplatedConfigLoader
from kedro.framework.project import _IsSubclassValidator, _ProjectSettings
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

from kedro_mlflow.config.kedro_mlflow_config import KedroMlflowConfigError


def _write_yaml(filepath, config):
    yaml_str = yaml.dump(config)
    filepath.write_text(yaml_str)


# TODO : reenable this test which is currently failing beacause kedro "import settings"
# is completetly messing up because we have several projects
# and the first import wins


def test_mlflow_config_default(kedro_project):
    # kedro_project is a pytest.fixture in conftest
    dict_config = dict(
        server=dict(
            mlflow_tracking_uri="mlruns",
            credentials=None,
        ),
        tracking=dict(
            disable_tracking=dict(pipelines=["my_disabled_pipeline"]),
            experiment=dict(name="fake_package", restore_if_deleted=True),
            run=dict(id="123456789", name="my_run", nested=True),
            params=dict(
                dict_params=dict(
                    flatten=True,
                    recursive=False,
                    sep="-",
                ),
                long_params_strategy="truncate",
            ),
        ),
        ui=dict(port="5151", host="localhost"),
    )

    _write_yaml(kedro_project / "conf" / "local" / "mlflow.yml", dict_config)
    expected = dict_config.copy()
    expected["server"]["mlflow_tracking_uri"] = (kedro_project / "mlruns").as_uri()

    bootstrap_project(kedro_project)
    with KedroSession.create(project_path=kedro_project) as session:
        context = session.load_context()
        assert context.mlflow.dict(exclude={"project_path"}) == expected


def test_mlflow_config_in_uninitialized_project(kedro_project):
    # config_with_base_mlflow_conf is a pytest.fixture in conftest
    with pytest.raises(
        KedroMlflowConfigError, match="No 'mlflow.yml' config file found in environment"
    ):
        bootstrap_project(kedro_project)
        with KedroSession.create(project_path=kedro_project) as session:
            session.load_context()


@pytest.fixture(autouse=True)
def mock_validate_settings(mocker):
    # KedroSession eagerly validates that a project's settings.py is correct by
    # importing it. settings.py does not actually exists as part of this test suite
    # since we are testing session in isolation, so the validation is patched.
    mocker.patch("kedro.framework.session.session.validate_settings")


def _mock_imported_settings_paths(mocker, mock_settings):
    for path in [
        "kedro.framework.project.settings",
        "kedro.framework.session.session.settings",
    ]:
        mocker.patch(path, mock_settings)
    return mock_settings


@pytest.fixture
def mock_settings_templated_config_loader_class(mocker):
    class MockSettings(_ProjectSettings):
        _CONFIG_LOADER_CLASS = _IsSubclassValidator(
            "CONFIG_LOADER_CLASS", default=lambda *_: TemplatedConfigLoader
        )

        _CONFIG_LOADER_ARGS = Validator(
            "CONFIG_LOADER_ARGS", default=dict(globals_pattern="*globals.yml")
        )

    return _mock_imported_settings_paths(mocker, MockSettings())


@pytest.fixture
def local_logging_config():
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
def fake_project(tmp_path, local_logging_config):
    fake_project_dir = Path(tmp_path) / "fake_project"
    (fake_project_dir / "src").mkdir(parents=True)

    pyproject_toml_path = fake_project_dir / "pyproject.toml"
    payload = {
        "tool": {
            "kedro": {
                "project_version": kedro_version,
                "project_name": "fake_project",
                "package_name": "fake_package",
            }
        }
    }
    toml_str = toml.dumps(payload)
    pyproject_toml_path.write_text(toml_str, encoding="utf-8")

    env_logging = fake_project_dir / "conf" / "base" / "logging.yml"
    env_logging.parent.mkdir(parents=True)
    env_logging.write_text(json.dumps(local_logging_config), encoding="utf-8")
    (fake_project_dir / "conf" / "local").mkdir()
    return fake_project_dir


@pytest.mark.usefixtures("mock_settings_templated_config_loader_class")
def test_mlflow_config_with_templated_config_loader(fake_project):
    dict_config = dict(
        server=dict(
            mlflow_tracking_uri="${mlflow_tracking_uri}",
            credentials=None,
        ),
        tracking=dict(
            disable_tracking=dict(pipelines=["my_disabled_pipeline"]),
            experiment=dict(name="fake_package", restore_if_deleted=True),
            run=dict(id="123456789", name="my_run", nested=True),
            params=dict(
                dict_params=dict(
                    flatten=True,
                    recursive=False,
                    sep="-",
                ),
                long_params_strategy="truncate",
            ),
        ),
        ui=dict(port="5151", host="localhost"),
    )

    _write_yaml(fake_project / "conf" / "local" / "mlflow.yml", dict_config)

    _write_yaml(
        fake_project / "conf" / "local" / "globals.yml",
        dict(mlflow_tracking_uri="dynamic_mlruns"),
    )

    expected = dict_config.copy()
    expected["server"]["mlflow_tracking_uri"] = (
        fake_project / "dynamic_mlruns"
    ).as_uri()

    bootstrap_project(fake_project)
    with KedroSession.create("fake_package", fake_project) as session:
        context = session.load_context()
        assert context.mlflow.dict(exclude={"project_path"}) == expected
