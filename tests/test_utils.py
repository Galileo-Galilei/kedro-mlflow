from pathlib import Path

import pytest

from kedro_mlflow.utils import (
    KEDRO_VERSION,
    _get_project_globals,
    _is_kedro_project,
    _parse_requirements,
    _read_kedro_yml,
    _validate_project_path,
)


def test_read_kedro_yml(tmp_path, config_dir):

    kedro_yml_dict = _read_kedro_yml(tmp_path)
    expected_kedro_yml_dict = {
        "context_path": "dummy_package.run.ProjectContext",
        "project_name": "dummy_package",
        "project_version": "0.16.5",
        "package_name": "dummy_package",
    }

    assert kedro_yml_dict == expected_kedro_yml_dict


@pytest.mark.parametrize(
    "project_path,project_path_expected",
    (
        [None, Path().cwd()],
        [pytest.lazy_fixture("tmp_path"), pytest.lazy_fixture("tmp_path")],
    ),
)
def test_validate_project_path(project_path, project_path_expected):

    project_path_result = _validate_project_path(project_path)
    assert project_path_result == project_path_expected


@pytest.mark.parametrize(
    "project,is_kedro_project",
    (
        [pytest.lazy_fixture("tmp_path"), False],
        [pytest.lazy_fixture("config_dir"), True],
    ),
)
def test_is_kedro_project(project, is_kedro_project, tmp_path):

    flag = _is_kedro_project(tmp_path)
    assert flag == is_kedro_project


def test_get_project_globals(tmp_path, config_dir):

    project_globals = _get_project_globals(tmp_path)

    expected_project_globals = {
        "context_path": "dummy_package/run/ProjectContext",
        "project_name": "dummy_package",
        "package_name": "dummy_package",
        "kedro_version": KEDRO_VERSION,
    }

    assert project_globals == expected_project_globals


def test_parse_requirements(tmp_path):

    with open(tmp_path / "requirements.txt", "w") as f:
        f.writelines(["kedro==0.16.5\n", " mlflow==1.11.0\n" "-r pandas\n"])

    requirements = _parse_requirements(tmp_path / "requirements.txt")
    expected_requirements = ["kedro==0.16.5", "mlflow==1.11.0"]

    assert requirements == expected_requirements
