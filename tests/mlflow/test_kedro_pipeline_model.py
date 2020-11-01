from pathlib import Path

import mlflow
import pytest
from kedro.extras.datasets.pickle import PickleDataSet
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline, node

from kedro_mlflow.mlflow import KedroPipelineModel
from kedro_mlflow.pipeline import pipeline_ml_factory


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


def test_model_packaging(tmp_path, pipeline_ml_obj):

    catalog = DataCatalog(
        {
            "raw_data": MemoryDataSet(),
            "data": MemoryDataSet(),
            "model": PickleDataSet(
                filepath=(tmp_path / "model.pkl").resolve().as_posix()
            ),
        }
    )

    catalog._data_sets["model"].save(2)  # emulate model fitting

    artifacts = pipeline_ml_obj.extract_pipeline_artifacts(catalog)

    kedro_model = KedroPipelineModel(pipeline_ml=pipeline_ml_obj, catalog=catalog)

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    with mlflow.start_run():
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=kedro_model,
            artifacts=artifacts,
            conda_env={"python": "3.7.0"},
        )
        run_id = mlflow.active_run().info.run_id

    loaded_model = mlflow.pyfunc.load_model(
        model_uri=(Path(r"runs:/") / run_id / "model").as_posix()
    )
    assert loaded_model.predict(1) == 2


# should very likely add tests to see what happens when the artifacts
# are incorrect
# incomplete
# contains to input_name
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
            conda_env={"python": "3.7.0"},
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

    # model not persisted

    kedro_model = KedroPipelineModel(pipeline_ml=pipeline_ml_obj, catalog=catalog)

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    with mlflow.start_run():
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=kedro_model,
            artifacts=None,  # no artifacts provided
            conda_env={"python": "3.7.0"},
        )
        run_id = mlflow.active_run().info.run_id

    with pytest.raises(
        ValueError, match="Provided artifacts do not match catalog entries"
    ):
        mlflow.pyfunc.load_model(
            model_uri=(Path(r"runs:/") / run_id / "model").as_posix()
        )
