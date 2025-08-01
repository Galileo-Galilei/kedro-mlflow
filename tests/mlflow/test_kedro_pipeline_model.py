from pathlib import Path
from tempfile import TemporaryDirectory

import mlflow
import pandas as pd
import pytest
from kedro.io import DataCatalog, DatasetNotFoundError, MemoryDataset
from kedro.pipeline import Pipeline, node
from kedro_datasets.pickle import PickleDataset
from pytest_lazy_fixtures import lf
from sklearn.linear_model import LinearRegression

from kedro_mlflow.io.models import MlflowModelLocalFileSystemDataset
from kedro_mlflow.mlflow import KedroPipelineModel
from kedro_mlflow.mlflow.kedro_pipeline_model import KedroPipelineModelError
from kedro_mlflow.pipeline import pipeline_ml_factory


@pytest.fixture
def tmp_folder():
    tmp_folder = TemporaryDirectory()
    return tmp_folder


def preprocess_fun(data):
    return data


def fit_encoder_fun(data):
    return 4


def apply_encoder_fun(encoder, data):
    return data * encoder


def train_fun(data):
    return 2


def train_fun_hyperparam(data, hyperparam):
    return 2


def predict_fun(model, data):
    return data * model


def predict_fun_with_metric(model, data):
    return data * model, "super_metric"


def predict_fun_return_nothing(model, data):
    pass


def remove_stopwords(data, stopwords):
    return data


def convert_probs_to_pred(data, threshold):
    return (data > threshold) * 1


@pytest.fixture
def pipeline_inference_dummy():
    pipeline_inference_dummy = Pipeline(
        [
            node(
                func=preprocess_fun,
                inputs="raw_data",
                outputs="data",
                tags=["training", "inference"],
            ),
            node(func=predict_fun, inputs=["model", "data"], outputs="predictions"),
        ]
    )
    return pipeline_inference_dummy


@pytest.fixture
def pipeline_inference_with_intermediary_artifacts():
    pipeline_inference_with_intermediary_artifacts = Pipeline(
        [
            node(
                func=preprocess_fun,
                inputs="raw_data",
                outputs="data",
                tags=["training", "inference"],
            ),
            node(
                func=apply_encoder_fun,
                inputs=["encoder", "data"],
                outputs="encoded_data",
                tags=["training", "inference"],
            ),
            node(
                func=predict_fun,
                inputs=["model", "encoded_data"],
                outputs="predictions",
                tags=["inference"],
            ),
        ]
    )
    return pipeline_inference_with_intermediary_artifacts


@pytest.fixture
def pipeline_inference_with_inputs_artifacts():
    pipeline_inference_with_inputs_artifacts = Pipeline(
        [
            node(
                func=remove_stopwords,
                inputs=dict(data="data", stopwords="stopwords_from_nltk"),
                outputs="cleaned_data",
                tags=["training", "inference"],
            ),
            node(
                func=predict_fun,
                inputs=["model", "cleaned_data"],
                outputs="predictions",
                tags=["inference"],
            ),
        ]
    )
    return pipeline_inference_with_inputs_artifacts


