import pytest
import yaml
from kedro.framework.context import load_context

from kedro_mlflow.framework.context import get_mlflow_config
from kedro_mlflow.framework.context.config import KedroMlflowConfigError


def _write_yaml(filepath, config):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    yaml_str = yaml.dump(config)
    filepath.write_text(yaml_str)


def test_get_mlflow_config(mocker, tmp_path, config_dir):
    # config_with_base_mlflow_conf is a pytest.fixture in conftest
    mocker.patch("logging.config.dictConfig")
    mocker.patch("kedro_mlflow.utils._is_kedro_project", return_value=True)

    _write_yaml(
        tmp_path / "conf" / "base" / "mlflow.yml",
        dict(
            mlflow_tracking_uri="mlruns",
            credentials=None,
            experiment=dict(name="fake_package", create=True),
            run=dict(id="123456789", name="my_run", nested=True),
            ui=dict(port="5151", host="localhost"),
            hooks=dict(
                node=dict(
                    flatten_dict_params=True,
                    recursive=False,
                    sep="-",
                    long_parameters_strategy="truncate",
                )
            ),
        ),
    )
    expected = {
        "mlflow_tracking_uri": (tmp_path / "mlruns").as_uri(),
        "credentials": None,
        "experiments": {"name": "fake_package", "create": True},
        "run": {"id": "123456789", "name": "my_run", "nested": True},
        "ui": {"port": "5151", "host": "localhost"},
        "hooks": {
            "node": {
                "flatten_dict_params": True,
                "recursive": False,
                "sep": "-",
                "long_parameters_strategy": "truncate",
            }
        },
    }
    context = load_context(tmp_path)
    assert get_mlflow_config(context).to_dict() == expected


def test_get_mlflow_config_in_uninitialized_project(mocker, tmp_path, config_dir):
    # config_with_base_mlflow_conf is a pytest.fixture in conftest
    mocker.patch("logging.config.dictConfig")
    mocker.patch("kedro_mlflow.utils._is_kedro_project", return_value=True)

    context = load_context(tmp_path)
    with pytest.raises(
        KedroMlflowConfigError, match="No 'mlflow.yml' config file found in environment"
    ):
        get_mlflow_config(context)


def test_mlflow_config_with_templated_config(mocker, tmp_path, config_dir):

    _write_yaml(
        tmp_path / "conf" / "base" / "mlflow.yml",
        dict(
            mlflow_tracking_uri="${mlflow_tracking_uri}",
            credentials=None,
            experiment=dict(name="fake_package", create=True),
            run=dict(id="123456789", name="my_run", nested=True),
            ui=dict(port="5151", host="localhost"),
            hooks=dict(
                node=dict(
                    flatten_dict_params=True,
                    recursive=False,
                    sep="-",
                    long_parameters_strategy="truncate",
                )
            ),
        ),
    )

    _write_yaml(
        tmp_path / "conf" / "base" / "globals.yml",
        dict(mlflow_tracking_uri="testruns"),
    )

    expected = {
        "mlflow_tracking_uri": (tmp_path / "testruns").as_uri(),
        "credentials": None,
        "experiments": {"name": "fake_package", "create": True},
        "run": {"id": "123456789", "name": "my_run", "nested": True},
        "ui": {"port": "5151", "host": "localhost"},
        "hooks": {
            "node": {
                "flatten_dict_params": True,
                "recursive": False,
                "sep": "-",
                "long_parameters_strategy": "truncate",
            }
        },
    }

    context = load_context(tmp_path)
    assert get_mlflow_config(context).to_dict() == expected
