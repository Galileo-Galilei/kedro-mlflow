import pytest
import yaml

from kedro_mlflow.framework.cli.cli import TEMPLATE_FOLDER_PATH
from kedro_mlflow.framework.cli.cli_utils import write_jinja_template
from kedro_mlflow.framework.context.config import KedroMlflowConfig


@pytest.fixture
def template_mlflowyml(tmp_path):
    # the goal is to discover all potential ".py" files
    # but for now there is only "run.py"
    # # this is rather a safeguard for further add
    raw_template_path = TEMPLATE_FOLDER_PATH / "mlflow.yml"
    rendered_template_path = tmp_path / raw_template_path.name
    tags = {
        "project_name": "This is a fake project",
        "python_package": "fake_project",
        "kedro_version": "0.16.0",
    }

    write_jinja_template(src=raw_template_path, dst=rendered_template_path, **tags)
    return rendered_template_path.as_posix()


def test_mlflow_yml_rendering(template_mlflowyml):
    # the mlflow yml file must be consistent with the default in KedroMlflowConfig for readibility
    with open(template_mlflowyml, "r") as file_handler:
        mlflow_config = yaml.load(file_handler)
    expected_config = dict(
        mlflow_tracking_uri="mlruns",
        credentials=None,
        disable_tracking=KedroMlflowConfig.DISABLE_TRACKING_OPTS,
        experiment=KedroMlflowConfig.EXPERIMENT_OPTS,
        ui=KedroMlflowConfig.UI_OPTS,
        run=KedroMlflowConfig.RUN_OPTS,
        hooks=dict(node=KedroMlflowConfig.NODE_HOOK_OPTS),
    )
    expected_config["experiment"]["name"] = "fake_project"  # check for proper rendering
    assert mlflow_config == expected_config
