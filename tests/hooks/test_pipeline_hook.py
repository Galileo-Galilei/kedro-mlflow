import sys

import pytest
import yaml

from kedro_mlflow.hooks.pipeline_hook import _format_conda_env


@pytest.fixture
def python_version():
    return ".".join(
        [
            str(sys.version_info.major),
            str(sys.version_info.minor),
            str(sys.version_info.micro),
        ]
    )


@pytest.fixture
def requirements_path(tmp_path):
    return tmp_path / "requirements.txt"


@pytest.fixture
def requirements_path_str(requirements_path):
    return requirements_path.as_posix()


@pytest.fixture
def environment_path(tmp_path):
    return tmp_path / "environment.yml"


@pytest.fixture
def environment_path_str(environment_path):
    return environment_path.as_posix()


@pytest.fixture
def env_from_none(python_version):
    return dict(python=python_version)


@pytest.fixture
def env_from_requirements(requirements_path, python_version):
    requirements_data = ["pandas>=1.0.0,<2.0.0", "kedro==0.15.9"]
    with open(requirements_path, mode="w") as file_handler:
        for item in requirements_data:
            file_handler.write(f"{item}\n")
    return dict(python=python_version, dependencies=requirements_data)


@pytest.fixture
def env_from_dict(python_version):
    return dict(
        python=python_version, dependencies=["pandas>=1.0.0,<2.0.0", "kedro==0.15.9"]
    )


@pytest.fixture
def env_from_environment(environment_path, env_from_dict):

    with open(environment_path, mode="w") as file_handler:
        yaml.dump(env_from_dict, file_handler)

    return env_from_dict


@pytest.mark.parametrize(
    "conda_env,expected",
    (
        [None, pytest.lazy_fixture("env_from_none")],
        [pytest.lazy_fixture("env_from_dict"), pytest.lazy_fixture("env_from_dict")],
        [
            pytest.lazy_fixture("requirements_path"),
            pytest.lazy_fixture("env_from_requirements"),
        ],
        [
            pytest.lazy_fixture("requirements_path_str"),
            pytest.lazy_fixture("env_from_requirements"),
        ],
        [
            pytest.lazy_fixture("environment_path"),
            pytest.lazy_fixture("env_from_environment"),
        ],
        [
            pytest.lazy_fixture("environment_path_str"),
            pytest.lazy_fixture("env_from_environment"),
        ],
    ),
)
def test_format_conda_env(conda_env, expected):
    conda_env = _format_conda_env(conda_env)
    assert conda_env == expected


def test_format_conda_env_error():
    with pytest.raises(ValueError, match="Invalid conda_env"):
        _format_conda_env(["invalid_list"])
