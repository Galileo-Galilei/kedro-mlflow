import sys
from typing import Any, Dict, Iterable, Optional

import mlflow
import pandas as pd
import pytest
import yaml
from kedro.config import ConfigLoader
from kedro.extras.datasets.pickle import PickleDataSet
from kedro.framework.hooks import hook_impl
from kedro.framework.project import Validator, _ProjectPipelines, _ProjectSettings
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline, node
from kedro.runner import SequentialRunner
from kedro.versioning import Journal
from mlflow.entities import RunStatus
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient

from kedro_mlflow.config import get_mlflow_config
from kedro_mlflow.framework.hooks.pipeline_hook import (
    MlflowPipelineHook,
    _generate_kedro_command,
)
from kedro_mlflow.io.metrics import (
    MlflowMetricDataSet,
    MlflowMetricHistoryDataSet,
    MlflowMetricsDataSet,
)
from kedro_mlflow.pipeline import pipeline_ml_factory
from kedro_mlflow.pipeline.pipeline_ml import PipelineML


@pytest.fixture
def python_version():
    python_version = ".".join(
        [
            str(sys.version_info.major),
            str(sys.version_info.minor),
            str(sys.version_info.micro),
        ]
    )
    return python_version


@pytest.fixture
def requirements_path(tmp_path):
    return tmp_path / "requirements.txt"


@pytest.fixture
def requirements_path_str(requirements_path):
    return requirements_path.as_posix()


@pytest.fixture
def environment_path(tmp_path):
    return tmp_path / "environment.yml"


@pytest.fixture
def environment_path_str(environment_path):
    return environment_path.as_posix()


@pytest.fixture
def env_from_none(python_version):
    return dict(python=python_version)


@pytest.fixture
def env_from_requirements(requirements_path, python_version):
    requirements_data = ["pandas>=1.0.0,<2.0.0", "kedro==0.15.9"]
    with open(requirements_path, mode="w") as file_handler:
        for item in requirements_data:
            file_handler.write(f"{item}\n")
    return dict(python=python_version, dependencies=requirements_data)


@pytest.fixture
def env_from_dict(python_version):
    env_from_dict = dict(python=python_version, dependencies=["pandas>=1.0.0,<2.0.0"])
    return env_from_dict


@pytest.fixture
def env_from_environment(environment_path, env_from_dict):

    with open(environment_path, mode="w") as file_handler:
        yaml.dump(env_from_dict, file_handler)

    env_from_environment = env_from_dict

    return env_from_environment


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
        journal: Journal,
    ) -> DataCatalog:
        return DataCatalog.from_config(
            catalog, credentials, load_versions, save_version, journal
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
            MlflowPipelineHook(),
            # MlflowNodeHook(),
        ),
    )


@pytest.fixture(autouse=True)
def mocked_logging(mocker):
    # Disable logging.config.dictConfig in KedroSession._setup_logging as
    # it changes logging.config and affects other unit tests
    return mocker.patch("logging.config.dictConfig")


@pytest.fixture
def mock_failing_pipelines(mocker):
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


@pytest.fixture
def dummy_pipeline():
    def preprocess_fun(data):
        return data

    def train_fun(data, param):
        return 2

    def metrics_fun(data, model):
        return {"metric_key": {"value": 1.1, "step": 0}}

    def metric_fun(data, model):
        return 1.1

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
def dummy_pipeline_ml(dummy_pipeline, env_from_dict):

    dummy_pipeline_ml = pipeline_ml_factory(
        training=dummy_pipeline.only_nodes_with_tags("training"),
        inference=dummy_pipeline.only_nodes_with_tags("inference"),
        input_name="raw_data",
        log_model_kwargs={"conda_env": env_from_dict, "artifact_path": "model"},
    )
    return dummy_pipeline_ml


@pytest.fixture
def dummy_catalog(tmp_path):
    dummy_catalog = DataCatalog(
        {
            "raw_data": MemoryDataSet(pd.DataFrame(data=[1], columns=["a"])),
            "params:unused_param": MemoryDataSet("blah"),
            "data": MemoryDataSet(),
            "model": PickleDataSet((tmp_path / "model.csv").as_posix()),
            "my_metrics": MlflowMetricsDataSet(),
            "another_metrics": MlflowMetricsDataSet(prefix="foo"),
            "my_metric": MlflowMetricDataSet(),
            "another_metric": MlflowMetricDataSet(key="foo"),
            "my_metric_history": MlflowMetricHistoryDataSet(),
            "another_metric_history": MlflowMetricHistoryDataSet(key="bar"),
        }
    )
    return dummy_catalog


