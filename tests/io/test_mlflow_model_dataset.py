import mlflow
import pytest
from kedro.io.core import DataSetError
from mlflow.tracking import MlflowClient
from sklearn.linear_model import LinearRegression

from kedro_mlflow.io import MlflowModelDataSet


@pytest.fixture
def linreg_model():
    return LinearRegression()


@pytest.fixture
def linreg_path(tmp_path):
    return tmp_path / "06_models/linreg"


@pytest.fixture
def mlflow_client_run_id(tmp_path):
    tracking_uri = tmp_path / "mlruns"
    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_client = MlflowClient(tracking_uri=tracking_uri.as_uri())
    mlflow.start_run()
    yield mlflow_client, mlflow.active_run().info.run_id
    mlflow.end_run()


def test_flavor_does_not_exists(linreg_path):
    with pytest.raises(DataSetError):
        MlflowModelDataSet.from_config(
            name="whoops",
            config={
                "type": "kedro_mlflow.io.MlflowModelDataSet",
                "flavor": "mlflow.whoops",
                "path": linreg_path,
            },
        )


def test_save_unversioned_under_same_path(
    linreg_path, linreg_model, mlflow_client_run_id
):
    model_config = {
        "name": "linreg",
        "config": {
            "type": "kedro_mlflow.io.MlflowModelDataSet",
            "flavor": "mlflow.sklearn",
            "path": linreg_path,
        },
    }
    mlflow_model_ds = MlflowModelDataSet.from_config(**model_config)
    mlflow_model_ds.save(linreg_model)
    mlflow_model_ds.save(linreg_model)


@pytest.mark.parametrize(
    "versioned,from_run_id",
    [(False, False), (True, False), (False, True), (True, True)],
)
def test_save_load_local(
    linreg_path, linreg_model, mlflow_client_run_id, versioned, from_run_id
):
    model_config = {
        "name": "linreg",
        "config": {
            "type": "kedro_mlflow.io.MlflowModelDataSet",
            "flavor": "mlflow.sklearn",
            "path": linreg_path,
            "versioned": versioned,
        },
    }
    mlflow_model_ds = MlflowModelDataSet.from_config(**model_config)
    mlflow_model_ds.save(linreg_model)

    if versioned:
        assert (
            linreg_path / mlflow_model_ds._version.save / linreg_path.name
        ).exists(), "Versioned model saved locally"
    else:
        assert linreg_path.exists(), "Unversioned model saved locally"

    mlflow_client, run_id = mlflow_client_run_id
    artifact = mlflow_client.list_artifacts(run_id=run_id)[0]
    versioned_str = "Versioned" if versioned else "Unversioned"
    assert linreg_path.name == artifact.path, f"{versioned_str} model logged to MLflow"

    if from_run_id:
        model_config["config"]["run_id"] = run_id
        mlflow_model_ds = MlflowModelDataSet.from_config(**model_config)

    linreg_model_loaded = mlflow_model_ds.load()
    assert isinstance(
        linreg_model_loaded, LinearRegression
    ), f"{versioned_str} model loaded"
