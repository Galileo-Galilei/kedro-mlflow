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


def test_flavor_does_not_exists():
    with pytest.raises(DatasetError, match="'mlflow.whoops' module not found"):
        MlflowModelTrackingDataset.from_config(
            name="whoops",
            config={
                "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
                "flavor": "mlflow.whoops",
            },
        )


def test_save_sklearn_flavor_with_run_id_and_already_active_run(tracking_uri):
    """This test checks that saving a mlflow dataset must fail
    if a run_id is specified but is different from the
    mlflow.active_run()

    """
    mlflow.set_tracking_uri(tracking_uri)
    # close all opened mlflow runs to avoid interference between tests
    while mlflow.active_run():
        mlflow.end_run()

    mlflow.start_run()
    existing_run_id = mlflow.active_run().info.run_id
    mlflow.end_run()

    artifact_path = "my_linreg"
    model_config = {
        "name": "linreg",
        "config": {
            "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
            "run_id": existing_run_id,
            "artifact_path": artifact_path,
            "flavor": "mlflow.sklearn",
        },
    }
    mlflow_model_ds = MlflowModelTrackingDataset.from_config(**model_config)

    # if a run is active, it is impossible to log in another run
    with mlflow.start_run():
        with pytest.raises(
            DatasetError,
            match="if there is an mlflow active run",
        ):
            mlflow_model_ds.save(linreg_model)


@pytest.mark.parametrize("active_run_when_loading", [False, True])
def test_save_and_load_sklearn_flavor_with_run_id(
    mlflow_client, linreg_model, active_run_when_loading
):
    with mlflow.start_run():
        existing_run_id = mlflow.active_run().info.run_id

    artifact_path = "my_linreg"
    model_config = {
        "name": "linreg",
        "config": {
            "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
            "run_id": existing_run_id,
            "artifact_path": artifact_path,
            "flavor": "mlflow.sklearn",
        },
    }
    mlflow_model_ds = MlflowModelTrackingDataset.from_config(**model_config)

    # "_save" opens, log and close the specified run
    mlflow_model_ds.save(linreg_model)

    mlflow_client.list_artifacts(run_id=existing_run_id)[0]
    artifact = mlflow_client.list_artifacts(run_id=existing_run_id)[0]
    assert artifact.path == artifact_path

    if not active_run_when_loading:
        mlflow.end_run()

    mlflow_model_ds = MlflowModelTrackingDataset.from_config(**model_config)
    linreg_model_loaded = mlflow_model_ds.load()
    assert isinstance(linreg_model_loaded, LinearRegression)
    assert pytest.approx(linreg_model_loaded.predict([[1, 2]])[0], abs=10 ** (-14)) == 5  # noqa: PLR2004


@pytest.mark.parametrize("initial_active_run", [False, True])
def test_save_and_load_sklearn_flavor_without_run_id(
    mlflow_client, linreg_model, initial_active_run
):
    artifact_path = "my_linreg"
    model_config = {
        "name": "linreg",
        "config": {
            "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
            "run_id": None,
            "artifact_path": artifact_path,
            "flavor": "mlflow.sklearn",
        },
    }
    mlflow_model_ds = MlflowModelTrackingDataset.from_config(**model_config)

    # if no initial active run, "_save" triggers the run opening
    if initial_active_run:
        mlflow.start_run()
    mlflow_model_ds.save(linreg_model)
    current_run_id = mlflow.active_run().info.run_id

    mlflow_client.list_artifacts(run_id=current_run_id)[0]
    artifact = mlflow_client.list_artifacts(run_id=current_run_id)[0]
    assert artifact.path == artifact_path

    # the run_id is still opened
    mlflow_model_ds = MlflowModelTrackingDataset.from_config(**model_config)
    linreg_model_loaded = mlflow_model_ds.load()
    assert isinstance(linreg_model_loaded, LinearRegression)
    assert pytest.approx(linreg_model_loaded.predict([[1, 2]])[0], abs=10 ** (-14)) == 5  # noqa: PLR2004

    # load a second time after closing the active_run
    mlflow.end_run()
    model_config2 = model_config.copy()
    model_config2["config"]["run_id"] = current_run_id
    mlflow_model_ds2 = MlflowModelTrackingDataset.from_config(**model_config2)
    linreg_model_loaded2 = mlflow_model_ds2.load()

    assert isinstance(linreg_model_loaded2, LinearRegression)
    assert (
        pytest.approx(linreg_model_loaded2.predict([[1, 2]])[0], abs=10 ** (-14)) == 5  # noqa: PLR2004
    )


def test_load_without_run_id_nor_active_run(tracking_uri):
    mlflow.set_tracking_uri(tracking_uri)
    # close all opened mlflow runs to avoid interference between tests
    while mlflow.active_run():
        mlflow.end_run()

    artifact_path = "my_linreg"
    model_config = {
        "name": "linreg",
        "config": {
            "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
            "run_id": None,
            "artifact_path": artifact_path,
            "flavor": "mlflow.sklearn",
        },
    }
    mlflow_model_ds = MlflowModelTrackingDataset.from_config(**model_config)

    with pytest.raises(
        DatasetError,
        match="To access the model_uri, you must either",
    ):
        mlflow_model_ds.load()


@pytest.mark.parametrize(
    "pipeline",
    [
        (lf("pipeline_ml_obj")),  # must work for PipelineML
        (lf("pipeline_inference")),  # must work for Pipeline
    ],
)
def test_pyfunc_flavor_python_model_save_and_load(
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
            "artifact_path": "test_model",
            "save_args": {
                "artifacts": artifacts,
                "conda_env": {"python": "3.10.0", "dependencies": ["kedro==0.18.11"]},
            },
        },
    }

    mlflow.set_tracking_uri(tracking_uri)
    mlflow_model_ds = MlflowModelTrackingDataset.from_config(**model_config)
    mlflow_model_ds.save(kedro_pipeline_model)
    current_run_id = mlflow.active_run().info.run_id

    # close the run, create another dataset and reload
    # (emulate a new "kedro run" with the launch of the )
    mlflow.end_run()
    model_config2 = model_config.copy()
    model_config2["config"]["run_id"] = current_run_id
    mlflow_model_ds2 = MlflowModelTrackingDataset.from_config(**model_config2)

    loaded_model = mlflow_model_ds2.load()

    loaded_model.predict(pd.DataFrame(data=[1], columns=["a"])) == pd.DataFrame(
        data=[2], columns=["a"]
    )


# TODO: add a test for "pyfunc_workflow=loader_module"


def test_pyfunc_flavor_wrong_pyfunc_workflow(tracking_uri):
    mlflow.set_tracking_uri(tracking_uri)
    model_config = {
        "name": "kedro_pipeline_model",
        "config": {
            "type": "kedro_mlflow.io.models.MlflowModelTrackingDataset",
            "flavor": "mlflow.pyfunc",
            "pyfunc_workflow": "wrong_workflow",
            "artifact_path": "test_model",
        },
    }
    with pytest.raises(
        DatasetError,
        match=r"PyFunc models require specifying `pyfunc_workflow` \(set to either `python_model` or `loader_module`\)",
    ):
        MlflowModelTrackingDataset.from_config(**model_config)


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
def test_metrics_history_dataset_with_metadata(metadata):
    mlflow_model_ds = MlflowModelTrackingDataset(
        flavor="mlflow.sklearn",
        metadata=metadata,
    )

    assert mlflow_model_ds.metadata == metadata

    # Metadata should not show in _describe
    assert "metadata" not in mlflow_model_ds._describe()
