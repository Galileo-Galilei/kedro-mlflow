from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pytest
import toml
import yaml
from kedro import __version__ as kedro_version
from kedro.config import ConfigLoader
from kedro.framework.hooks import hook_impl

# from kedro.framework.hooks.manager import get_hook_manager
from kedro.framework.project import (
    Validator,
    _ProjectPipelines,
    _ProjectSettings,
    configure_project,
)
from kedro.framework.session import KedroSession
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline, node
from mlflow.tracking import MlflowClient

from kedro_mlflow.framework.hooks import MlflowHook

MOCK_PACKAGE_NAME = "mock_package_name"


def fake_fun(input):
    artifact = input
    metrics = {
        "metric1": {"value": 1.1, "step": 1},
        "metric2": [{"value": 1.1, "step": 1}, {"value": 1.2, "step": 2}],
    }
    metric = 1
    metric_history = [0.1, 0.2, 0.3]
    model = 3
    return artifact, metrics, metric, metric_history, model


@pytest.fixture
def kedro_project_path(tmp_path):
    return tmp_path / MOCK_PACKAGE_NAME


@pytest.fixture
def local_logging_config():
    return {
        "version": 1,
        "formatters": {
            "simple": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
        },
        "root": {"level": "INFO", "handlers": ["console"]},
        "loggers": {"kedro": {"level": "INFO", "handlers": ["console"]}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            }
        },
    }


def _write_yaml(filepath: Path, config: Dict):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    yaml_str = yaml.dump(config)
    filepath.write_text(yaml_str)


def _write_toml(filepath: Path, config: Dict):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    toml_str = toml.dumps(config)
    filepath.write_text(toml_str)


@pytest.fixture
def catalog_config(kedro_project_path):
    fake_data_filepath = str(kedro_project_path / "fake_data.pkl")
    return {
        "artifact_data": {
            "type": "kedro_mlflow.io.artifacts.MlflowArtifactDataSet",
            "data_set": {
                "type": "pickle.PickleDataSet",
                "filepath": fake_data_filepath,
            },
        },
        "metrics_data": {
            "type": "kedro_mlflow.io.metrics.MlflowMetricsDataSet",
        },
        "metric_data": {
            "type": "kedro_mlflow.io.metrics.MlflowMetricDataSet",
        },
        "metric_history_data": {
            "type": "kedro_mlflow.io.metrics.MlflowMetricHistoryDataSet",
        },
        "model": {
            "type": "kedro_mlflow.io.models.MlflowModelLoggerDataSet",
            "flavor": "mlflow.sklearn",
        },
    }


@pytest.fixture
def mlflow_config_wo_tracking():
    # this is the default configuration except that oine pipeline is deactivated
    return dict(
        # "mlflow_tracking_uri": "mlruns",
        # "credentials": None,
        tracking=dict(disable_tracking=dict(pipelines=["pipeline_off"]))
        # "experiments": MOCK_PACKAGE_NAME,
        # "run": {"id": None, "name": None, "nested": True},
        # "ui": {"port": None, "host": None},
        # "hooks": {
        #     "flatten_dict_params": False,
        #     "recursive": True,
        #     "sep": ".",
        #     "long_parameters_strategy": "fail",
        # },
    )


# @pytest.fixture(autouse=True)
# def clear_hook_manager():
#     yield
#     hook_manager = get_hook_manager()
#     plugins = hook_manager.get_plugins()
#     for plugin in plugins:
#         hook_manager.unregister(plugin)


@pytest.fixture(autouse=True)
def config_dir(
    kedro_project_path, catalog_config, local_logging_config, mlflow_config_wo_tracking
):
    catalog_yml = kedro_project_path / "conf" / "base" / "catalog.yml"
    parameters_yml = kedro_project_path / "conf" / "base" / "parameters.yml"
    credentials_yml = kedro_project_path / "conf" / "local" / "credentials.yml"
    mlflow_yml = kedro_project_path / "conf" / "local" / "mlflow.yml"
    logging_yml = kedro_project_path / "conf" / "local" / "logging.yml"
    pyproject_toml = kedro_project_path / "pyproject.toml"
    _write_yaml(catalog_yml, catalog_config)
    _write_yaml(parameters_yml, {"a": "my_param_a"})
    _write_yaml(mlflow_yml, mlflow_config_wo_tracking)
    _write_yaml(credentials_yml, {})
    _write_yaml(logging_yml, local_logging_config)
    payload = {
        "tool": {
            "kedro": {
                "project_version": kedro_version,
                "project_name": MOCK_PACKAGE_NAME,
                "package_name": MOCK_PACKAGE_NAME,
            }
        }
    }
    _write_toml(pyproject_toml, payload)


