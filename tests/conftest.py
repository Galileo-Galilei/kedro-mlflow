import os
import shutil

import mlflow
import pytest
from cookiecutter.main import cookiecutter
from kedro import __version__ as kedro_version
from kedro.framework.cli.starters import TEMPLATE_PATH
from mlflow import MlflowClient

from kedro_mlflow.framework.cli.cli import TEMPLATE_FOLDER_PATH
from kedro_mlflow.framework.cli.cli_utils import write_jinja_template

_FAKE_PROJECT_NAME = "fake_project"


@pytest.fixture
def tracking_uri(tmp_path):
    tracking_uri = (tmp_path / "mlruns").as_uri()
    return tracking_uri


@pytest.fixture
def mlflow_client(tracking_uri):
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient(tracking_uri)
    return client


@pytest.fixture(autouse=True)
def cleanup_mlflow_after_runs():
    # A test function will be run at this point
    yield
    while mlflow.active_run():
        mlflow.end_run()

    import mlflow.tracking.fluent as mtf

    # if set_experiment has been called before, it stores the experiment_id
    # as a global variable, so if we change the tracking_uri afterwards
    # mlflow is completly lost because the experiment id no longer exists
    # we just reset it after a test, like in a brand new session
    if hasattr(mtf, "_active_experiment_id"):
        mtf._active_experiment_id = None

    if "MLFLOW_TRACKING_URI" in os.environ:
        os.environ.pop("MLFLOW_TRACKING_URI")

    # see https://github.com/kedro-org/kedro/blob/859f98217eed12208a922b771a97cbfb82ba7e80/tests/framework/session/test_session.py#L173


@pytest.fixture
def kedro_project(tmp_path):
    # TODO : this is also an integration test since this depends from the kedro version
    config = {
        # "output_dir": tmp_path,
        "project_name": _FAKE_PROJECT_NAME,
        "repo_name": _FAKE_PROJECT_NAME,
        "python_package": _FAKE_PROJECT_NAME,
        "kedro_version": kedro_version,
        "tools": "['None']",
        "example_pipeline": "False",
    }

    cookiecutter(
        str(TEMPLATE_PATH),
        output_dir=tmp_path,  # config["output_dir"],
        no_input=True,
        extra_context=config,
        accept_hooks=False,
    )

    shutil.rmtree(
        tmp_path / _FAKE_PROJECT_NAME / "tests"
    )  # avoid conflicts with pytest

    return tmp_path / _FAKE_PROJECT_NAME


@pytest.fixture
def kedro_project_with_mlflow_conf(kedro_project):
    write_jinja_template(
        src=TEMPLATE_FOLDER_PATH / "mlflow.yml",
        is_cookiecutter=False,
        dst=kedro_project / "conf" / "local" / "mlflow.yml",
        python_package="fake_project",
    )

    return kedro_project
