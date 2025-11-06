from tempfile import TemporaryDirectory

import mlflow
import pandas as pd
import pytest
from kedro.io import DataCatalog, MemoryDataset
from kedro.io.core import DatasetError
from kedro.pipeline import Pipeline, node
from kedro_datasets.pickle import PickleDataset
from pytest_lazy_fixtures import lf
from sklearn.linear_model import LinearRegression

from kedro_mlflow.io.models import MlflowModelTrackingDataset
from kedro_mlflow.mlflow import KedroPipelineModel
from kedro_mlflow.pipeline import pipeline_ml_factory


@pytest.fixture
def linreg_model():
    linreg_model = LinearRegression()
    linreg_model.fit(
        X=pd.DataFrame(data=[[1, 2], [3, 4]], columns=["a", "b"]),
        y=pd.Series(data=[5, 10]),
    )
    return linreg_model


@pytest.fixture
def tmp_folder():
    tmp_folder = TemporaryDirectory()
    return tmp_folder


@pytest.fixture
def prexisting_run_id(tracking_uri):
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.start_run()
    yield mlflow.active_run().info.run_id
    mlflow.end_run()


@pytest.fixture
def pipeline_ml_obj():
    def preprocess_fun(data):
        return data

    def fit_fun(data):
        return 2

    def predict_fun(model, data):
        return data * model

    full_pipeline = Pipeline(
        [
            node(
                func=preprocess_fun,
                inputs="raw_data",
                outputs="data",
                tags=["inference", "training"],
            ),
            node(func=fit_fun, inputs="data", outputs="model", tags=["training"]),
            node(
                func=predict_fun,
                inputs=["data", "model"],
                outputs="predictions",
                tags=["inference"],
            ),
        ]
    )

    pipeline_ml_obj = pipeline_ml_factory(
        training=full_pipeline.only_nodes_with_tags("training"),
        inference=full_pipeline.only_nodes_with_tags("inference"),
        input_name="raw_data",
    )

    return pipeline_ml_obj


@pytest.fixture
def pipeline_inference(pipeline_ml_obj):
    return pipeline_ml_obj.inference


@pytest.fixture
def dummy_catalog(tmp_path):
    dummy_catalog = DataCatalog(
        {
            "raw_data": MemoryDataset(),
            "data": MemoryDataset(),
            "model": PickleDataset(
                filepath=(tmp_path / "data" / "06_models" / "model.pkl")
                .resolve()
                .as_posix()
            ),
        }
    )
    dummy_catalog["model"].save(2)  # emulate model fitting

    return dummy_catalog


@pytest.fixture
def kedro_pipeline_model(pipeline_ml_obj, dummy_catalog):
    kedro_pipeline_model = KedroPipelineModel(
        pipeline=pipeline_ml_obj,
        catalog=dummy_catalog,
        input_name=pipeline_ml_obj.input_name,
    )

    return kedro_pipeline_model


def test_model_tracking_dataset_flavor_does_not_exists():
    with pytest.raises(DatasetError, match="'mlflow.whoops' module not found"):
        MlflowModelTrackingDataset.from_config(
            name="model_ds",
            config={
                "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
                "save_args": {"name": "whoops"},
                "flavor": "mlflow.whoops",
            },
        )


# TODO: change the test to check that load work and save crashes with model_uri
def test_model_tracking_dataset_ensure_cannot_save_sklearn_flavor_with_model_uri(
    linreg_model,
):
    model_config = {
        "name": "model_ds",
        "config": {
            "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
            "save_args": {"name": "my_linreg"},
            "load_args": {"model_uri": "models:/my_linreg/1"},
            "flavor": "mlflow.sklearn",
        },
    }

    mlflow_model_ds = MlflowModelTrackingDataset.from_config(**model_config)

    with pytest.raises(
        DatasetError,
        match="It is impossible to save a model when 'model_uri' is specified.",
    ):
        mlflow_model_ds.save(linreg_model)


