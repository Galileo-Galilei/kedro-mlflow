import pytest
import yaml
from mlflow.tracking import MlflowClient

from kedro_mlflow.framework.context.config import (
    KedroMlflowConfig,
    KedroMlflowConfigError,
    _validate_opts,
)


def test_validate_opts_invalid_option():
    d1 = dict(c=3)
    d2 = dict(a=1, b=2)
    with pytest.raises(
        KedroMlflowConfigError, match="Provided option 'c' is not valid"
    ):
        # error if opts contains keys not in default
        _validate_opts(d1, d2)


def test_validate_opts_missing_options():
    d1 = dict(a=4)
    d2 = dict(a=1, b=2)
    # override default when possible with d1 and d2  unmodified (i.e. deepcopied)
    assert _validate_opts(d1, d2) == dict(a=4, b=2)
    assert d1 == dict(a=4)
    assert d2 == dict(a=1, b=2)


def test_validate_opts_no_options():
    d1 = None
    d2 = dict(a=1, b=2)
    # override default when possible with d1 and d2 untouched
    assert _validate_opts(d1, d2) == d2
    assert d1 is None
    assert d2 == dict(a=1, b=2)


def test_kedro_mlflow_config_init_wrong_path(tmp_path):
    # create a ".kedro.yml" file to identify "tmp_path" as the root of a kedro project
    with pytest.raises(
        KedroMlflowConfigError, match="not a valid path to a kedro project"
    ):
        KedroMlflowConfig(project_path=tmp_path)


def test_kedro_mlflow_config_init(tmp_path):
    # create a ".kedro.yml" file to identify "tmp_path" as the root of a kedro project
    (tmp_path / ".kedro.yml").write_text(yaml.dump(dict(context_path="fake/path")))

    config = KedroMlflowConfig(project_path=tmp_path)
    assert config.to_dict() == dict(
        mlflow_tracking_uri=(tmp_path / "mlruns").as_uri(),
        experiments=KedroMlflowConfig.EXPERIMENT_OPTS,
        run=KedroMlflowConfig.RUN_OPTS,
        ui=KedroMlflowConfig.UI_OPTS,
        hooks=dict(node=KedroMlflowConfig.NODE_HOOK_OPTS),
    )


def test_kedro_mlflow_config_new_experiment_does_not_exists(mocker, tmp_path):
    # create a ".kedro.yml" file to identify "tmp_path" as the root of a kedro project
    mocker.patch("kedro_mlflow.utils._is_kedro_project", return_value=True)

    config = KedroMlflowConfig(
        project_path=tmp_path,
        mlflow_tracking_uri="mlruns",
        experiment_opts=dict(name="exp1"),
    )
    assert "exp1" in [exp.name for exp in config.mlflow_client.list_experiments()]


def test_kedro_mlflow_config_experiment_exists(mocker, tmp_path):
    # create a ".kedro.yml" file to identify "tmp_path" as the root of a kedro project
    mocker.patch("kedro_mlflow.utils._is_kedro_project", return_value=True)

    # create an experiment with the same name
    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    MlflowClient(mlflow_tracking_uri).create_experiment("exp1")
    config = KedroMlflowConfig(
        project_path=tmp_path,
        mlflow_tracking_uri="mlruns",
        experiment_opts=dict(name="exp1"),
    )
    assert "exp1" in [exp.name for exp in config.mlflow_client.list_experiments()]


def test_kedro_mlflow_config_experiment_was_deleted(mocker, tmp_path):
    # create a ".kedro.yml" file to identify "tmp_path" as the root of a kedro project
    mocker.patch("kedro_mlflow.utils._is_kedro_project", lambda x: True)

    # create an experiment with the same name and then delete it
    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow_client = MlflowClient(mlflow_tracking_uri)
    mlflow_client.create_experiment("exp1")
    mlflow_client.delete_experiment(
        mlflow_client.get_experiment_by_name("exp1").experiment_id
    )

    # the config must restore properly the experiment
    config = KedroMlflowConfig(
        project_path=tmp_path,
        mlflow_tracking_uri="mlruns",
        experiment_opts=dict(name="exp1"),
    )
    assert "exp1" in [exp.name for exp in config.mlflow_client.list_experiments()]


@pytest.mark.parametrize(
    "uri",
    [
        (r"mlruns"),  # relative
        (pytest.lazy_fixture("tmp_path")),  # absolute
        (r"file:///C:/fake/path/mlruns"),  # local uri
    ],
)
def test_kedro_mlflow_config_validate_uri_local(mocker, tmp_path, uri):
    mocker.patch("kedro_mlflow.utils._is_kedro_project", return_value=True)
    mocker.patch("mlflow.tracking.MlflowClient", return_value=None)
    mocker.patch(
        "kedro_mlflow.framework.context.config.KedroMlflowConfig._get_or_create_experiment",
        return_value=None,
    )

    config = KedroMlflowConfig(project_path=tmp_path)
    assert config._validate_uri(uri=uri).startswith(r"file:///")  # relative


def test_from_dict_to_dict_idempotent(mocker, tmp_path):
    mocker.patch("kedro_mlflow.utils._is_kedro_project", return_value=True)
    mocker.patch("mlflow.tracking.MlflowClient", return_value=None)
    mocker.patch(
        "kedro_mlflow.framework.context.config.KedroMlflowConfig._get_or_create_experiment",
        return_value=None,
    )

    config = KedroMlflowConfig(project_path=tmp_path)
    original_config_dict = config.to_dict()
    # modify config
    config.from_dict(original_config_dict)
    assert config.to_dict() == original_config_dict
