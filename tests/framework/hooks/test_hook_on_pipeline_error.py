from typing import Any, Dict, Iterable, Optional

import mlflow
import pytest
from kedro.config import ConfigLoader
from kedro.framework.hooks import hook_impl
from kedro.framework.project import Validator, _ProjectPipelines, _ProjectSettings
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline, node
from mlflow.entities import RunStatus
from mlflow.tracking import MlflowClient

from kedro_mlflow.framework.hooks.mlflow_hook import MlflowHook


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


@pytest.fixture
def mock_failing_pipeline(mocker):
    def failing_node():
        mlflow.start_run(nested=True)
        raise ValueError("Let's make this pipeline fail")

    def mocked_register_pipelines():
        failing_pipeline = Pipeline(
            [
                node(
                    func=failing_node,
                    inputs=None,
                    outputs="fake_output",
                )
            ]
        )
        return {"__default__": failing_pipeline, "pipeline_off": failing_pipeline}

    mocker.patch.object(
        _ProjectPipelines,
        "_get_pipelines_registry_callable",
        return_value=mocked_register_pipelines,
    )


@pytest.mark.usefixtures("mock_settings_with_mlflow_hooks")
@pytest.mark.usefixtures("mock_failing_pipeline")
def test_on_pipeline_error(kedro_project_with_mlflow_conf):

    tracking_uri = (kedro_project_with_mlflow_conf / "mlruns").as_uri()

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf) as session:
        context = session.load_context()
        with pytest.raises(ValueError):
            session.run()

        # the run we want is the last one in the configuration experiment
        mlflow_client = MlflowClient(tracking_uri)
        experiment = mlflow_client.get_experiment_by_name(
            context.mlflow.tracking.experiment.name
        )
        failing_run_info = MlflowClient(tracking_uri).list_run_infos(
            experiment.experiment_id
        )[0]
        assert mlflow.active_run() is None  # the run must have been closed
        assert failing_run_info.status == RunStatus.to_string(
            RunStatus.FAILED
        )  # it must be marked as failed