def test_model_tracking_dataset_load_sklearn_flavor_with_model_uri_from_correct_uri(
    linreg_model,
):
    # pre save two different model
    model_info1 = mlflow.sklearn.log_model(linreg_model, "my_linreg1")
    model_info2 = mlflow.sklearn.log_model(linreg_model, "my_linreg2")
    model_config = {
        "name": "model_ds",
        "config": {
            "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
            "save_args": {"name": "my_linreg"},
            "load_args": {"model_uri": model_info1.model_uri},  # load the first one
            "flavor": "mlflow.sklearn",
        },
    }

    mlflow_model_ds = MlflowModelTrackingDataset.from_config(**model_config)

    linreg_model_loaded = mlflow_model_ds.load()
    # the model uri is the one specified in load_args
    assert mlflow_model_ds._describe()["model_uri"] == model_info1.model_uri
    assert mlflow_model_ds._describe()["model_uri"] != model_info2.model_uri

    assert isinstance(linreg_model_loaded, LinearRegression)
    assert pytest.approx(linreg_model_loaded.predict([[1, 2]])[0], abs=10 ** (-14)) == 5  # noqa: PLR2004


def test_model_tracking_dataset_save_and_load_sklearn_flavor_without_model_uri_load_args(
    linreg_model,
):
    model_config = {
        "name": "model_ds",
        "config": {
            "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
            "save_args": {"name": "my_linreg"},
            "flavor": "mlflow.sklearn",
        },
    }

    mlflow_model_ds = MlflowModelTrackingDataset.from_config(**model_config)

    # the model uri is stored just after saving
    assert mlflow_model_ds._describe()["model_uri"] is None
    mlflow_model_ds.save(linreg_model)
    # the model uri is the one specified in load_args
    assert (
        mlflow_model_ds._describe()["model_uri"] == mlflow.last_logged_model().model_uri
    )

    # when reloading, we got the same model
    linreg_model_loaded = mlflow_model_ds.load()

    assert isinstance(linreg_model_loaded, LinearRegression)
    assert pytest.approx(linreg_model_loaded.predict([[1, 2]])[0], abs=10 ** (-14)) == 5  # noqa: PLR2004


def test_model_tracking_dataset_save_twice(linreg_model):
    # when saving twice, the model uri should be updated to the last one

    model_config = {
        "name": "model_ds",
        "config": {
            "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
            "save_args": {"name": "my_linreg"},
            "flavor": "mlflow.sklearn",
        },
    }

    mlflow_model_ds = MlflowModelTrackingDataset.from_config(**model_config)

    # the model uri is stored just after saving
    mlflow_model_ds.save(linreg_model)
    last_logged_model_uri1 = mlflow.last_logged_model().model_uri
    assert mlflow_model_ds._describe()["model_uri"] == last_logged_model_uri1

    # save a second time
    mlflow_model_ds.save(linreg_model)
    last_logged_model_uri2 = mlflow.last_logged_model().model_uri
    assert last_logged_model_uri1 != last_logged_model_uri2
    assert mlflow_model_ds._describe()["model_uri"] == last_logged_model_uri2


# TODO: change the test to load with or without load_args={model_uri}
def test_load_without_model_uri_in_load_args_and_no_save_before(tracking_uri):
    mlflow.set_tracking_uri(tracking_uri)
    # close all opened mlflow runs to avoid interference between tests
    while mlflow.active_run():
        mlflow.end_run()

    name = "my_linreg"
    model_config = {
        "name": "linreg",
        "config": {
            "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
            "save_args": {"name": name},
            "flavor": "mlflow.sklearn",
        },
    }
    mlflow_model_ds = MlflowModelTrackingDataset.from_config(**model_config)

    with pytest.raises(
        DatasetError,
        match="To load from a given model_uri, you must either",
    ):
        mlflow_model_ds.load()


