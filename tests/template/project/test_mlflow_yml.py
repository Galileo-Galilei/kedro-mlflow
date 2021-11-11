import pytest
import yaml

from kedro_mlflow.config.kedro_mlflow_config import KedroMlflowConfig
from kedro_mlflow.framework.cli.cli import TEMPLATE_FOLDER_PATH
from kedro_mlflow.framework.cli.cli_utils import write_jinja_template


@pytest.fixture
def template_mlflowyml(tmp_path):
    # the goal is to discover all potential ".py" files
    # but for now there is only "run.py"
    # this is rather a safeguard for further add
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

    # note: Using Pydantic model Construct method skip all validations
    # and here we do not want to check the path
    expected_config = KedroMlflowConfig.construct(
        project_path="fake/path",
        tracking=dict(
            disable_tracking=dict(pipelines=[]),
            experiment=dict(name="fake_project", restore_if_deleted=True),
            params=dict(
                dict_params=dict(flatten=False, recursive=True, sep="."),
                long_params_strategy="fail",
            ),
            run=dict(id=None, name=None, nested=True),
        ),  # check for proper rendering
    )

    assert mlflow_config == expected_config.dict(exclude={"project_path"})