@pytest.fixture
def pipeline_inference_with_parameters():
    pipeline_inference_with_parameters = Pipeline(
        [
            # almost the same that previsously but stopwords are parameters
            # this is a shared parameter between inference and training
            node(
                func=remove_stopwords,
                inputs=dict(data="data", stopwords="params:stopwords"),
                outputs="cleaned_data",
                tags=["training", "inference"],
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

    return pipeline_inference_with_parameters


@pytest.fixture
def catalog_with_encoder(tmp_path):
    catalog_with_encoder = DataCatalog(
        {
            "raw_data": MemoryDataset(),
            "data": MemoryDataset(),
            "encoder": PickleDataset(
                filepath=(tmp_path / "encoder.pkl").resolve().as_posix()
            ),
            "model": PickleDataset(
                filepath=(tmp_path / "model.pkl").resolve().as_posix()
            ),
        }
    )
    return catalog_with_encoder


@pytest.fixture
def catalog_with_stopwords(tmp_path):
    catalog_with_stopwords = DataCatalog(
        {
            "data": MemoryDataset(),
            "cleaned_data": MemoryDataset(),
            "stopwords_from_nltk": PickleDataset(
                filepath=(tmp_path / "stopwords.pkl").resolve().as_posix()
            ),
            "model": PickleDataset(
                filepath=(tmp_path / "model.pkl").resolve().as_posix()
            ),
        }
    )
    return catalog_with_stopwords


@pytest.fixture
def catalog_with_parameters(tmp_path):
    catalog_with_parameters = DataCatalog(
        {
            "data": MemoryDataset(),
            "cleaned_data": MemoryDataset(),
            "params:stopwords": MemoryDataset(["Hello", "Hi"]),
            "params:penalty": MemoryDataset(0),
            "model": PickleDataset(
                filepath=(tmp_path / "model.pkl").resolve().as_posix()
            ),
            "params:threshold": MemoryDataset(0.5),
        }
    )
    return catalog_with_parameters


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
            "raw_data": MemoryDataset(),
            "data": MemoryDataset(),
            "model": PickleDataset(
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
    tmp_path, tmp_folder, pipeline_inference_dummy, dummy_catalog, copy_mode, expected
):
    dummy_catalog["model"].save(2)  # emulate model fitting

    kedro_model = KedroPipelineModel(
        pipeline=pipeline_inference_dummy,
        catalog=dummy_catalog,
        copy_mode=copy_mode,
        input_name="raw_data",
    )

    artifacts = kedro_model.extract_pipeline_artifacts(tmp_folder)

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    with mlflow.start_run():
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=kedro_model,
            artifacts=artifacts,
            conda_env={"python": "3.10.0", "dependencies": ["kedro==0.18.11"]},
        )
        run_id = mlflow.active_run().info.run_id

    loaded_model = mlflow.pyfunc.load_model(model_uri=f"runs:/{run_id}/model")

    # first assertion: prediction works
    assert loaded_model.predict(1) == 2  # noqa: PLR2004

    # second assertion: copy_mode works

    actual_copy_mode = {
        name: ds._copy_mode
        for name, ds in loaded_model._model_impl.python_model.loaded_catalog.items()
    }

    assert actual_copy_mode == expected


def test_kedro_pipeline_model_with_wrong_copy_mode_type(
    pipeline_inference_dummy, dummy_catalog
):
    with pytest.raises(TypeError, match="'copy_mode' must be a 'str' or a 'dict'"):
        KedroPipelineModel(
            pipeline=pipeline_inference_dummy,
            catalog=dummy_catalog,
            copy_mode=1346,
            input_name="raw_data",
        )


# should very likely add tests to see what happens when the artifacts
# are incorrect
# incomplete
# contains no input_name
# some memory datasets inside the catalog are persisted?


def test_model_packaging_too_many_artifacts(tmp_path, pipeline_inference_dummy):
    catalog = DataCatalog(
        {
            "raw_data": PickleDataset(
                filepath=(tmp_path / "raw_data.pkl").resolve().as_posix()
            ),
            "data": MemoryDataset(),
            "model": PickleDataset(
                filepath=(tmp_path / "model.pkl").resolve().as_posix()
            ),
        }
    )

    catalog["raw_data"].save(1)  # emulate input on disk
    catalog["model"].save(2)  # emulate model fitting

    # the input is persisted
    artifacts = {
        name: Path(dataset._filepath.as_posix())
        .resolve()
        .as_uri()  # weird bug when directly converting PurePosixPath to windows: it is considered as relative
        for name, dataset in catalog.items()
        if not isinstance(dataset, MemoryDataset)
    }

    kedro_model = KedroPipelineModel(
        pipeline=pipeline_inference_dummy, catalog=catalog, input_name="raw_data"
    )

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    with pytest.raises(
        ValueError, match="Provided artifacts do not match catalog entries"
    ):
        # before mlflow 2.21, this block could be outside the pytest.raises context manager
        # but for mlflow>=2.21, there is a check of the example made at logging time, so
        # the error is raised at logging time instead of loading time
        with mlflow.start_run():
            mlflow.pyfunc.log_model(
                artifact_path="model",
                python_model=kedro_model,
                artifacts=artifacts,
                conda_env={"python": "3.10.0", "dependencies": ["kedro==0.18.11"]},
            )
            run_id = mlflow.active_run().info.run_id
        mlflow.pyfunc.load_model(
            model_uri=(Path(r"runs:/") / run_id / "model").as_posix()
        )


def test_model_packaging_missing_artifacts(tmp_path, pipeline_inference_dummy):
    catalog = DataCatalog(
        {
            "raw_data": MemoryDataset(),
            "data": MemoryDataset(),
            "model": PickleDataset(
                filepath=(tmp_path / "model.pkl").resolve().as_posix()
            ),
        }
    )

    catalog["model"].save(2)  # emulate model fitting

    kedro_model = KedroPipelineModel(
        pipeline=pipeline_inference_dummy, catalog=catalog, input_name="raw_data"
    )

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    with pytest.raises(
        ValueError, match="Provided artifacts do not match catalog entries"
    ):
        # before mlflow 2.21, this block could be outside the pytest.raises context manager
        # but for mlflow>=2.21, there is a check of the example made at logging time, so
        # the error is raised at logging time instead of loading time
        with mlflow.start_run():
            mlflow.pyfunc.log_model(
                artifact_path="model",
                python_model=kedro_model,
                artifacts={
                    "bad_model_name": Path(catalog["model"]._filepath.as_posix())
                    .resolve()
                    .as_uri()
                },  # correct path, but wrong catalog name
                conda_env={"python": "3.10.0", "dependencies": ["kedro==0.18.11"]},
            )
            run_id = mlflow.active_run().info.run_id
        mlflow.pyfunc.load_model(
            model_uri=(Path(r"runs:/") / run_id / "model").as_posix()
        )


def test_kedro_pipeline_ml_loading_deepcopiable_catalog(tmp_path, tmp_folder):
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
    model_dataset = MlflowModelLocalFileSystemDataset(
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
    catalog = DataCatalog({"data": MemoryDataset(), "model": model_dataset})

    kedro_model = KedroPipelineModel(
        pipeline=ml_pipeline, catalog=catalog, input_name=ml_pipeline.input_name
    )
    artifacts = kedro_model.extract_pipeline_artifacts(tmp_folder)

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


# filtering that remove the degree of freedom constraints should fail
@pytest.mark.parametrize(
    "pipeline,catalog,input_name,result",
    [
        (
            lf("pipeline_inference_dummy"),
            lf("dummy_catalog"),
            "raw_data",
            {"raw_data", "model"},
        ),
        (
            lf("pipeline_inference_with_intermediary_artifacts"),
            lf("catalog_with_encoder"),
            "raw_data",
            {"raw_data", "model", "encoder"},
        ),
        (
            lf("pipeline_inference_with_inputs_artifacts"),
            lf("catalog_with_stopwords"),
            "data",
            {"data", "model", "stopwords_from_nltk"},
        ),
        (
            lf("pipeline_inference_with_parameters"),
            lf("catalog_with_parameters"),
            "data",
            {
                "data",
                "model",
                "params:stopwords",
                "params:threshold",
            },
        ),
    ],
)
def test_catalog_extraction(pipeline, catalog, input_name, result):
    kedro_pipeline_model = KedroPipelineModel(
        pipeline=pipeline, catalog=catalog, input_name=input_name
    )
    filtered_catalog = kedro_pipeline_model.initial_catalog
    assert set(filtered_catalog.keys()) == result


def test_catalog_extraction_missing_inference_input(pipeline_inference_dummy):
    catalog = DataCatalog({"raw_data": MemoryDataset(), "data": MemoryDataset()})
    # "model" is missing in the catalog
    with pytest.raises(
        DatasetNotFoundError,
        match="Dataset 'model' not found in the catalog",
    ):
        KedroPipelineModel(
            pipeline=pipeline_inference_dummy,
            catalog=catalog,
            input_name="raw_data",
        )


def test_catalog_extraction_unpersisted_inference_input(pipeline_inference_dummy):
    catalog = DataCatalog(
        {"raw_data": MemoryDataset(), "data": MemoryDataset(), "model": MemoryDataset()}
    )

    # "model" is a MemoryDataset in the catalog
    with pytest.raises(
        KedroPipelineModelError,
        match="The datasets of the training pipeline must be persisted locally",
    ):
        KedroPipelineModel(
            pipeline=pipeline_inference_dummy,
            catalog=catalog,
            input_name="raw_data",
        )


@pytest.mark.parametrize(
    "pipeline,catalog,input_name,result",
    [
        (
            lf("pipeline_inference_dummy"),
            lf("dummy_catalog"),
            "raw_data",
            pd.DataFrame([1, 2, 3]),
        ),
        (
            lf("pipeline_inference_with_intermediary_artifacts"),
            lf("catalog_with_encoder"),
            "raw_data",
            pd.DataFrame([1, 2, 3]),
        ),
        (
            lf("pipeline_inference_with_inputs_artifacts"),
            lf("catalog_with_stopwords"),
            "data",
            pd.DataFrame([1, 2, 3]),
        ),
        (
            lf("pipeline_inference_with_parameters"),
            lf("catalog_with_parameters"),
            "data",
            pd.DataFrame([0, 1, 1]),
        ),
    ],
)
def test_kedro_pipeline_model_save_and_load(
    tmp_path, pipeline, catalog, input_name, result
):
    kedro_pipeline_model = KedroPipelineModel(
        pipeline=pipeline, catalog=catalog, input_name=input_name
    )
    # emulate artifacts persistence
    for ds in catalog.values():
        if hasattr(ds, "_filepath") is not None:
            ds.save(1)

    artifacts = kedro_pipeline_model.extract_pipeline_artifacts(tmp_path)

    with mlflow.start_run():
        mlflow.pyfunc.log_model(
            artifact_path="model",
            python_model=kedro_pipeline_model,
            artifacts=artifacts,
        )
        run_id = mlflow.active_run().info.run_id

    loaded_model = mlflow.pyfunc.load_model(f"runs:/{run_id}/model")

    data = pd.DataFrame([1, 2, 3])

    assert (loaded_model.predict(data) == result).all(axis=None)


def test_kedro_pipeline_model_too_many_outputs():
    catalog = DataCatalog(
        {
            "data": MemoryDataset(),
            "predictions": MemoryDataset(),
            "metrics": MemoryDataset(),
        }
    )

    def predict_and_evaluate(data):
        return 1, 1

    pipeline = Pipeline(
        [
            node(
                func=predict_and_evaluate,
                inputs={"data": "data"},
                outputs=["predictions", "metrics"],
            ),
        ]
    )

    with pytest.raises(ValueError, match="Pipeline must have one and only one output"):
        KedroPipelineModel(pipeline, catalog, input_name="data")