@pytest.mark.parametrize(
    "pipeline",
    [
        (lf("pipeline_ml_obj")),  # must work for PipelineML
        (lf("pipeline_inference")),  # must work for Pipeline
    ],
)
def test_pyfunc_flavor_python_model_save_and_load_tracking_dataset(
    tmp_folder,
    tracking_uri,
    pipeline,
    dummy_catalog,
):
    kedro_pipeline_model = KedroPipelineModel(
        pipeline=pipeline,
        catalog=dummy_catalog,
        input_name="raw_data",
    )
    artifacts = kedro_pipeline_model.extract_pipeline_artifacts(tmp_folder)

    model_config = {
        "name": "kedro_pipeline_model",
        "config": {
            "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
            "flavor": "mlflow.pyfunc",
            "pyfunc_workflow": "python_model",
            "save_args": {
                "name": "test_model",
                "artifacts": artifacts,
                "conda_env": {"python": "3.10.0", "dependencies": ["kedro==0.18.11"]},
            },
        },
    }

    mlflow.set_tracking_uri(tracking_uri)
    mlflow_model_ds = MlflowModelTrackingDataset.from_config(**model_config)
    mlflow_model_ds.save(kedro_pipeline_model)  # no run created in mlflow 3

    model_config2 = model_config.copy()
    # add load args in model_config2 with a model uri key pointing to the last saved model
    model_config2["config"]["load_args"] = {"model_uri": mlflow_model_ds.model_uri}

    mlflow_model_ds2 = MlflowModelTrackingDataset.from_config(**model_config2)

    loaded_model = mlflow_model_ds2.load()

    loaded_model.predict(pd.DataFrame(data=[1], columns=["a"])) == pd.DataFrame(
        data=[2], columns=["a"]
    )


def test_pyfunc_flavor_wrong_pyfunc_workflow(tracking_uri):
    mlflow.set_tracking_uri(tracking_uri)
    model_config = {
        "name": "tracking_ds",
        "config": {
            "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
            "flavor": "mlflow.pyfunc",
            "pyfunc_workflow": "wrong_workflow",
            "save_args": {"name": "kedro_pipeline_model"},
        },
    }
    with pytest.raises(
        DatasetError,
        match=r"PyFunc models require specifying `pyfunc_workflow` \(set to either `python_model` or `loader_module`\)",
    ):
        MlflowModelTrackingDataset.from_config(**model_config)


# TODO: change the test to check if no model has been created
def test_mlflow_model_tracking_logging_deactivation(mlflow_client, linreg_model):
    mlflow_model_tracking_dataset = MlflowModelTrackingDataset(flavor="mlflow.sklearn")

    mlflow_model_tracking_dataset._logging_activated = False

    all_runs_id_beginning = {
        run.run_id
        for k in range(len(mlflow_client.search_experiments()))
        for run in mlflow_client.search_runs(experiment_ids=f"{k}")
    }

    mlflow_model_tracking_dataset.save(linreg_model)

    all_runs_id_end = {
        run.run_id
        for k in range(len(mlflow_client.search_experiments()))
        for run in mlflow_client.search_runs(experiment_ids=f"{k}")
    }

    assert all_runs_id_beginning == all_runs_id_end


def test_mlflow_model_tracking_logging_deactivation_is_bool():
    mlflow_model_tracking_dataset = MlflowModelTrackingDataset(flavor="mlflow.sklearn")

    with pytest.raises(ValueError, match="_logging_activated must be a boolean"):
        mlflow_model_tracking_dataset._logging_activated = "hello"


@pytest.mark.parametrize(
    "metadata",
    (
        None,
        {"description": "My awsome dataset"},
        {"string": "bbb", "int": 0},
    ),
)
def test_mlflow_model_tracking_dataset_with_metadata(metadata):
    mlflow_model_ds = MlflowModelTrackingDataset(
        flavor="mlflow.sklearn",
        metadata=metadata,
    )

    assert mlflow_model_ds.metadata == metadata

    # Metadata should not show in _describe
    assert "metadata" not in mlflow_model_ds._describe()
