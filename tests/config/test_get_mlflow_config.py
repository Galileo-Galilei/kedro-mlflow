import pytest
import yaml
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

from kedro_mlflow.config import get_mlflow_config
from kedro_mlflow.config.kedro_mlflow_config import KedroMlflowConfigError


def _write_yaml(filepath, config):
    yaml_str = yaml.dump(config)
    filepath.write_text(yaml_str)


# TODO : reenable this test which is currently failing beacause kedro "import settings"
# is completetly messing up because we have several projects
# and the first import wins


def test_get_mlflow_config(kedro_project):
    # kedro_project is a pytest.fixture in conftest

    _write_yaml(
        kedro_project / "conf" / "local" / "mlflow.yml",
        dict(
            mlflow_tracking_uri="mlruns",
            credentials=None,
            disable_tracking=dict(pipelines=["my_disabled_pipeline"]),
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
        "mlflow_tracking_uri": (kedro_project / "mlruns").as_uri(),
        "credentials": None,
        "disable_tracking": {"pipelines": ["my_disabled_pipeline"]},
        "experiment": {"name": "fake_package", "create": True},
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

    bootstrap_project(kedro_project)
    with KedroSession.create(project_path=kedro_project):
        assert get_mlflow_config().dict(exclude={"project_path"}) == expected


def test_get_mlflow_config_in_uninitialized_project(kedro_project):
    # config_with_base_mlflow_conf is a pytest.fixture in conftest
    with pytest.raises(
        KedroMlflowConfigError, match="No 'mlflow.yml' config file found in environment"
    ):
        bootstrap_project(kedro_project)
        with KedroSession.create(project_path=kedro_project):
            get_mlflow_config()


# TODO : reenable this test which is currently failing beacause kedro "import settings"
# is completetly messing up beacause we have several projects
# and the first import wins


def test_mlflow_config_with_templated_config_loader(
    kedro_project_with_tcl,
):

    _write_yaml(
        kedro_project_with_tcl / "conf" / "local" / "mlflow.yml",
        dict(
            mlflow_tracking_uri="${mlflow_tracking_uri}",
            credentials=None,
            disable_tracking=dict(pipelines=["my_disabled_pipeline"]),
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
        kedro_project_with_tcl / "conf" / "local" / "globals.yml",
        dict(mlflow_tracking_uri="dynamic_mlruns"),
    )

    expected = {
        "mlflow_tracking_uri": (kedro_project_with_tcl / "dynamic_mlruns").as_uri(),
        "credentials": None,
        "disable_tracking": {"pipelines": ["my_disabled_pipeline"]},
        "experiment": {"name": "fake_package", "create": True},
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
    bootstrap_project(kedro_project_with_tcl)
    with KedroSession.create(project_path=kedro_project_with_tcl):
        assert get_mlflow_config().dict(exclude={"project_path"}) == expected
