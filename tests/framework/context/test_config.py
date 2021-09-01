import os

import mlflow
import pytest
import yaml
from deprecation import fail_if_not_removed
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from mlflow.tracking import MlflowClient

from kedro_mlflow.framework.context.config import (
    KedroMlflowConfig,
    KedroMlflowConfigError,
    _validate_opts,
)


@fail_if_not_removed
def test_validate_opts_invalid_option():
    d1 = dict(c=3)
    d2 = dict(a=1, b=2)
    with pytest.raises(
        KedroMlflowConfigError, match="Provided option 'c' is not valid"
    ):
        # error if opts contains keys not in default
        _validate_opts(d1, d2)


@fail_if_not_removed
def test_validate_opts_missing_options():
    d1 = dict(a=4)
    d2 = dict(a=1, b=2)
    # override default when possible with d1 and d2  unmodified (i.e. deepcopied)
    assert _validate_opts(d1, d2) == dict(a=4, b=2)
    assert d1 == dict(a=4)
    assert d2 == dict(a=1, b=2)


@fail_if_not_removed
def test_validate_opts_no_options():
    d1 = None
    d2 = dict(a=1, b=2)
    # override default when possible with d1 and d2 untouched
    assert _validate_opts(d1, d2) == d2
    assert d1 is None
    assert d2 == dict(a=1, b=2)


@fail_if_not_removed
def test_kedro_mlflow_config_init_wrong_path(tmp_path):
    # create a ".kedro.yml" file to identify "tmp_path" as the root of a kedro project
    with pytest.raises(
        KedroMlflowConfigError, match="not a valid path to a kedro project"
    ):
        KedroMlflowConfig(project_path=tmp_path)


@fail_if_not_removed
def test_kedro_mlflow_config_init(kedro_project_with_mlflow_conf):
    # kedro_project_with_mlflow_conf is a global fixture in conftest

    config = KedroMlflowConfig(project_path=kedro_project_with_mlflow_conf)
    assert config.to_dict() == dict(
        mlflow_tracking_uri=(kedro_project_with_mlflow_conf / "mlruns").as_uri(),
        credentials=None,
        disable_tracking=KedroMlflowConfig.DISABLE_TRACKING_OPTS,
        experiments=KedroMlflowConfig.EXPERIMENT_OPTS,
        run=KedroMlflowConfig.RUN_OPTS,
        ui=KedroMlflowConfig.UI_OPTS,
        hooks=dict(node=KedroMlflowConfig.NODE_HOOK_OPTS),
    )


@fail_if_not_removed
def test_kedro_mlflow_config_bad_long_parameters_strategy(
    kedro_project_with_mlflow_conf,
):
    # create a ".kedro.yml" file to identify "tmp_path" as the root of a kedro project
    with pytest.raises(
        KedroMlflowConfigError, match="'long_parameters_strategy' must be one of "
    ):
        KedroMlflowConfig(
            project_path=kedro_project_with_mlflow_conf,
            node_hook_opts=dict(long_parameters_strategy="does_not_exist"),
        )


@fail_if_not_removed
def test_kedro_mlflow_config_new_experiment_does_not_exists(
    kedro_project_with_mlflow_conf,
):

    config = KedroMlflowConfig(
        project_path=kedro_project_with_mlflow_conf,
        mlflow_tracking_uri="mlruns",
        experiment_opts=dict(name="exp1"),
    )

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        config.setup()

    assert "exp1" in [exp.name for exp in config.mlflow_client.list_experiments()]


@fail_if_not_removed
def test_kedro_mlflow_config_experiment_exists(mocker, kedro_project_with_mlflow_conf):

    # create an experiment with the same name
    mlflow_tracking_uri = (
        kedro_project_with_mlflow_conf / "conf" / "local" / "mlruns"
    ).as_uri()
    MlflowClient(mlflow_tracking_uri).create_experiment("exp1")
    config = KedroMlflowConfig(
        project_path=kedro_project_with_mlflow_conf,
        mlflow_tracking_uri="mlruns",
        experiment_opts=dict(name="exp1"),
    )

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        config.setup()
    assert "exp1" in [exp.name for exp in config.mlflow_client.list_experiments()]


@fail_if_not_removed
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
        experiment_opts=dict(name="exp1"),
    )

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        config.setup()

    assert "exp1" in [exp.name for exp in config.mlflow_client.list_experiments()]


@fail_if_not_removed
def test_kedro_mlflow_config_setup_set_tracking_uri(kedro_project_with_mlflow_conf):

    # create an experiment with the same name and then delete it
    mlflow_tracking_uri = (kedro_project_with_mlflow_conf / "awesome_tracking").as_uri()

    # the config must restore properly the experiment
    config = KedroMlflowConfig(
        project_path=kedro_project_with_mlflow_conf,
        mlflow_tracking_uri="awesome_tracking",
        experiment_opts=dict(name="exp1"),
    )

    bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(project_path=kedro_project_with_mlflow_conf):
        config.setup()

    assert mlflow.get_tracking_uri() == mlflow_tracking_uri


@fail_if_not_removed
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


@fail_if_not_removed
def test_kedro_mlflow_config_setup_tracking_priority(kedro_project_with_mlflow_conf):
    """Test if the mlflow_tracking uri set is the one of mlflow.yml
    if it also eist in credentials.

    Args:
        mocker ([type]): [description]
        tmp_path ([type]): [description]
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


@fail_if_not_removed
@pytest.mark.parametrize(
    "uri",
    [
        (r"mlruns"),  # relative
        (pytest.lazy_fixture("tmp_path")),  # absolute
        (r"file:///C:/fake/path/mlruns"),  # local uri
    ],
)
def test_kedro_mlflow_config_validate_uri_local(
    mocker, kedro_project_with_mlflow_conf, uri
):
    mocker.patch("mlflow.tracking.MlflowClient", return_value=None)
    mocker.patch(
        "kedro_mlflow.framework.context.config.KedroMlflowConfig._get_or_create_experiment",
        return_value=None,
    )

    config = KedroMlflowConfig(project_path=kedro_project_with_mlflow_conf)
    assert config._validate_uri(uri=uri).startswith(r"file:///")  # relative


@fail_if_not_removed
def test_from_dict_to_dict_idempotent(mocker, kedro_project_with_mlflow_conf):
    mocker.patch("mlflow.tracking.MlflowClient", return_value=None)
    mocker.patch(
        "kedro_mlflow.framework.context.config.KedroMlflowConfig._get_or_create_experiment",
        return_value=None,
    )

    config = KedroMlflowConfig(project_path=kedro_project_with_mlflow_conf)
    original_config_dict = config.to_dict()
    # modify config
    config.from_dict(original_config_dict)
    assert config.to_dict() == original_config_dict
