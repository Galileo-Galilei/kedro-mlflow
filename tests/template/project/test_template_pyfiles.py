import black
import pytest
from click.testing import CliRunner
from flake8.api.legacy import get_style_guide
from isort import SortImports

from kedro_mlflow.framework.cli.cli import TEMPLATE_FOLDER_PATH
from kedro_mlflow.framework.cli.cli_utils import write_jinja_template


@pytest.fixture
def template_runpy(tmp_path):
    # the goal is to discover all potential ".py" files
    # but for now there is only "run.py"
    # # this is rather a safeguard for further add
    raw_template_path = TEMPLATE_FOLDER_PATH / "run.py"
    rendered_template_path = tmp_path / raw_template_path.name
    tags = {
        "project_name": "This is a fake project",
        "python_package": "fake_project",
        "kedro_version": "0.16.0",
    }

    write_jinja_template(
        src=raw_template_path, dst=rendered_template_path, is_cookiecutter=True, **tags
    )
    return rendered_template_path.as_posix()


def test_number_of_templates_py():
    # for now, there is only run.py as a template
    # if new .py templates are added, a fixture must be created
    # and it must be added to pytest.mark.parametrize for
    # black, flake8 and isort tests
    assert len(list(TEMPLATE_FOLDER_PATH.glob("**/*.py"))) == 1


@pytest.mark.parametrize("python_file", [(pytest.lazy_fixture("template_runpy"))])
def test_check_black(python_file):
    cli_runner = CliRunner()
    result_black = cli_runner.invoke(black.main, python_file)
    assert "1 file left unchanged" in result_black.output


@pytest.mark.parametrize("python_file", [(pytest.lazy_fixture("template_runpy"))])
def test_check_flake8(python_file):
    style_guide = get_style_guide()
    report = style_guide.check_files([python_file])
    assert len(report.get_statistics("E")) == 0  # no errors must be found


@pytest.mark.parametrize("python_file", [(pytest.lazy_fixture("template_runpy"))])
def test_check_isort(python_file):
    result_isort = SortImports(python_file)
    result_isort.output
