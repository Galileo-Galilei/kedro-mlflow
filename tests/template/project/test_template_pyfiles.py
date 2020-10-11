from pathlib import Path

import black
import pytest
from click.testing import CliRunner
from flake8.api.legacy import get_style_guide
from isort import SortImports
from kedro import __file__ as KEDRO_PATH

from kedro_mlflow.framework.cli.cli import TEMPLATE_FOLDER_PATH
from kedro_mlflow.framework.cli.cli_utils import (
    render_jinja_template,
    write_jinja_template,
)


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
    # IMPORTANT : to ensure black will not change the file,
    # we need to keep line 50 on 1 line (and not 2).
    # Black complains in the non-rendered form because the line is too long,
    # but when the file is rendered, the tags are replaced by much shorter names and
    # black wants to force them on the same line.
    # TODO : open an issue to kedro
    cli_runner = CliRunner()
    result_black = cli_runner.invoke(black.main, python_file)
    assert "1 file left unchanged" in result_black.output


@pytest.mark.parametrize("python_file", [(pytest.lazy_fixture("template_runpy"))])
def test_check_flake8(python_file):
    style_guide = get_style_guide()
    report = style_guide.check_files([python_file])
    assert report.total_errors == 0  # no errors must be found


@pytest.mark.parametrize("python_file", [(pytest.lazy_fixture("template_runpy"))])
def test_check_isort(python_file):
    result_isort = SortImports(python_file)
    result_isort.output


def test_runpy_template_is_consistent_with_kedro():
    tags = {
        "project_name": "This is a fake project",
        "python_package": "fake_project",
        "kedro_version": "0.16.0",
    }
    kedro_runpy_path = (
        Path(KEDRO_PATH).parent
        / "templates"
        / "project"
        / "{{ cookiecutter.repo_name }}"
        / "src"
        / "{{ cookiecutter.python_package }}"
        / "run.py"
    )

    kedro_mlflow_runpy = render_jinja_template(
        TEMPLATE_FOLDER_PATH / "run.py", is_cookiecutter=True, **tags
    )
    kedro_runpy = render_jinja_template(kedro_runpy_path, is_cookiecutter=True, **tags)

    # remove the 2 specific additions for kedro_mlflow
    kedro_mlflow_runpy = kedro_mlflow_runpy.replace(
        "from kedro_mlflow.framework.hooks import MlflowNodeHook, MlflowPipelineHook\n\n",
        "",
    )
    kedro_mlflow_runpy = kedro_mlflow_runpy.replace(
        "    hooks = (\n        MlflowNodeHook(),\n        MlflowPipelineHook(),\n    )\n",
        "",
    )

    # remove wrong black linting in current (0.16.1) kedro version
    # TODO: open an issue to kedro and remove this once the correction is made
    # this was fixed in kedro==0.16.3!
    # kedro_runpy = kedro_runpy.replace(
    #     "\n        package_name=Path(__file__).resolve().parent.name",
    #     " package_name=Path(__file__).resolve().parent.name",
    # )

    assert kedro_mlflow_runpy == kedro_runpy
