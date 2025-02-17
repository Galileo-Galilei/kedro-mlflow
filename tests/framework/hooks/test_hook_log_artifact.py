import mlflow
import pandas as pd
import pytest
from kedro.framework.hooks import _create_hook_manager
from kedro.framework.hooks.manager import _register_hooks
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog, MemoryDataset
from kedro.pipeline import Pipeline, node
from kedro.runner import ThreadRunner
from kedro_datasets.pickle import PickleDataset

from kedro_mlflow.framework.hooks.mlflow_hook import MlflowHook
from kedro_mlflow.io.artifacts import MlflowArtifactDataset


@pytest.fixture
def dummy_pipeline():
    def preprocess_fun(data):
        return data

    def train_fun(data):
        return 2

    dummy_pipeline = Pipeline(
        [
            node(
                func=preprocess_fun,
                inputs="raw_data",
                outputs="data",
            ),
            node(
                func=train_fun,
                inputs=["data"],
                outputs="model",
            ),
        ]
    )
    return dummy_pipeline


@pytest.fixture
def dummy_catalog(tmp_path):
    dummy_catalog = DataCatalog(
        {
            "raw_data": MemoryDataset(pd.DataFrame(data=[1], columns=["a"])),
            "data": MemoryDataset(),
            "model": MlflowArtifactDataset(
                dataset=dict(
                    type=PickleDataset, filepath=(tmp_path / "model.csv").as_posix()
                )
            ),
        }
    )
    return dummy_catalog


@pytest.fixture
def dummy_run_params(tmp_path):
    dummy_run_params = {
        "project_path": tmp_path.as_posix(),
        "env": "local",
        "kedro_version": "0.16.0",
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


def test_mlflow_hook_log_artifacts_within_same_run_with_thread_runner(
    kedro_project, dummy_run_params, dummy_pipeline, dummy_catalog
):
    # this test is very specific to a new design introduced in mlflow 2.18 to make it thread safe
    # see https://github.com/Galileo-Galilei/kedro-mlflow/issues/613
    bootstrap_project(kedro_project)

    with KedroSession.create(project_path=kedro_project) as session:
        context = session.load_context()  # setup mlflow

        mlflow_hook = MlflowHook()
        runner = ThreadRunner()  # this is what we want to test

        mlflow_hook.after_context_created(context)
        mlflow_hook.after_catalog_created(
            catalog=dummy_catalog,
            # `after_catalog_created` is not using any of arguments bellow,
            # so we are setting them to empty values.
            conf_catalog={},
            conf_creds={},
            feed_dict={},
            save_version="",
            load_versions="",
        )
        mlflow_hook.before_pipeline_run(
            run_params=dummy_run_params,
            pipeline=dummy_pipeline,
            catalog=dummy_catalog,
        )

        # we get the run id BEFORE running the pipeline because it was modified in different thread
        run_id_before_run = mlflow.active_run().info.run_id

        hook_manager = _create_hook_manager()
        _register_hooks(hook_manager, (mlflow_hook,))

        runner.run(dummy_pipeline, dummy_catalog, hook_manager)

        run_id_after_run = mlflow.active_run().info.run_id

        # CHECK 1: check that we are not on the second id created by the thread.lock()
        assert run_id_before_run == run_id_after_run

        mlflow_hook.after_pipeline_run(
            run_params=dummy_run_params,
            pipeline=dummy_pipeline,
            catalog=dummy_catalog,
        )

        mlflow_client = context.mlflow.server._mlflow_client

        # check that the artifact is assocaied to the initial run:

        artifacts_list = mlflow_client.list_artifacts(run_id_before_run)
        assert len(artifacts_list) == 1