class DummyProjectHooks:
    @hook_impl
    def register_config_loader(self, conf_paths: Iterable[str]) -> ConfigLoader:
        return ConfigLoader(conf_paths)

    @hook_impl
    def register_catalog(
        self,
        catalog: Optional[Dict[str, Dict[str, Any]]],
        credentials: Dict[str, Dict[str, Any]],
        load_versions: Dict[str, str],
        save_version: str,
    ) -> DataCatalog:
        return DataCatalog.from_config(
            catalog, credentials, load_versions, save_version
        )


def _mock_imported_settings_paths(mocker, mock_settings):
    for path in [
        "kedro.framework.context.context.settings",
        "kedro.framework.session.session.settings",
        "kedro.framework.project.settings",
    ]:
        mocker.patch(path, mock_settings)
    return mock_settings


def _mock_settings_with_hooks(mocker, hooks):
    class MockSettings(_ProjectSettings):
        _HOOKS = Validator("HOOKS", default=hooks)

    return _mock_imported_settings_paths(mocker, MockSettings())


@pytest.fixture
def mock_settings_with_mlflow_hooks(mocker):

    return _mock_settings_with_hooks(
        mocker,
        hooks=(
            DummyProjectHooks(),
            MlflowHook(),
        ),
    )


@pytest.fixture(autouse=True)
def mocked_logging(mocker):
    # Disable logging.config.dictConfig in KedroSession._setup_logging as
    # it changes logging.config and affects other unit tests
    return mocker.patch("logging.config.dictConfig")


@pytest.fixture
def dummy_pipeline():
    dummy_pipeline = Pipeline(
        [
            node(
                func=fake_fun,
                inputs=["params:a"],
                outputs=[
                    "artifact_data",
                    "metrics_data",
                    "metric_data",
                    "metric_history_data",
                    "model",
                ],
            )
        ]
    )
    return dummy_pipeline


@pytest.fixture(autouse=True)
def mock_pipelines(mocker, dummy_pipeline):
    def mocked_register_pipelines():
        return {
            "__default__": dummy_pipeline,
            "pipeline_off": dummy_pipeline,
            "pipeline_on": dummy_pipeline,
        }

    mocker.patch.object(
        _ProjectPipelines,
        "_get_pipelines_registry_callable",
        return_value=mocked_register_pipelines,
    )

    return mocked_register_pipelines()


@pytest.fixture
def mock_session(
    mocker, mock_settings_with_mlflow_hooks, kedro_project_path
):  # pylint: disable=unused-argument

    # we need to patch "kedro.framework.session.session.validate_settings" instead of
    # "kedro.framework.project.validate_settings" because it is imported
    mocker.patch("kedro.framework.session.session.validate_settings")
    # idem, we patch we need to patch "kedro.framework.session.session._register_hooks_setuptools" instead of
    # "kedro.framework.hooks.manager._register_hooks_setuptools" because it is imported

    mocker.patch(
        "kedro.framework.session.session._register_hooks_setuptools"
    )  # prevent registering the one of the plugins which are already installed
    configure_project(MOCK_PACKAGE_NAME)
    return KedroSession.create(MOCK_PACKAGE_NAME, kedro_project_path)


def test_deactivated_tracking_but_not_for_given_pipeline(
    mocker, config_dir, kedro_project_path, mock_session
):

    mocker.patch("kedro.framework.session.session.KedroSession._setup_logging")

    with mock_session:

        mock_session.load_context()  # setup mlflow config

        mlflow_client = MlflowClient((Path(kedro_project_path) / "mlruns").as_uri())

        # 0 is default, 1 is "fake_exp"
        all_runs_id_beginning = set(
            [
                run.run_id
                for k in range(len(mlflow_client.list_experiments()))
                for run in mlflow_client.list_run_infos(experiment_id=f"{k}")
            ]
        )

        mock_session.run(pipeline_name="pipeline_on")

        all_runs_id_end = set(
            [
                run.run_id
                for k in range(len(mlflow_client.list_experiments()))
                for run in mlflow_client.list_run_infos(experiment_id=f"{k}")
            ]
        )

        assert len(all_runs_id_end - all_runs_id_beginning) == 1  # 1 run is created


def test_deactivated_tracking_for_given_pipeline(
    mocker, config_dir, kedro_project_path, mock_session
):

    mocker.patch("kedro.framework.session.session.KedroSession._setup_logging")

    with mock_session:
        mlflow_client = MlflowClient((kedro_project_path / "mlruns").as_uri())

        # 0 is default, 1 is "fake_exp"
        all_runs_id_beginning = set(
            [
                run.run_id
                for k in range(len(mlflow_client.list_experiments()))
                for run in mlflow_client.list_run_infos(experiment_id=f"{k}")
            ]
        )

        mock_session.run(pipeline_name="pipeline_off")

        all_runs_id_end = set(
            [
                run.run_id
                for k in range(len(mlflow_client.list_experiments()))
                for run in mlflow_client.list_run_infos(experiment_id=f"{k}")
            ]
        )

        assert all_runs_id_beginning == all_runs_id_end  # no run is created
