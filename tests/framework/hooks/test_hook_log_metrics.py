import mlflow
import pandas as pd
import pytest
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog, MemoryDataset
from kedro.pipeline import Pipeline, node
from kedro.runner import SequentialRunner
from kedro_datasets.pickle import PickleDataset

from kedro_mlflow.framework.hooks.mlflow_hook import MlflowHook
from kedro_mlflow.io.metrics import (
    MlflowMetricDataset,
    MlflowMetricHistoryDataset,
    MlflowMetricsHistoryDataset,
)

TEST_METRIC_VALUE = 1.1


@pytest.fixture
def dummy_pipeline():
    def preprocess_fun(data):
        return data

    def train_fun(data, param):
        return 2

    def metrics_fun(data, model):
        return {"metric_key": {"value": TEST_METRIC_VALUE, "step": 0}}

    def metric_fun(data, model):
        return TEST_METRIC_VALUE

    def metric_history_fun(data, model):
        return [0.1, 0.2]

    def predict_fun(model, data):
        return data * model

    dummy_pipeline = Pipeline(
        [
            node(
                func=preprocess_fun,
                inputs="raw_data",
                outputs="data",
                tags=["training", "inference"],
            ),
            node(
                func=train_fun,
                inputs=["data", "params:unused_param"],
                outputs="model",
                tags=["training"],
            ),
            node(
                func=metrics_fun,
                inputs=["model", "data"],
                outputs="my_metrics",
                tags=["training"],
            ),
            node(
                func=metrics_fun,
                inputs=["model", "data"],
                outputs="another_metrics",
                tags=["training"],
            ),
            node(
                func=metric_fun,
                inputs=["model", "data"],
                outputs="my_metric",
                tags=["training"],
            ),
            node(
                func=metric_fun,
                inputs=["model", "data"],
                outputs="another_metric",
                tags=["training"],
            ),
            node(
                func=metric_history_fun,
                inputs=["model", "data"],
                outputs="my_metric_history",
                tags=["training"],
            ),
            node(
                func=metric_history_fun,
                inputs=["model", "data"],
                outputs="another_metric_history",
                tags=["training"],
            ),
            node(
                func=predict_fun,
                inputs=["model", "data"],
                outputs="predictions",
                tags=["inference"],
            ),
        ]
    )
    return dummy_pipeline


@pytest.fixture
def dummy_catalog(tmp_path):
    dummy_catalog = DataCatalog(
        {
            "raw_data": MemoryDataset(pd.DataFrame(data=[1], columns=["a"])),
            "params:unused_param": MemoryDataset("blah"),
            "data": MemoryDataset(),
            "model": PickleDataset(filepath=(tmp_path / "model.csv").as_posix()),
            "my_metrics": MlflowMetricsHistoryDataset(),
            "another_metrics": MlflowMetricsHistoryDataset(prefix="foo"),
            "my_metric": MlflowMetricDataset(),
            "another_metric": MlflowMetricDataset(key="foo"),
            "my_metric_history": MlflowMetricHistoryDataset(),
            "another_metric_history": MlflowMetricHistoryDataset(key="bar"),
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


def test_mlflow_hook_automatically_prefix_metrics_dataset(
    kedro_project_with_mlflow_conf, dummy_catalog
):
    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf) as session:
        context = session.load_context()  # triggers conf setup

        # config_with_base_mlflow_conf is a conftest fixture
        mlflow_hook = MlflowHook()
        mlflow_hook.after_context_created(context)  # setup mlflow config

        mlflow_hook.after_catalog_created(
            catalog=dummy_catalog,
            # `after_catalog_created` is not using any of below arguments,
            # so we are setting them to empty values.
            conf_catalog={},
            conf_creds={},
            feed_dict={},
            save_version="",
            load_versions="",
        )
        # Check if metrics datasets have prefix with its names.
        # for metric
        assert dummy_catalog._datasets["my_metrics"]._prefix == "my_metrics"
        assert dummy_catalog._datasets["another_metrics"]._prefix == "foo"
        assert dummy_catalog._datasets["my_metric"].key == "my_metric"
        assert dummy_catalog._datasets["another_metric"].key == "foo"


def test_mlflow_hook_metrics_dataset_with_run_id(
    kedro_project_with_mlflow_conf, dummy_pipeline, dummy_run_params
):
    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf) as session:
        context = session.load_context()  # setup mlflow

        with mlflow.start_run():
            existing_run_id = mlflow.active_run().info.run_id

        dummy_catalog_with_run_id = DataCatalog(
            {
                "raw_data": MemoryDataset(pd.DataFrame(data=[1], columns=["a"])),
                "params:unused_param": MemoryDataset("blah"),
                "data": MemoryDataset(),
                "model": PickleDataset(
                    filepath=(
                        kedro_project_with_mlflow_conf / "data" / "model.csv"
                    ).as_posix()
                ),
                "my_metrics": MlflowMetricsHistoryDataset(run_id=existing_run_id),
                "another_metrics": MlflowMetricsHistoryDataset(
                    run_id=existing_run_id, prefix="foo"
                ),
                "my_metric": MlflowMetricDataset(run_id=existing_run_id),
                "another_metric": MlflowMetricDataset(
                    run_id=existing_run_id, key="foo"
                ),
                "my_metric_history": MlflowMetricHistoryDataset(run_id=existing_run_id),
                "another_metric_history": MlflowMetricHistoryDataset(
                    run_id=existing_run_id, key="bar"
                ),
            }
        )

        mlflow_hook = MlflowHook()
        runner = SequentialRunner()

        mlflow_hook.after_context_created(context)
        mlflow_hook.after_catalog_created(
            catalog=dummy_catalog_with_run_id,
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
            catalog=dummy_catalog_with_run_id,
        )
        runner.run(dummy_pipeline, dummy_catalog_with_run_id, session._hook_manager)

        current_run_id = mlflow.active_run().info.run_id

        mlflow_hook.after_pipeline_run(
            run_params=dummy_run_params,
            pipeline=dummy_pipeline,
            catalog=dummy_catalog_with_run_id,
        )

        mlflow_client = context.mlflow.server._mlflow_client
        # the first run is created in Default (id 0),
        # but the one initialised in before_pipeline_run
        # is create  in kedro_project experiment (id 1)
        all_experiment_ids = [
            exp.experiment_id for exp in mlflow_client.search_experiments()
        ]
        all_run_ids = {
            run.info.run_id
            for run in mlflow_client.search_runs(experiment_ids=all_experiment_ids)
        }

        # the metrics are supposed to have been logged inside existing_run_id
        run_data = mlflow_client.get_run(existing_run_id).data

        # Check if metrics datasets have prefix with its names.
        # for metric
        assert all_run_ids == {current_run_id, existing_run_id}

        assert run_data.metrics["my_metrics.metric_key"] == TEST_METRIC_VALUE
        assert run_data.metrics["foo.metric_key"] == TEST_METRIC_VALUE
        assert run_data.metrics["my_metric"] == TEST_METRIC_VALUE
        assert run_data.metrics["foo"] == TEST_METRIC_VALUE
        assert (
            run_data.metrics["my_metric_history"] == 0.2  # noqa: PLR2004
        )  # the list is stored, but only the last value is retrieved
        assert (
            run_data.metrics["bar"] == 0.2  # noqa: PLR2004
        )  # the list is stored, but only the last value is retrieved