@pytest.fixture
def pipeline_ml_with_parameters():
    def remove_stopwords(data, stopwords):
        return data

    def train_fun_hyperparam(data, hyperparam):
        return 2

    def predict_fun(model, data):
        return data * model

    def convert_probs_to_pred(data, threshold):
        return (data > threshold) * 1

    full_pipeline = Pipeline(
        [
            # almost the same that previsously but stopwords are parameters
            # this is a shared parameter between inference and training22
            node(
                func=remove_stopwords,
                inputs=dict(data="data", stopwords="params:stopwords"),
                outputs="cleaned_data",
                tags=["training", "inference"],
            ),
            # parameters in training pipeline, should not be persisted
            node(
                func=train_fun_hyperparam,
                inputs=["cleaned_data", "params:penalty"],
                outputs="model",
                tags=["training"],
            ),
            node(
                func=predict_fun,
                inputs=["model", "cleaned_data"],
                outputs="predicted_probs",
                tags=["inference"],
            ),
            # this time, there is a parameter only for the inference pipeline
            node(
                func=convert_probs_to_pred,
                inputs=["predicted_probs", "params:threshold"],
                outputs="predictions",
                tags=["inference"],
            ),
        ]
    )
    pipeline_ml_with_parameters = pipeline_ml_factory(
        training=full_pipeline.only_nodes_with_tags("training"),
        inference=full_pipeline.only_nodes_with_tags("inference"),
        input_name="data",
        log_model_kwargs={
            "conda_env": {"python": "3.7.0", "dependencies": ["kedro==0.16.5"]},
        },
    )
    return pipeline_ml_with_parameters


@pytest.fixture
def dummy_signature(dummy_catalog, dummy_pipeline_ml):
    input_data = dummy_catalog.load(dummy_pipeline_ml.input_name)
    dummy_signature = infer_signature(input_data)
    return dummy_signature


