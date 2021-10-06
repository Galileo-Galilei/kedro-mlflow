from tempfile import TemporaryDirectory

import mlflow
import pandas as pd
import pytest
from kedro.extras.datasets.pickle import PickleDataSet
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline, node
from sklearn.linear_model import LinearRegression

from kedro_mlflow.io.models import MlflowModelSaverDataSet
from kedro_mlflow.mlflow import KedroPipelineModel
from kedro_mlflow.pipeline import pipeline_ml_factory


@pytest.fixture
def linreg_model():
    linreg_model = LinearRegression()
    return linreg_model


@pytest.fixture
def tmp_folder():
    tmp_folder = TemporaryDirectory()
    return tmp_folder


@pytest.fixture
def linreg_path(tmp_path):
    linreg_path = tmp_path / "data" / "06_models" / "linreg"
    return linreg_path


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
            "raw_data": MemoryDataSet(),
            "data": MemoryDataSet(),
            "model": PickleDataSet(
                filepath=(tmp_path / "data" / "06_models" / "model.pkl")
                .resolve()
                .as_posix()
            ),
        }
    )
    dummy_catalog._data_sets["model"].save(2)  # emulate model fitting

    return dummy_catalog


@pytest.fixture
def kedro_pipeline_model(tmp_path, pipeline_ml_obj, dummy_catalog):

    kedro_pipeline_model = KedroPipelineModel(
        pipeline=pipeline_ml_obj,
        catalog=dummy_catalog,
        input_name=pipeline_ml_obj.input_name,
    )

    return kedro_pipeline_model


def test_save_unversioned_under_same_path(
    linreg_path,
    linreg_model,
):
    model_config = {
        "name": "linreg",
        "config": {
            "type": "kedro_mlflow.io.models.MlflowModelSaverDataSet",
            "flavor": "mlflow.sklearn",
            "filepath": linreg_path.as_posix(),
        },
    }
    mlflow_model_ds = MlflowModelSaverDataSet.from_config(**model_config)
    mlflow_model_ds.save(linreg_model)
    # check that second save does not fail
    # this happens if the underlying folder already exists
    mlflow_model_ds.save(linreg_model)


@pytest.mark.parametrize("versioned", [False, True])
def test_save_load_local(linreg_path, linreg_model, versioned):
    model_config = {
        "name": "linreg",
        "config": {
            "type": "kedro_mlflow.io.models.MlflowModelSaverDataSet",
            "filepath": linreg_path.as_posix(),
            "flavor": "mlflow.sklearn",
            "versioned": versioned,
        },
    }
    mlflow_model_ds = MlflowModelSaverDataSet.from_config(**model_config)
    mlflow_model_ds.save(linreg_model)

    if versioned:
        assert (
            linreg_path / mlflow_model_ds._version.save / linreg_path.name
        ).exists()  # Versioned model saved locally
    else:
        assert linreg_path.exists()  # Unversioned model saved locally

    linreg_model_loaded = mlflow_model_ds.load()
    assert isinstance(linreg_model_loaded, LinearRegression)


@pytest.mark.parametrize(
    "pipeline",
    [
        (pytest.lazy_fixture("pipeline_ml_obj")),  # must work for PipelineML
        (pytest.lazy_fixture("pipeline_inference")),  # must work for Pipeline
    ],
)
def test_pyfunc_flavor_python_model_save_and_load(
    tmp_path, tmp_folder, pipeline, dummy_catalog
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
            "type": "kedro_mlflow.io.models.MlflowModelSaverDataSet",
            "filepath": (
                tmp_path / "data" / "06_models" / "my_custom_model"
            ).as_posix(),
            "flavor": "mlflow.pyfunc",
            "pyfunc_workflow": "python_model",
            "save_args": {
                "artifacts": artifacts,
                "conda_env": {"python": "3.7.0", "dependencies": ["kedro==0.16.5"]},
            },
        },
    }

    mlflow_model_ds = MlflowModelSaverDataSet.from_config(**model_config)
    mlflow_model_ds.save(kedro_pipeline_model)

    assert mlflow.active_run() is None

    # close the run, create another dataset and reload
    # (emulate a new "kedro run" with the launch of the )
    loaded_model = mlflow_model_ds.load()

    loaded_model.predict(pd.DataFrame(data=[1], columns=["a"])) == pd.DataFrame(
        data=[2], columns=["a"]
    )
