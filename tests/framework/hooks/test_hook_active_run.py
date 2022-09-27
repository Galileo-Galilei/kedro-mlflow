import mlflow
import pytest
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline, node

from kedro_mlflow.framework.hooks import MlflowHook


@pytest.fixture
def dummy_run_params(tmp_path):
    dummy_run_params = {
        "run_id": "",
        "project_path": tmp_path.as_posix(),
        "env": "local",
        "kedro_version": "0.16.5",
        "tags": [],
        "from_nodes": [],
        "to_nodes": [],
        "node_names": [],
        "from_inputs": [],
        "load_versions": [],
        "pipeline_name": "my_cool_pipeline",
        "extra_params": [],
    }
    return dummy_run_params


@pytest.fixture
def dummy_node():
    def fake_fun(arg1, arg2, arg3):
        return None

    node_test = node(
        func=fake_fun,
        inputs={"arg1": "params:param1", "arg2": "foo", "arg3": "parameters"},
        outputs="out",
    )

    return node_test


@pytest.fixture
def dummy_pipeline(dummy_node):

    dummy_pipeline = Pipeline([dummy_node])

    return dummy_pipeline


@pytest.fixture
def dummy_catalog():

    catalog = DataCatalog(
        {
            "params:param1": 1,
            "foo": MemoryDataSet(),
            "bar": MemoryDataSet(),
            "parameters": {"param1": 1, "param2": 2},
        }
    )

    return catalog


def test_hook_use_active_run_if_exist_and_do_not_close(
    kedro_project,
    dummy_run_params,
    dummy_pipeline,
    dummy_catalog,
):

    mlflow.set_tracking_uri(f"file:///{kedro_project}/mlruns")
    with mlflow.start_run():
        mlflow_run_id = mlflow.active_run().info.run_id
        bootstrap_project(kedro_project)
        with KedroSession.create(
            project_path=kedro_project,
        ) as session:
            context = session.load_context()

            mlflow_node_hook = MlflowHook()
            mlflow_node_hook.after_context_created(context)
            mlflow_node_hook.before_pipeline_run(
                run_params=dummy_run_params,
                pipeline=dummy_pipeline,
                catalog=dummy_catalog,
            )
            # check after before_pipeline_run, we should still have the same run
            assert mlflow.active_run().info.run_id == mlflow_run_id

            mlflow_node_hook.after_pipeline_run(
                run_params=dummy_run_params,
                pipeline=dummy_pipeline,
                catalog=dummy_catalog,
            )
            # the run must still be open
            assert mlflow.active_run().info.run_id == mlflow_run_id

            mlflow_node_hook.on_pipeline_error(
                error=ValueError,
                run_params=dummy_run_params,
                pipeline=dummy_pipeline,
                catalog=dummy_catalog,
            )
            # the run must still be open
            assert mlflow.active_run().info.run_id == mlflow_run_id


def test_hook_active_run_exists_with_different_tracking_uri(
    kedro_project,
    dummy_run_params,
    dummy_pipeline,
    dummy_catalog,
):
    # tracking uri is "mlruns2", not "mlruns"
    mlflow.set_tracking_uri(f"file:///{kedro_project}/mlruns2")
    with mlflow.start_run():
        mlflow_run_id = mlflow.active_run().info.run_id
        bootstrap_project(kedro_project)
        with KedroSession.create(
            project_path=kedro_project,
        ) as session:
            context = session.load_context()

            mlflow_node_hook = MlflowHook()
            mlflow_node_hook.after_context_created(context)

            mlflow.log_param("a", "1")  # emulate param logging
            # the config should be modified
            assert (
                mlflow_node_hook.mlflow_config.server.mlflow_tracking_uri
                == f"file:///{kedro_project}/mlruns2"
            )
            assert mlflow_node_hook.mlflow_config.tracking.experiment.name == "Default"
            assert mlflow_node_hook.mlflow_config.tracking.run.id == mlflow_run_id

            assert mlflow.get_tracking_uri() == f"file:///{kedro_project}/mlruns2"

            # mlflow.active_run() does not have all data, we should get it trhough the client: https://www.mlflow.org/docs/latest/python_api/mlflow.html#mlflow.active_run
            active_run = mlflow_node_hook.mlflow_config.server._mlflow_client.get_run(
                mlflow.active_run().info.run_id
            )
            assert active_run.data.params == {"a": "1"}