@pytest.fixture
def dummy_run_params(tmp_path):
    dummy_run_params = {
        "run_id": "abcdef",
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


@pytest.mark.parametrize(
    "pipeline_to_run",
    [
        (pytest.lazy_fixture("dummy_pipeline")),
        (pytest.lazy_fixture("dummy_pipeline_ml")),
    ],
)
def test_mlflow_pipeline_hook_with_different_pipeline_types(
    kedro_project_with_mlflow_conf,
    env_from_dict,
    pipeline_to_run,
    dummy_catalog,
    dummy_run_params,
):

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        # config_with_base_mlflow_conf is a conftest fixture
        pipeline_hook = MlflowPipelineHook()
        runner = SequentialRunner()
        pipeline_hook.after_catalog_created(
            catalog=dummy_catalog,
            # `after_catalog_created` is not using any of below arguments,
            # so we are setting them to empty values.
            conf_catalog={},
            conf_creds={},
            feed_dict={},
            save_version="",
            load_versions="",
            run_id=dummy_run_params["run_id"],
        )
        pipeline_hook.before_pipeline_run(
            run_params=dummy_run_params, pipeline=pipeline_to_run, catalog=dummy_catalog
        )
        runner.run(pipeline_to_run, dummy_catalog)
        run_id = mlflow.active_run().info.run_id
        pipeline_hook.after_pipeline_run(
            run_params=dummy_run_params, pipeline=pipeline_to_run, catalog=dummy_catalog
        )
        # test : parameters should have been logged
        mlflow_conf = get_mlflow_config()
        mlflow_client = MlflowClient(mlflow_conf.server.mlflow_tracking_uri)
        run_data = mlflow_client.get_run(run_id).data

        # all run_params are recorded as tags
        for k, v in dummy_run_params.items():
            if v:
                assert run_data.tags[k] == str(v)

        # params are not recorded because we don't have MlflowNodeHook here
        # and the model should not be logged when it is not a PipelineML
        nb_artifacts = len(mlflow_client.list_artifacts(run_id))
        if isinstance(pipeline_to_run, PipelineML):
            assert nb_artifacts == 1
        else:
            assert nb_artifacts == 0

        # Check if metrics datasets have prefix with its names.
        # for metric
        assert dummy_catalog._data_sets["my_metrics"]._prefix == "my_metrics"
        assert dummy_catalog._data_sets["another_metrics"]._prefix == "foo"
        assert dummy_catalog._data_sets["my_metric"].key == "my_metric"
        assert dummy_catalog._data_sets["another_metric"].key == "foo"

        if isinstance(pipeline_to_run, PipelineML):
            trained_model = mlflow.pyfunc.load_model(f"runs:/{run_id}/model")
            assert trained_model.metadata.signature.to_dict() == {
                "inputs": '[{"name": "a", "type": "long"}]',
                "outputs": None,
            }


@pytest.mark.parametrize(
    "copy_mode,expected",
    [
        (None, {"raw_data": None, "data": None, "model": None}),
        ("assign", {"raw_data": "assign", "data": "assign", "model": "assign"}),
        ("deepcopy", {"raw_data": "deepcopy", "data": "deepcopy", "model": "deepcopy"}),
        ({"model": "assign"}, {"raw_data": None, "data": None, "model": "assign"}),
    ],
)
def test_mlflow_pipeline_hook_with_copy_mode(
    kedro_project_with_mlflow_conf,
    dummy_pipeline_ml,
    dummy_catalog,
    dummy_run_params,
    copy_mode,
    expected,
):
    # config_with_base_mlflow_conf is a conftest fixture
    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):

        pipeline_hook = MlflowPipelineHook()
        runner = SequentialRunner()

        pipeline_hook.after_catalog_created(
            catalog=dummy_catalog,
            # `after_catalog_created` is not using any of arguments bellow,
            # so we are setting them to empty values.
            conf_catalog={},
            conf_creds={},
            feed_dict={},
            save_version="",
            load_versions="",
            run_id=dummy_run_params["run_id"],
        )

        pipeline_to_run = pipeline_ml_factory(
            training=dummy_pipeline_ml.training,
            inference=dummy_pipeline_ml.inference,
            input_name=dummy_pipeline_ml.input_name,
            log_model_kwargs={
                "artifact_path": dummy_pipeline_ml.log_model_kwargs["artifact_path"],
                "conda_env": {"python": "3.7.0", "dependencies": ["kedro==0.16.5"]},
            },
            kpm_kwargs={
                "copy_mode": copy_mode,
            },
        )
        pipeline_hook.before_pipeline_run(
            run_params=dummy_run_params, pipeline=pipeline_to_run, catalog=dummy_catalog
        )
        runner.run(pipeline_to_run, dummy_catalog)
        run_id = mlflow.active_run().info.run_id
        pipeline_hook.after_pipeline_run(
            run_params=dummy_run_params, pipeline=pipeline_to_run, catalog=dummy_catalog
        )

        mlflow_tracking_uri = (kedro_project_with_mlflow_conf / "mlruns").as_uri()
        mlflow.set_tracking_uri(mlflow_tracking_uri)

        loaded_model = mlflow.pyfunc.load_model(model_uri=f"runs:/{run_id}/model")

        actual_copy_mode = {
            name: ds._copy_mode
            for name, ds in loaded_model._model_impl.python_model.loaded_catalog._data_sets.items()
        }

        assert actual_copy_mode == expected


