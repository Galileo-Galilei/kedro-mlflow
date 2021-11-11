import os

import mlflow
import pytest
import yaml
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from mlflow.tracking import MlflowClient

from kedro_mlflow.config.kedro_mlflow_config import (
    KedroMlflowConfig,
    KedroMlflowConfigError,
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
        server=dict(
            mlflow_tracking_uri=(kedro_project_with_mlflow_conf / "mlruns").as_uri(),
            stores_environment_variables={},
            credentials=None,
        ),
        tracking=dict(
            disable_tracking=dict(pipelines=[]),
            experiment=dict(name="Default", restore_if_deleted=True),
            run=dict(id=None, name=None, nested=True),
            params=dict(
                dict_params=dict(
                    flatten=False,
                    recursive=True,
                    sep=".",
                ),
                long_params_strategy="fail",
            ),
        ),
        ui=dict(port="5000", host="127.0.0.1"),
    )


def test_kedro_mlflow_config_new_experiment_does_not_exists(
    kedro_project_with_mlflow_conf,
):

    config = KedroMlflowConfig(
        project_path=kedro_project_with_mlflow_conf,
        server=dict(mlflow_tracking_uri="mlruns"),
        tracking=dict(experiment=dict(name="exp1")),
    )

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        config.setup()

    assert "exp1" in [
        exp.name for exp in config.server._mlflow_client.list_experiments()
    ]


def test_kedro_mlflow_config_experiment_exists(kedro_project_with_mlflow_conf):

    # create an experiment with the same name
    mlflow_tracking_uri = (
        kedro_project_with_mlflow_conf / "conf" / "local" / "mlruns"
    ).as_uri()
    MlflowClient(mlflow_tracking_uri).create_experiment("exp1")
    config = KedroMlflowConfig(
        project_path=kedro_project_with_mlflow_conf,
        server=dict(mlflow_tracking_uri="mlruns"),
        tracking=dict(experiment=dict(name="exp1")),
    )

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        config.setup()
    assert "exp1" in [
        exp.name for exp in config.server._mlflow_client.list_experiments()
    ]


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
        server=dict(mlflow_tracking_uri="mlruns"),
        tracking=dict(experiment=dict(name="exp1")),
    )

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        config.setup()

    assert "exp1" in [
        exp.name for exp in config.server._mlflow_client.list_experiments()
    ]


def test_kedro_mlflow_config_setup_set_experiment_globally(
    kedro_project_with_mlflow_conf,
):

    mlflow_tracking_uri = (kedro_project_with_mlflow_conf / "mlruns").as_uri()

    # the config must restore properly the experiment
    config = KedroMlflowConfig(
        project_path=kedro_project_with_mlflow_conf,
        server=dict(mlflow_tracking_uri="mlruns"),
        tracking=dict(experiment=dict(name="incredible_exp")),
    )

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        config.setup()

    mlflow_client = MlflowClient(mlflow_tracking_uri)
    runs_list_before_interactive_run = mlflow_client.list_run_infos(
        config.tracking.experiment._experiment.experiment_id
    )

    with mlflow.start_run():
        mlflow.log_param("a", 1)
        my_run_id = mlflow.active_run().info.run_id

    runs_list_after_interactive_run = mlflow_client.list_run_infos(
        config.tracking.experiment._experiment.experiment_id
    )

    assert (
        len(runs_list_after_interactive_run) - len(runs_list_before_interactive_run)
        == 1
    )
    assert runs_list_after_interactive_run[0].run_id == my_run_id


def test_kedro_mlflow_config_setup_set_tracking_uri(kedro_project_with_mlflow_conf):

    mlflow_tracking_uri = (kedro_project_with_mlflow_conf / "awesome_tracking").as_uri()

    config = KedroMlflowConfig(
        project_path=kedro_project_with_mlflow_conf,
        server=dict(mlflow_tracking_uri="awesome_tracking"),
        tracking=dict(experiment=dict(name="exp1")),
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
        project_path=kedro_project_with_mlflow_conf,
        server=dict(credentials="my_mlflow_creds"),
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
        server=dict(
            mlflow_tracking_uri="mlruns1",
            credentials="my_mlflow_creds",
        ),
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

    kmc = KedroMlflowConfig(project_path=kedro_project_with_mlflow_conf)
    assert kmc._validate_uri(uri=uri).startswith(r"file:///")  # relative


def test_kedro_mlflow_config_validate_uri_databricks(kedro_project_with_mlflow_conf):
    # databricks is a reseved keyword which should not be modified
    kmc = KedroMlflowConfig(project_path=kedro_project_with_mlflow_conf)
    config_uri = kmc._validate_uri(uri="databricks")

    assert config_uri == "databricks"


def test_from_dict_to_dict_idempotent(kedro_project_with_mlflow_conf):
    config = KedroMlflowConfig(project_path=kedro_project_with_mlflow_conf)
    original_config_dict = config.dict()
    # modify config
    reloaded_config = KedroMlflowConfig.parse_obj(original_config_dict)
    assert config == reloaded_config
