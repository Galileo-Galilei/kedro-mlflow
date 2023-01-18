import mlflow
import pytest
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline

from kedro_mlflow.framework.hooks import MlflowHook


@pytest.mark.parametrize(
    "pipeline_name,expected_mlflow_run_name",
    [
        ("my_cool_pipeline", "my_cool_pipeline"),
        ("__default__", "__default__"),
        (None, "__default__"),
    ],
)
def test_pipeline_use_pipeline_name_as_run_name(
    kedro_project, pipeline_name, expected_mlflow_run_name
):

    dummy_run_params = {
        "run_id": "1234",
        "project_path": "path/to/project",
        "env": "local",
        "kedro_version": "X.Y.Z",
        "tags": [],
        "from_nodes": [],
        "to_nodes": [],
        "node_names": [],
        "from_inputs": [],
        "load_versions": [],
        "pipeline_name": pipeline_name,
        "extra_params": [],
    }

    bootstrap_project(kedro_project)
    with KedroSession.create(
        project_path=kedro_project,
    ) as session:
        context = session.load_context()

        mlflow_node_hook = MlflowHook()
        mlflow_node_hook.after_context_created(context)
        mlflow_node_hook.before_pipeline_run(
            run_params=dummy_run_params, pipeline=Pipeline([]), catalog=DataCatalog()
        )

        assert (
            mlflow.active_run().data.tags["mlflow.runName"] == expected_mlflow_run_name
        )