def test_mlflow_pipeline_hook_metric_metrics_with_run_id(
    kedro_project_with_mlflow_conf, dummy_pipeline_ml, dummy_run_params
):

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):

        mlflow_conf = get_mlflow_config()
        mlflow.set_tracking_uri(mlflow_conf.server.mlflow_tracking_uri)

        with mlflow.start_run():
            existing_run_id = mlflow.active_run().info.run_id

        dummy_catalog_with_run_id = DataCatalog(
            {
                "raw_data": MemoryDataSet(pd.DataFrame(data=[1], columns=["a"])),
                "params:unused_param": MemoryDataSet("blah"),
                "data": MemoryDataSet(),
                "model": PickleDataSet(
                    (kedro_project_with_mlflow_conf / "data" / "model.csv").as_posix()
                ),
                "my_metrics": MlflowMetricsDataSet(run_id=existing_run_id),
                "another_metrics": MlflowMetricsDataSet(
                    run_id=existing_run_id, prefix="foo"
                ),
                "my_metric": MlflowMetricDataSet(run_id=existing_run_id),
                "another_metric": MlflowMetricDataSet(
                    run_id=existing_run_id, key="foo"
                ),
                "my_metric_history": MlflowMetricHistoryDataSet(run_id=existing_run_id),
                "another_metric_history": MlflowMetricHistoryDataSet(
                    run_id=existing_run_id, key="bar"
                ),
            }
        )

        pipeline_hook = MlflowPipelineHook()

        runner = SequentialRunner()
        pipeline_hook.after_catalog_created(
            catalog=dummy_catalog_with_run_id,
            # `after_catalog_created` is not using any of arguments bellow,
            # so we are setting them to empty values.
            conf_catalog={},
            conf_creds={},
            feed_dict={},
            save_version="",
            load_versions="",
            run_id=dummy_run_params["run_id"],
        )
        pipeline_hook.before_pipeline_run(
            run_params=dummy_run_params,
            pipeline=dummy_pipeline_ml,
            catalog=dummy_catalog_with_run_id,
        )
        runner.run(dummy_pipeline_ml, dummy_catalog_with_run_id)

        current_run_id = mlflow.active_run().info.run_id

        pipeline_hook.after_pipeline_run(
            run_params=dummy_run_params,
            pipeline=dummy_pipeline_ml,
            catalog=dummy_catalog_with_run_id,
        )

        mlflow_client = MlflowClient(mlflow_conf.server.mlflow_tracking_uri)
        # the first run is created in Default (id 0),
        # but the one initialised in before_pipeline_run
        # is create  in kedro_project experiment (id 1)
        all_runs_id = set(
            [
                run.run_id
                for k in range(2)
                for run in mlflow_client.list_run_infos(experiment_id=f"{k}")
            ]
        )

        # the metrics are supposed to have been logged inside existing_run_id
        run_data = mlflow_client.get_run(existing_run_id).data

        # Check if metrics datasets have prefix with its names.
        # for metric
        assert all_runs_id == {current_run_id, existing_run_id}

        assert run_data.metrics["my_metrics.metric_key"] == 1.1
        assert run_data.metrics["foo.metric_key"] == 1.1
        assert run_data.metrics["my_metric"] == 1.1
        assert run_data.metrics["foo"] == 1.1
        assert (
            run_data.metrics["my_metric_history"] == 0.2
        )  # the list is tored, but only the last value is retrieved
        assert (
            run_data.metrics["bar"] == 0.2
        )  # the list is tored, but only the last value is retrieved


def test_mlflow_pipeline_hook_save_pipeline_ml_with_parameters(
    kedro_project_with_mlflow_conf,  # a fixture to be in a kedro project
    tmp_path,
    pipeline_ml_with_parameters,
    dummy_run_params,
):
    # config_with_base_mlflow_conf is a conftest fixture
    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):

        mlflow_conf = get_mlflow_config()
        mlflow.set_tracking_uri(mlflow_conf.server.mlflow_tracking_uri)

        catalog_with_parameters = DataCatalog(
            {
                "data": MemoryDataSet(pd.DataFrame(data=[1], columns=["a"])),
                "cleaned_data": MemoryDataSet(),
                "params:stopwords": MemoryDataSet(["Hello", "Hi"]),
                "params:penalty": MemoryDataSet(0.1),
                "model": PickleDataSet(
                    (kedro_project_with_mlflow_conf / "data" / "model.csv").as_posix()
                ),
                "params:threshold": MemoryDataSet(0.5),
            }
        )

        pipeline_hook = MlflowPipelineHook()

        runner = SequentialRunner()
        pipeline_hook.after_catalog_created(
            catalog=catalog_with_parameters,
            # `after_catalog_created` is not using any of arguments bellow,
            # so we are setting them to empty values.
            conf_catalog={},
            conf_creds={},
            feed_dict={},
            save_version="",
            load_versions="",
            run_id=dummy_run_params["run_id"],
        )
        pipeline_hook.before_pipeline_run(
            run_params=dummy_run_params,
            pipeline=pipeline_ml_with_parameters,
            catalog=catalog_with_parameters,
        )
        runner.run(pipeline_ml_with_parameters, catalog_with_parameters)

        current_run_id = mlflow.active_run().info.run_id

        # This is what we want to test: model must be saved and the parameters automatically persisted on disk
        pipeline_hook.after_pipeline_run(
            run_params=dummy_run_params,
            pipeline=pipeline_ml_with_parameters,
            catalog=catalog_with_parameters,
        )

        # the 2 parameters which are inputs of inference pipeline
        # must have been persisted and logged inside the model's artifacts
        model = mlflow.pyfunc.load_model(f"runs:/{current_run_id}/model")
        assert set(
            model.metadata.to_dict()["flavors"]["python_function"]["artifacts"].keys()
        ) == {"model", "params:stopwords", "params:threshold"}

        # the model should be loadable and predict() should work (this tests KedroPipelineModel)
        assert model.predict(pd.DataFrame(data=[1], columns=["a"])).values[0][0] == 1


