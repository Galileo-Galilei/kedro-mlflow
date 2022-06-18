import sys

import mlflow
import pandas as pd
import pytest
from kedro.extras.datasets.pickle import PickleDataSet
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline, node
from kedro.runner import SequentialRunner
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient

from kedro_mlflow.framework.hooks.mlflow_hook import MlflowHook
from kedro_mlflow.pipeline import pipeline_ml_factory
from kedro_mlflow.pipeline.pipeline_ml import PipelineML


@pytest.fixture
def env_from_dict():
    python_version = ".".join(
        [
            str(sys.version_info.major),
            str(sys.version_info.minor),
            str(sys.version_info.micro),
        ]
    )
    env_from_dict = dict(python=python_version, dependencies=["pandas>=1.0.0,<2.0.0"])
    return env_from_dict


@pytest.fixture(autouse=True)
def mocked_logging(mocker):
    # Disable logging.config.dictConfig in KedroSession._setup_logging as
    # it changes logging.config and affects other unit tests
    return mocker.patch("logging.config.dictConfig")


@pytest.fixture
def dummy_pipeline():
    def preprocess_fun(data):
        return data

    def train_fun(data, param):
        return 2

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
def test_mlflow_hook_save_pipeline_ml(
    kedro_project_with_mlflow_conf,
    pipeline_to_run,
    dummy_catalog,
    dummy_run_params,
):

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf) as session:
        context = session.load_context()  # triggers conf setup

        # config_with_base_mlflow_conf is a conftest fixture
        mlflow_hook = MlflowHook()
        mlflow_hook.after_context_created(context)  # setup mlflow config
        runner = SequentialRunner()
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
        mlflow_hook.before_pipeline_run(
            run_params=dummy_run_params, pipeline=pipeline_to_run, catalog=dummy_catalog
        )
        runner.run(pipeline_to_run, dummy_catalog, session._hook_manager)
        run_id = mlflow.active_run().info.run_id
        mlflow_hook.after_pipeline_run(
            run_params=dummy_run_params, pipeline=pipeline_to_run, catalog=dummy_catalog
        )
        # test : parameters should have been logged
        mlflow_client = MlflowClient(context.mlflow.server.mlflow_tracking_uri)
        run_data = mlflow_client.get_run(run_id).data

        # all run_params are recorded as tags
        for k, v in dummy_run_params.items():
            if v:
                assert run_data.tags[k] == str(v)

        # params are not recorded because we don't have MlflowHook here
        # and the model should not be logged when it is not a PipelineML
        nb_artifacts = len(mlflow_client.list_artifacts(run_id))
        if isinstance(pipeline_to_run, PipelineML):
            assert nb_artifacts == 1
        else:
            assert nb_artifacts == 0

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
def test_mlflow_hook_save_pipeline_ml_with_copy_mode(
    kedro_project_with_mlflow_conf,
    dummy_pipeline_ml,
    dummy_catalog,
    dummy_run_params,
    copy_mode,
    expected,
):
    # config_with_base_mlflow_conf is a conftest fixture
    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf) as session:
        context = session.load_context()
        mlflow_hook = MlflowHook()
        runner = SequentialRunner()
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
        mlflow_hook.before_pipeline_run(
            run_params=dummy_run_params, pipeline=pipeline_to_run, catalog=dummy_catalog
        )
        runner.run(pipeline_to_run, dummy_catalog, session._hook_manager)
        run_id = mlflow.active_run().info.run_id
        mlflow_hook.after_pipeline_run(
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


def test_mlflow_hook_save_pipeline_ml_with_parameters(
    kedro_project_with_mlflow_conf,  # a fixture to be in a kedro project
    pipeline_ml_with_parameters,
    dummy_run_params,
):
    # config_with_base_mlflow_conf is a conftest fixture
    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf) as session:

        context = session.load_context()

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

        mlflow_hook = MlflowHook()
        mlflow_hook.after_context_created(context)

        runner = SequentialRunner()
        mlflow_hook.after_catalog_created(
            catalog=catalog_with_parameters,
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
            pipeline=pipeline_ml_with_parameters,
            catalog=catalog_with_parameters,
        )
        runner.run(
            pipeline_ml_with_parameters, catalog_with_parameters, session._hook_manager
        )

        current_run_id = mlflow.active_run().info.run_id

        # This is what we want to test: model must be saved and the parameters automatically persisted on disk
        mlflow_hook.after_pipeline_run(
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
def test_mlflow_hook_save_pipeline_ml_with_signature(
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
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf) as session:
        mlflow_hook = MlflowHook()
        runner = SequentialRunner()

        pipeline_to_run = pipeline_ml_factory(
            training=dummy_pipeline.only_nodes_with_tags("training"),
            inference=dummy_pipeline.only_nodes_with_tags("inference"),
            input_name="raw_data",
            log_model_kwargs={
                "conda_env": env_from_dict,
                "signature": model_signature,
            },
        )

        context = session.load_context()
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
            run_params=dummy_run_params, pipeline=pipeline_to_run, catalog=dummy_catalog
        )
        runner.run(pipeline_to_run, dummy_catalog, session._hook_manager)
        run_id = mlflow.active_run().info.run_id
        mlflow_hook.after_pipeline_run(
            run_params=dummy_run_params, pipeline=pipeline_to_run, catalog=dummy_catalog
        )

        # test : parameters should have been logged
        trained_model = mlflow.pyfunc.load_model(f"runs:/{run_id}/model")
        assert trained_model.metadata.signature == expected_signature


@pytest.mark.parametrize(
    "artifact_path,expected_artifact_path",
    ([None, "model"], ["my_custom_model", "my_custom_model"]),
)
def test_mlflow_hook_save_pipeline_ml_with_artifact_path(
    kedro_project_with_mlflow_conf,
    env_from_dict,
    dummy_pipeline,
    dummy_catalog,
    dummy_run_params,
    artifact_path,
    expected_artifact_path,
):
    # config_with_base_mlflow_conf is a conftest fixture
    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf) as session:
        mlflow_hook = MlflowHook()
        runner = SequentialRunner()

        log_model_kwargs = {
            "conda_env": env_from_dict,
        }
        if artifact_path is not None:
            # we need to test what happens if the key is NOT present
            log_model_kwargs["artifact_path"] = artifact_path

        pipeline_to_run = pipeline_ml_factory(
            training=dummy_pipeline.only_nodes_with_tags("training"),
            inference=dummy_pipeline.only_nodes_with_tags("inference"),
            input_name="raw_data",
            log_model_kwargs=log_model_kwargs,
        )

        context = session.load_context()
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
            run_params=dummy_run_params, pipeline=pipeline_to_run, catalog=dummy_catalog
        )
        runner.run(pipeline_to_run, dummy_catalog, session._hook_manager)
        run_id = mlflow.active_run().info.run_id
        mlflow_hook.after_pipeline_run(
            run_params=dummy_run_params, pipeline=pipeline_to_run, catalog=dummy_catalog
        )

        # test : parameters should have been logged
        trained_model = mlflow.pyfunc.load_model(
            f"runs:/{run_id}/{expected_artifact_path}"
        )
        # the real test is that the model is loaded without error
        assert trained_model is not None
