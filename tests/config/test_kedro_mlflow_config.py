import os

import mlflow
import pytest
import yaml
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from mlflow.tracking import MlflowClient

from kedro_mlflow.config.kedro_mlflow_config import (
    DisableTrackingOptions,
    ExperimentOptions,
    HookOptions,
    KedroMlflowConfig,
    KedroMlflowConfigError,
    RunOptions,
    UiOptions,
)


def test_kedro_mlflow_config_init_wrong_path(tmp_path):
    # create a ".kedro.yml" file to identify "tmp_path" as the root of a kedro project
    with pytest.raises(
        KedroMlflowConfigError, match="is not the root of kedro project"
    ):
        KedroMlflowConfig(project_path=tmp_path)


def test_kedro_mlflow_config_init(kedro_project_with_mlflow_conf):
    # kedro_project_with_mlflow_conf is a global fixture in conftest

    config = KedroMlflowConfig(project_path=kedro_project_with_mlflow_conf)
    assert config.dict(exclude={"project_path"}) == dict(
        mlflow_tracking_uri=(kedro_project_with_mlflow_conf / "mlruns").as_uri(),
        credentials=None,
        disable_tracking=DisableTrackingOptions().dict(),
        experiment=ExperimentOptions().dict(),
        run=RunOptions().dict(),
        ui=UiOptions().dict(),
        hooks=HookOptions().dict(),
    )


def test_kedro_mlflow_config_new_experiment_does_not_exists(
    kedro_project_with_mlflow_conf,
):

    config = KedroMlflowConfig(
        project_path=kedro_project_with_mlflow_conf,
        mlflow_tracking_uri="mlruns",
        experiment=dict(name="exp1"),
    )

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        config.setup()

    assert "exp1" in [exp.name for exp in config._mlflow_client.list_experiments()]


def test_kedro_mlflow_config_experiment_exists(mocker, kedro_project_with_mlflow_conf):

    # create an experiment with the same name
    mlflow_tracking_uri = (
        kedro_project_with_mlflow_conf / "conf" / "local" / "mlruns"
    ).as_uri()
    MlflowClient(mlflow_tracking_uri).create_experiment("exp1")
    config = KedroMlflowConfig(
        project_path=kedro_project_with_mlflow_conf,
        mlflow_tracking_uri="mlruns",
        experiment=dict(name="exp1"),
    )

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        config.setup()
    assert "exp1" in [exp.name for exp in config._mlflow_client.list_experiments()]


def test_kedro_mlflow_config_experiment_was_deleted(kedro_project_with_mlflow_conf):

    # create an experiment with the same name and then delete it
    mlflow_tracking_uri = (kedro_project_with_mlflow_conf / "mlruns").as_uri()
    mlflow_client = MlflowClient(mlflow_tracking_uri)
    mlflow_client.create_experiment("exp1")
    mlflow_client.delete_experiment(
        mlflow_client.get_experiment_by_name("exp1").experiment_id
    )

    # the config must restore properly the experiment
    config = KedroMlflowConfig(
        project_path=kedro_project_with_mlflow_conf,
        mlflow_tracking_uri="mlruns",
        experiment=dict(name="exp1"),
    )

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        config.setup()

    assert "exp1" in [exp.name for exp in config._mlflow_client.list_experiments()]


def test_kedro_mlflow_config_setup_set_tracking_uri(kedro_project_with_mlflow_conf):

    # create an experiment with the same name and then delete it
    mlflow_tracking_uri = (kedro_project_with_mlflow_conf / "awesome_tracking").as_uri()

    # the config must restore properly the experiment
    config = KedroMlflowConfig(
        project_path=kedro_project_with_mlflow_conf,
        mlflow_tracking_uri="awesome_tracking",
        experiment=dict(name="exp1"),
    )

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        config.setup()

    assert mlflow.get_tracking_uri() == mlflow_tracking_uri


def test_kedro_mlflow_config_setup_export_credentials(kedro_project_with_mlflow_conf):

    (kedro_project_with_mlflow_conf / "conf/base/credentials.yml").write_text(
        yaml.dump(dict(my_mlflow_creds=dict(fake_mlflow_cred="my_fake_cred")))
    )

    # the config must restore properly the experiment
    config = KedroMlflowConfig(
        project_path=kedro_project_with_mlflow_conf, credentials="my_mlflow_creds"
    )

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        config.setup()

    assert os.environ["fake_mlflow_cred"] == "my_fake_cred"


def test_kedro_mlflow_config_setup_tracking_priority(kedro_project_with_mlflow_conf):
    """Test if the mlflow_tracking uri set is the one of mlflow.yml
    if it also exist in credentials.

    """
    # create a ".kedro.yml" file to identify "tmp_path" as the root of a kedro project

    (kedro_project_with_mlflow_conf / "conf/base/credentials.yml").write_text(
        yaml.dump(dict(my_mlflow_creds=dict(mlflow_tracking_uri="mlruns2")))
    )

    config = KedroMlflowConfig(
        project_path=kedro_project_with_mlflow_conf,
        mlflow_tracking_uri="mlruns1",
        credentials="my_mlflow_creds",
    )

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        config.setup()

    assert (
        mlflow.get_tracking_uri()
        == (kedro_project_with_mlflow_conf / "mlruns1").as_uri()
    )


@pytest.mark.parametrize(
    "uri",
    [
        (r"mlruns"),  # relative
        (pytest.lazy_fixture("tmp_path")),  # absolute
        (r"file:///C:/fake/path/mlruns"),  # local uri
    ],
)
def test_kedro_mlflow_config_validate_uri_local(kedro_project_with_mlflow_conf, uri):

    assert KedroMlflowConfig._validate_uri(
        uri=uri, values={"project_path": kedro_project_with_mlflow_conf}
    ).startswith(
        r"file:///"
    )  # relative


def test_from_dict_to_dict_idempotent(kedro_project_with_mlflow_conf):
    config = KedroMlflowConfig(project_path=kedro_project_with_mlflow_conf)
    original_config_dict = config.dict()
    # modify config
    reloaded_config = KedroMlflowConfig.parse_obj(original_config_dict)
    assert config == reloaded_config
