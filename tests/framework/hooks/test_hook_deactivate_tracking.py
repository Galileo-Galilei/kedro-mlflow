from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pytest
import toml
import yaml
from kedro import __version__ as kedro_version
from kedro.config import AbstractConfigLoader, OmegaConfigLoader
from kedro.framework.hooks import hook_impl
from kedro.framework.project import (
    Validator,
    _ProjectPipelines,
    _ProjectSettings,
    configure_project,
)
from kedro.framework.session import KedroSession
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline, node

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
            "type": "kedro_mlflow.io.artifacts.MlflowArtifactDataset",
            "dataset": {
                "type": "pickle.PickleDataset",
                "filepath": fake_data_filepath,
            },
        },
        "metrics_data": {
            "type": "kedro_mlflow.io.metrics.MlflowMetricsHistoryDataset",
        },
        "metric_data": {
            "type": "kedro_mlflow.io.metrics.MlflowMetricDataset",
        },
        "metric_history_data": {
            "type": "kedro_mlflow.io.metrics.MlflowMetricHistoryDataset",
        },
        "model": {
            "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
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


@pytest.fixture(autouse=True)
def config_dir(
    kedro_project_path,
    catalog_config,
    mlflow_config_wo_tracking,
):
    catalog_yml = kedro_project_path / "conf" / "base" / "catalog.yml"
    parameters_yml = kedro_project_path / "conf" / "base" / "parameters.yml"
    credentials_yml = kedro_project_path / "conf" / "local" / "credentials.yml"
    mlflow_yml = kedro_project_path / "conf" / "local" / "mlflow.yml"
    pyproject_toml = kedro_project_path / "pyproject.toml"
    _write_yaml(catalog_yml, catalog_config)
    _write_yaml(parameters_yml, {"a": "my_param_a"})
    _write_yaml(mlflow_yml, mlflow_config_wo_tracking)
    _write_yaml(credentials_yml, {})
    payload = {
        "tool": {
            "kedro": {
                "project_name": MOCK_PACKAGE_NAME,
                "package_name": MOCK_PACKAGE_NAME,
                "kedro_init_version": kedro_version,
            }
        }
    }
    _write_toml(pyproject_toml, payload)


class DummyProjectHooks:
    @hook_impl
    def register_config_loader(self, conf_paths: Iterable[str]) -> AbstractConfigLoader:
        return OmegaConfigLoader(conf_paths)

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
def mock_session(mocker, mock_settings_with_mlflow_hooks, kedro_project_path):  # pylint: disable=unused-argument
    # we need to patch "kedro.framework.session.session.validate_settings" instead of
    # "kedro.framework.project.validate_settings" because it is imported
    mocker.patch("kedro.framework.session.session.validate_settings")

    # idem, we patch we need to patch "kedro.framework.session.session._register_hooks_entry_points" instead of
    # "kedro.framework.hooks.manager._register_hooks_entry_points" because it is imported
    mocker.patch(
        "kedro.framework.session.session._register_hooks_entry_points"
    )  # prevent registering the one of the plugins which are already installed

    configure_project(MOCK_PACKAGE_NAME)
    return KedroSession.create(kedro_project_path)


def test_deactivated_tracking_but_not_for_given_pipeline(mock_session):
    with mock_session:
        context = mock_session.load_context()  # setup mlflow config

        mlflow_client = context.mlflow.server._mlflow_client

        # 0 is default, 1 is "mock_package_name"
        all_experiment_ids_beginning = [
            exp.experiment_id for exp in mlflow_client.search_experiments()
        ]
        all_run_ids_beginning = {
            run.info.run_id
            for run in mlflow_client.search_runs(
                experiment_ids=all_experiment_ids_beginning
            )
        }

        mock_session.run(pipeline_name="pipeline_on")

        all_experiment_ids_end = [
            exp.experiment_id for exp in mlflow_client.search_experiments()
        ]
        all_run_ids_end = {
            run.info.run_id
            for run in mlflow_client.search_runs(experiment_ids=all_experiment_ids_end)
        }

        assert len(all_run_ids_end - all_run_ids_beginning) == 1  # 1 run is created


def test_deactivated_tracking_for_given_pipeline(mock_session):
    with mock_session:
        context = mock_session.load_context()  # setup mlflow config

        mlflow_client = context.mlflow.server._mlflow_client

        # 0 is default, 1 is "mock_package_name"
        all_experiment_ids_beginning = [
            exp.experiment_id for exp in mlflow_client.search_experiments()
        ]
        all_run_ids_beginning = {
            run.info.run_id
            for run in mlflow_client.search_runs(
                experiment_ids=all_experiment_ids_beginning
            )
        }

        mock_session.run(pipeline_name="pipeline_off")

        all_experiment_ids_end = [
            exp.experiment_id for exp in mlflow_client.search_experiments()
        ]
        all_run_ids_end = {
            run.info.run_id
            for run in mlflow_client.search_runs(experiment_ids=all_experiment_ids_end)
        }

        assert all_run_ids_beginning == all_run_ids_end  # no run is created
