import re

import mlflow
import pytest
from kedro.io.core import DatasetError
from mlflow import MlflowClient
from mlflow import __version__ as mlflow_version
from sklearn.tree import DecisionTreeClassifier

from kedro_mlflow.io.models import MlflowModelRegistryDataset

MLFLOW_VERSION_TUPLE = tuple(
    int(x) for x in re.findall("([0-9]+)\.([0-9]+)\.([0-9]+)", mlflow_version)[0]
)


def test_mlflow_model_registry_save_not_implemented(tmp_path):
    ml_ds = MlflowModelRegistryDataset(model_name="demo_model")
    with pytest.raises(
        DatasetError,
        match=r"The 'save' method is not implemented for MlflowModelRegistryDataset",
    ):
        ml_ds.save(DecisionTreeClassifier())


def test_mlflow_model_registry_alias_and_stage_or_version_fails(tmp_path):
    with pytest.raises(
        DatasetError,
        match=r"You cannot specify 'alias' and 'stage_or_version' simultaneously",
    ):
        MlflowModelRegistryDataset(
            model_name="demo_model", alias="my_alias", stage_or_version="my_stage"
        )


def test_mlflow_model_registry_load_given_stage_or_version(tmp_path, monkeypatch):
    # we must change the working directory because when
    # using mlflow with a local database tracking, the artifacts
    # are stored in a relative mlruns/ folder so we need to have
    # the same working directory that the one of the tracking uri
    monkeypatch.chdir(tmp_path)
    tracking_and_registry_uri = r"sqlite:///" + (tmp_path / "mlruns3.db").as_posix()
    mlflow.set_tracking_uri(tracking_and_registry_uri)
    mlflow.set_registry_uri(tracking_and_registry_uri)

    # setup: we train 3 version of a model under a single
    #  registered model and stage the 2nd one
    runs = {}
    for i in range(3):
        with mlflow.start_run():
            model = DecisionTreeClassifier()
            mlflow.sklearn.log_model(
                model, artifact_path="demo_model", registered_model_name="demo_model"
            )
            runs[i + 1] = mlflow.active_run().info.run_id

    client = MlflowClient(
        tracking_uri=tracking_and_registry_uri, registry_uri=tracking_and_registry_uri
    )
    client.transition_model_version_stage(name="demo_model", version=2, stage="Staging")

    # case 1: no version is provided, we take the last one
    ml_ds = MlflowModelRegistryDataset(model_name="demo_model")
    loaded_model = ml_ds.load()
    assert loaded_model.metadata.run_id == runs[3]

    # case 2: a stage is provided, we take the last model with this stage
    ml_ds = MlflowModelRegistryDataset(
        model_name="demo_model", stage_or_version="staging"
    )
    loaded_model = ml_ds.load()
    assert loaded_model.metadata.run_id == runs[2]

    # case 3: a version is provided, we take the associated model
    ml_ds = MlflowModelRegistryDataset(model_name="demo_model", stage_or_version="1")
    loaded_model = ml_ds.load()
    assert loaded_model.metadata.run_id == runs[1]


@pytest.mark.skipif(
    MLFLOW_VERSION_TUPLE < (2, 9, 0), reason="Requires mlflow 2.9.0 or higher"
)
def test_mlflow_model_registry_load_given_alias(tmp_path, monkeypatch):
    # we must change the working directory because when
    # using mlflow with a local database tracking, the artifacts
    # are stored in a relative mlruns/ folder so we need to have
    # the same working directory that the one of the tracking uri
    monkeypatch.chdir(tmp_path)
    tracking_and_registry_uri = r"sqlite:///" + (tmp_path / "mlruns4.db").as_posix()
    mlflow.set_tracking_uri(tracking_and_registry_uri)
    mlflow.set_registry_uri(tracking_and_registry_uri)

    # setup: we train 3 version of a model under a single
    #  registered model and alias the 2nd one
    runs = {}
    for i in range(2):
        with mlflow.start_run():
            model = DecisionTreeClassifier()
            mlflow.sklearn.log_model(
                model, artifact_path="demo_model", registered_model_name="demo_model"
            )
            runs[i + 1] = mlflow.active_run().info.run_id

    client = MlflowClient(
        tracking_uri=tracking_and_registry_uri, registry_uri=tracking_and_registry_uri
    )
    client.set_registered_model_alias(name="demo_model", alias="champion", version=1)

    # case 2: an alias is provided, we take the last model with this stage
    ml_ds = MlflowModelRegistryDataset(model_name="demo_model", alias="champion")
    loaded_model = ml_ds.load()
    assert loaded_model.metadata.run_id == runs[1]