@pytest.mark.parametrize(
    "model_signature,expected_signature",
    (
        [None, None],
        ["auto", pytest.lazy_fixture("dummy_signature")],
        [
            pytest.lazy_fixture("dummy_signature"),
            pytest.lazy_fixture("dummy_signature"),
        ],
    ),
)
def test_mlflow_pipeline_hook_with_pipeline_ml_signature(
    kedro_project_with_mlflow_conf,
    env_from_dict,
    dummy_pipeline,
    dummy_catalog,
    dummy_run_params,
    model_signature,
    expected_signature,
):
    # config_with_base_mlflow_conf is a conftest fixture
    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        pipeline_hook = MlflowPipelineHook()
        runner = SequentialRunner()

        pipeline_to_run = pipeline_ml_factory(
            training=dummy_pipeline.only_nodes_with_tags("training"),
            inference=dummy_pipeline.only_nodes_with_tags("inference"),
            input_name="raw_data",
            log_model_kwargs={
                "conda_env": env_from_dict,
                "artifact_path": "model",
                "signature": model_signature,
            },
        )

        pipeline_hook.after_catalog_created(
            catalog=dummy_catalog,
            # `after_catalog_created` is not using any of arguments bellow,
            # so we are setting them to empty values.
            conf_catalog={},
            conf_creds={},
            feed_dict={},
            save_version="",
            load_versions="",
            run_id=dummy_run_params["run_id"],
        )
        pipeline_hook.before_pipeline_run(
            run_params=dummy_run_params, pipeline=pipeline_to_run, catalog=dummy_catalog
        )
        runner.run(pipeline_to_run, dummy_catalog)
        run_id = mlflow.active_run().info.run_id
        pipeline_hook.after_pipeline_run(
            run_params=dummy_run_params, pipeline=pipeline_to_run, catalog=dummy_catalog
        )

        # test : parameters should have been logged
        trained_model = mlflow.pyfunc.load_model(f"runs:/{run_id}/model")
        assert trained_model.metadata.signature == expected_signature


def test_generate_kedro_commands():
    # TODO : add a better test because the formatting of record_data is subject to change
    # We could check that the command is recored and then rerun properly
    record_data = {
        "tags": ["tag1", "tag2"],
        "from_nodes": ["node1"],
        "to_nodes": ["node3"],
        "node_names": ["node1", "node2", "node1"],
        "from_inputs": ["data_in"],
        "load_versions": {"data_inter": "01:23:45"},
        "pipeline_name": "fake_pl",
    }

    expected = "kedro run --from-inputs=data_in --from-nodes=node1 --to-nodes=node3 --node=node1,node2,node1 --pipeline=fake_pl --tag=tag1,tag2 --load-version=data_inter:01:23:45"
    assert _generate_kedro_command(**record_data) == expected


@pytest.mark.parametrize("default_value", [None, []])
def test_generate_default_kedro_commands(default_value):
    """This test ensures that the _generate_kedro_comands accepts both
     `None` and empty `list` as default value, because CLI and interactive
     `Journal` do not use the same default.

    Args:
        default_value ([type]): [description]
    """
    record_data = {
        "tags": default_value,
        "from_nodes": default_value,
        "to_nodes": default_value,
        "node_names": default_value,
        "from_inputs": default_value,
        "load_versions": default_value,
        "pipeline_name": "fake_pl",
    }

    expected = "kedro run --pipeline=fake_pl"
    assert _generate_kedro_command(**record_data) == expected


def test_on_pipeline_error(
    kedro_project_with_mlflow_conf,
    mock_settings_with_mlflow_hooks,
    mock_failing_pipelines,
):

    tracking_uri = (kedro_project_with_mlflow_conf / "mlruns").as_uri()

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf) as session:
        kmc = get_mlflow_config()
        with pytest.raises(ValueError):
            session.run()

        # the run we want is the last one in the configuration experiment
        mlflow_client = MlflowClient(tracking_uri)
        experiment = mlflow_client.get_experiment_by_name(kmc.tracking.experiment.name)
        failing_run_info = MlflowClient(tracking_uri).list_run_infos(
            experiment.experiment_id
        )[0]
        assert mlflow.active_run() is None  # the run must have been closed
        assert failing_run_info.status == RunStatus.to_string(
            RunStatus.FAILED
        )  # it must be marked as failed
