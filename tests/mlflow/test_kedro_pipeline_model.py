from pathlib import Path
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
def tmp_folder():
    tmp_folder = TemporaryDirectory()
    return tmp_folder


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
def dummy_catalog(tmp_path):
    dummy_catalog = DataCatalog(
        {
            "raw_data": MemoryDataSet(),
            "data": MemoryDataSet(),
            "model": PickleDataSet(
                filepath=(tmp_path / "model.pkl").resolve().as_posix()
            ),
        }
    )
    return dummy_catalog


@pytest.mark.parametrize(
    "copy_mode,expected",
    [
        (None, {"raw_data": None, "data": None, "model": None}),
        ("assign", {"raw_data": "assign", "data": "assign", "model": "assign"}),
        ("deepcopy", {"raw_data": "deepcopy", "data": "deepcopy", "model": "deepcopy"}),
        ({"model": "assign"}, {"raw_data": None, "data": None, "model": "assign"}),
    ],
)
def test_model_packaging_with_copy_mode(
    tmp_path, tmp_folder, pipeline_ml_obj, dummy_catalog, copy_mode, expected
):

    dummy_catalog._data_sets["model"].save(2)  # emulate model fitting

    artifacts = pipeline_ml_obj.extract_pipeline_artifacts(dummy_catalog, tmp_folder)

    kedro_model = KedroPipelineModel(
        pipeline_ml=pipeline_ml_obj, catalog=dummy_catalog, copy_mode=copy_mode
    )

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    with mlflow.start_run():
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=kedro_model,
            artifacts=artifacts,
            conda_env={"python": "3.7.0", "dependencies": ["kedro==0.16.5"]},
        )
        run_id = mlflow.active_run().info.run_id

    loaded_model = mlflow.pyfunc.load_model(model_uri=f"runs:/{run_id}/model")

    # first assertion: prediction works
    assert loaded_model.predict(1) == 2

    # second assertion: copy_mode works
    actual_copy_mode = {
        name: ds._copy_mode
        for name, ds in loaded_model._model_impl.python_model.loaded_catalog._data_sets.items()
    }

    assert actual_copy_mode == expected


def test_kedro_pipeline_ml_with_wrong_copy_mode_type(pipeline_ml_obj, dummy_catalog):
    with pytest.raises(TypeError, match="'copy_mode' must be a 'str' or a 'dict'"):
        KedroPipelineModel(
            pipeline_ml=pipeline_ml_obj, catalog=dummy_catalog, copy_mode=1346
        )


# should very likely add tests to see what happens when the artifacts
# are incorrect
# incomplete
# contains no input_name
# some memory datasets inside the catalog are persisted?


def test_model_packaging_too_many_artifacts(tmp_path, pipeline_ml_obj):

    catalog = DataCatalog(
        {
            "raw_data": PickleDataSet(
                filepath=(tmp_path / "raw_data.pkl").resolve().as_posix()
            ),
            "data": MemoryDataSet(),
            "model": PickleDataSet(
                filepath=(tmp_path / "model.pkl").resolve().as_posix()
            ),
        }
    )

    catalog._data_sets["raw_data"].save(1)  # emulate input on disk
    catalog._data_sets["model"].save(2)  # emulate model fitting

    # the input is persited
    artifacts = {
        name: Path(dataset._filepath.as_posix())
        .resolve()
        .as_uri()  # weird bug when directly converting PurePosixPath to windows: it is considered as relative
        for name, dataset in catalog._data_sets.items()
        if not isinstance(dataset, MemoryDataSet)
    }

    kedro_model = KedroPipelineModel(pipeline_ml=pipeline_ml_obj, catalog=catalog)

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    with mlflow.start_run():
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=kedro_model,
            artifacts=artifacts,
            conda_env={"python": "3.7.0", "dependencies": ["kedro==0.16.5"]},
        )
        run_id = mlflow.active_run().info.run_id

    with pytest.raises(
        ValueError, match="Provided artifacts do not match catalog entries"
    ):
        mlflow.pyfunc.load_model(
            model_uri=(Path(r"runs:/") / run_id / "model").as_posix()
        )


def test_model_packaging_missing_artifacts(tmp_path, pipeline_ml_obj):

    catalog = DataCatalog(
        {
            "raw_data": MemoryDataSet(),
            "data": MemoryDataSet(),
            "model": PickleDataSet(
                filepath=(tmp_path / "model.pkl").resolve().as_posix()
            ),
        }
    )

    kedro_model = KedroPipelineModel(pipeline_ml=pipeline_ml_obj, catalog=catalog)

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    with mlflow.start_run():
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=kedro_model,
            artifacts=None,  # no artifacts provided
            conda_env={"python": "3.7.0", "dependencies": ["kedro==0.16.5"]},
        )
        run_id = mlflow.active_run().info.run_id

    with pytest.raises(
        ValueError, match="Provided artifacts do not match catalog entries"
    ):
        mlflow.pyfunc.load_model(
            model_uri=(Path(r"runs:/") / run_id / "model").as_posix()
        )


def test_kedro_pipeline_ml_loading_deepcoiable_catalog(tmp_path, tmp_folder):

    # create pipelien and catalog. The training will not be triggered
    def fit_fun(data):
        pass

    def predict_fun(model, data):
        return model.predict(data)

    training_pipeline = Pipeline([node(func=fit_fun, inputs="data", outputs="model")])

    inference_pipeline = Pipeline(
        [
            node(func=predict_fun, inputs=["model", "data"], outputs="predictions"),
        ]
    )

    ml_pipeline = pipeline_ml_factory(
        training=training_pipeline,
        inference=inference_pipeline,
        input_name="data",
    )

    # emulate training by creating the model manually
    model_dataset = MlflowModelSaverDataSet(
        filepath=(tmp_path / "model.pkl").resolve().as_posix(), flavor="mlflow.sklearn"
    )

    data = pd.DataFrame(
        data=[
            [1, 2],
            [3, 4],
        ],
        columns=["a", "b"],
    )
    labels = [4, 6]
    linreg = LinearRegression()
    linreg.fit(data, labels)
    model_dataset.save(linreg)

    # check that mlflow loading is ok
    catalog = DataCatalog({"data": MemoryDataSet(), "model": model_dataset})

    kedro_model = KedroPipelineModel(pipeline_ml=ml_pipeline, catalog=catalog)
    artifacts = ml_pipeline.extract_pipeline_artifacts(catalog, tmp_folder)

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    with mlflow.start_run():
        mlflow.pyfunc.log_model(
            artifact_path="model", python_model=kedro_model, artifacts=artifacts
        )
        run_id = mlflow.active_run().info.run_id

    loaded_model = mlflow.pyfunc.load_model(
        model_uri=(Path(r"runs:/") / run_id / "model").as_posix()
    )
    loaded_model.predict(data) == [4.0, 6.0]
