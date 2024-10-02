import re
import shutil
from pathlib import Path
from platform import python_version

import mlflow
import pandas as pd
import pytest
from click.testing import CliRunner
from cookiecutter.main import cookiecutter
from kedro import __version__ as kedro_version
from kedro.framework.cli.starters import TEMPLATE_PATH
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

from kedro_mlflow.framework.cli.cli import (
    modelify as cli_modelify,  # import after changing the path to avoid registering the project, else import pippeliens does not work!
)


def _write_file(filepath, txt):
    filepath.write_text(txt)


@pytest.fixture
def kp_for_modelify(tmp_path):
    # TODO: find a better way to inject dynamically
    # the templated config loader without modifying the template

    _FAKE_MODELIFY_PROJECT_NAME = r"kp_for_modelify"
    config = {
        # "output_dir": tmp_path,
        "project_name": _FAKE_MODELIFY_PROJECT_NAME,
        "repo_name": _FAKE_MODELIFY_PROJECT_NAME,
        "python_package": _FAKE_MODELIFY_PROJECT_NAME,
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
        tmp_path / _FAKE_MODELIFY_PROJECT_NAME / "tests"
    )  # avoid conflicts with pytest

    pipeline_registry_py = """
from kedro.pipeline import Pipeline, node

def predict_on_new_data(model, data):
    return data

def register_pipelines():
    inference_pipeline = Pipeline(
        [
        node(
            func=predict_on_new_data,
            inputs=dict(
                model="trained_model",
                data="my_input_data"
                ),
            outputs="predictions"
            )
        ]
    )

    return {
        "inference": inference_pipeline,
        "__default__": inference_pipeline,
    }
"""

    model_filepath = (
        tmp_path / config["repo_name"] / "data" / "my_model.pkl"
    ).as_posix()

    catalog_yml = f"""
    trained_model:
        type: pickle.PickleDataset
        filepath: {model_filepath}
    """

    mlflow_yml = """
    server:
        mlflow_tracking_uri: mlruns
    """

    kp_for_modelify = tmp_path / config["repo_name"]

    _write_file(
        kp_for_modelify / "src" / config["python_package"] / "pipeline_registry.py",
        pipeline_registry_py,
    )
    _write_file(
        kp_for_modelify / "conf" / "base" / "catalog.yml",
        catalog_yml,
    )
    _write_file(
        kp_for_modelify / "conf" / "base" / "mlflow.yml",
        mlflow_yml,
    )

    return kp_for_modelify


@pytest.fixture
def kp_for_modelify_persistent_input(kp_for_modelify):
    model_filepath = (kp_for_modelify / "data" / "my_model.pkl").as_posix()
    data_filepath = (kp_for_modelify / "data" / "my_input_data.pkl").as_posix()
    catalog_yml = f"""
    trained_model:
        type: pickle.PickleDataset
        filepath: {model_filepath}
    my_input_data:
        type: pickle.PickleDataset
        filepath: {data_filepath}
    """

    _write_file(
        kp_for_modelify / "conf" / "base" / "catalog.yml",
        catalog_yml,
    )
    return kp_for_modelify


@pytest.fixture
def kp_for_modelify_with_parameters(tmp_path):
    _FAKE_MODELIFY_PROJECT_NAME = r"kp_for_modelify_with_params"
    config = {
        # "output_dir": tmp_path,
        "project_name": _FAKE_MODELIFY_PROJECT_NAME,
        "repo_name": _FAKE_MODELIFY_PROJECT_NAME,
        "python_package": _FAKE_MODELIFY_PROJECT_NAME,
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
        tmp_path / _FAKE_MODELIFY_PROJECT_NAME / "tests"
    )  # avoid conflicts with pytest

    pipeline_registry_py = """
from kedro.pipeline import Pipeline, node

def predict_on_new_data(model, fixed_param, data):
    return data

def register_pipelines():
    inference_pipeline = Pipeline(
        [
        node(
            func=predict_on_new_data,
            inputs=dict(
                model="trained_model",
                fixed_param="params:my_param",
                data="my_input_data"
                ),
            outputs="predictions"
            )
        ]
    )

    return {
        "inference": inference_pipeline,
        "__default__": inference_pipeline,
    }
"""

    model_filepath = (
        tmp_path / config["repo_name"] / "data" / "my_model.pkl"
    ).as_posix()

    catalog_yml = f"""
    trained_model:
        type: pickle.PickleDataset
        filepath: {model_filepath}
    """

    parameters_yml = """
    my_param: 1
    """

    mlflow_yml = """
    server:
        mlflow_tracking_uri: mlruns
    """

    kp_for_modelify_with_parameters = tmp_path / config["repo_name"]

    _write_file(
        kp_for_modelify_with_parameters
        / "src"
        / config["python_package"]
        / "pipeline_registry.py",
        pipeline_registry_py,
    )
    _write_file(
        kp_for_modelify_with_parameters / "conf" / "base" / "catalog.yml",
        catalog_yml,
    )
    _write_file(
        kp_for_modelify_with_parameters / "conf" / "base" / "parameters.yml",
        parameters_yml,
    )
    _write_file(
        kp_for_modelify_with_parameters / "conf" / "base" / "mlflow.yml",
        mlflow_yml,
    )

    return kp_for_modelify_with_parameters


@pytest.mark.parametrize(
    "example_repo,artifacts_list,inside_subdirectory",
    [
        (pytest.lazy_fixture("kp_for_modelify"), ["trained_model"], False),
        (pytest.lazy_fixture("kp_for_modelify"), ["trained_model"], True),
        (
            pytest.lazy_fixture("kp_for_modelify_with_parameters"),
            ["trained_model", "params:my_param"],
            False,
        ),
    ],
)
def test_modelify_logs_in_mlflow_even_inside_subdirectory(
    monkeypatch, example_repo, artifacts_list, inside_subdirectory
):
    if inside_subdirectory is True:
        project_cwd = example_repo / "src"
    else:
        project_cwd = example_repo

    monkeypatch.chdir(project_cwd)

    bootstrap_project(example_repo)
    with KedroSession.create(project_path=example_repo) as session:
        context = session.load_context()
        catalog = context.catalog
        catalog.save("trained_model", 2)

    runs_list_before_cmd = context.mlflow.server._mlflow_client.search_runs(
        context.mlflow.tracking.experiment._experiment.experiment_id
    )
    cli_runner = CliRunner()

    result = cli_runner.invoke(
        cli_modelify,
        ["--pipeline", "inference", "--input-name", "my_input_data"],
        catch_exceptions=True,
    )

    runs_list_after_cmd = context.mlflow.server._mlflow_client.search_runs(
        context.mlflow.tracking.experiment._experiment.experiment_id
    )

    assert result.exit_code == 0
    # parse the log
    stripped_output = re.sub(r"\[.+\]", "", result.output)
    stripped_output = re.sub(
        "(TRACE|DEBUG|INFO|WARNING|ERROR|CRITICAL)", "", stripped_output
    )
    stripped_output = re.sub(r"\w+\.py:\d+", "", stripped_output)
    stripped_output = re.sub(r"[ \n]+", " ", stripped_output)

    for artifact in artifacts_list:
        assert (
            f"The dataset '{artifact}' is added to the Pipeline catalog"
            in stripped_output
        )
    assert "Model successfully logged" in stripped_output
    assert len(runs_list_after_cmd) - len(runs_list_before_cmd) == 1


def test_modelify_informative_error_on_invalid_input_name(monkeypatch, kp_for_modelify):
    monkeypatch.chdir(kp_for_modelify)

    cli_runner = CliRunner()

    result = cli_runner.invoke(
        cli_modelify,
        ["--pipeline", "inference", "--input-name", "invalid_input"],
        catch_exceptions=True,
    )

    assert result.exit_code == 1
    str_error = str(result.exception)
    assert isinstance(result.exception, ValueError)
    assert "'invalid_input' is not a valid 'input_name'" in str_error
    assert "my_input_data" in str_error
    assert "trained_model" in str_error


def test_modelify_with_artifact_path_arg(monkeypatch, kp_for_modelify):
    monkeypatch.chdir(kp_for_modelify)

    cli_runner = CliRunner()

    bootstrap_project(Path().cwd())
    with KedroSession.create() as session:
        context = session.load_context()
        catalog = context.catalog
        catalog.save("trained_model", 2)

    runs_id_set_before_cmd = {
        run.info.run_id
        for run in context.mlflow.server._mlflow_client.search_runs(
            context.mlflow.tracking.experiment._experiment.experiment_id
        )
    }

    result = cli_runner.invoke(
        cli_modelify,
        [
            "--pipeline",
            "inference",
            "--input-name",
            "my_input_data",
            "--artifact-path",
            "my_new_model",
        ],
        catch_exceptions=True,
    )
    runs_id_set_after_cmd = {
        run.info.run_id
        for run in context.mlflow.server._mlflow_client.search_runs(
            context.mlflow.tracking.experiment._experiment.experiment_id
        )
    }

    new_run_id = runs_id_set_after_cmd - runs_id_set_before_cmd

    assert result.exit_code == 0
    assert "my_new_model" in [
        file.path
        for file in context.mlflow.server._mlflow_client.list_artifacts(
            list(new_run_id)[0]
        )
    ]


def test_modelify_with_infer_signature_arg(
    monkeypatch, kp_for_modelify_persistent_input
):
    monkeypatch.chdir(kp_for_modelify_persistent_input)
    monkeypatch.chdir(kp_for_modelify_persistent_input)

    cli_runner = CliRunner()

    bootstrap_project(Path().cwd())
    my_input_data = pd.DataFrame({"col_int": [1, 2, 3], "col_str": ["a", "b", "c"]})
    with KedroSession.create() as session:
        context = session.load_context()
        catalog = context.catalog
        catalog.save("trained_model", 2)
        catalog.save("my_input_data", my_input_data)

    runs_id_set_before_cmd = {
        run.info.run_id
        for run in context.mlflow.server._mlflow_client.search_runs(
            context.mlflow.tracking.experiment._experiment.experiment_id
        )
    }

    result = cli_runner.invoke(
        cli_modelify,
        [
            "--pipeline",
            "inference",
            "--input-name",
            "my_input_data",
            "--infer-signature",
        ],
        catch_exceptions=True,
    )

    assert result.exit_code == 0

    runs_id_set_after_cmd = {
        run.info.run_id
        for run in context.mlflow.server._mlflow_client.search_runs(
            context.mlflow.tracking.experiment._experiment.experiment_id
        )
    }

    new_run_id = list(runs_id_set_after_cmd - runs_id_set_before_cmd)[0]

    loaded_model = mlflow.pyfunc.load_model(f"runs:/{new_run_id}/model")

    assert loaded_model.metadata.get_input_schema().to_dict() == [
        {"name": "col_int", "type": "long", "required": True},
        {"name": "col_str", "type": "string", "required": True},
    ]


@pytest.mark.parametrize(
    "flag_infer_signature",
    [True, False],
)
def test_modelify_with_infer_input_example(
    monkeypatch, kp_for_modelify_persistent_input, flag_infer_signature
):
    monkeypatch.chdir(kp_for_modelify_persistent_input)

    cli_runner = CliRunner()

    bootstrap_project(Path().cwd())
    my_input_data = pd.DataFrame({"col_int": [1, 2, 3], "col_str": ["a", "b", "c"]})
    with KedroSession.create() as session:
        context = session.load_context()
        catalog = context.catalog
        catalog.save("trained_model", 2)
        catalog.save("my_input_data", my_input_data)

    runs_id_set_before_cmd = {
        run.info.run_id
        for run in context.mlflow.server._mlflow_client.search_runs(
            context.mlflow.tracking.experiment._experiment.experiment_id
        )
    }

    cmd = [
        "--pipeline",
        "inference",
        "--input-name",
        "my_input_data",
        "--infer-input-example",
    ]
    if flag_infer_signature:
        cmd.append("--infer-signature")

    result = cli_runner.invoke(
        cli_modelify,
        cmd,
        catch_exceptions=True,
    )

    assert result.exit_code == 0

    runs_id_set_after_cmd = {
        run.info.run_id
        for run in context.mlflow.server._mlflow_client.search_runs(
            context.mlflow.tracking.experiment._experiment.experiment_id
        )
    }

    new_run_id = list(runs_id_set_after_cmd - runs_id_set_before_cmd)[0]

    loaded_model = mlflow.pyfunc.load_model(f"runs:/{new_run_id}/model")

    assert loaded_model.metadata.saved_input_example_info == {
        "artifact_path": "input_example.json",
        "pandas_orient": "split",
        "type": "dataframe",
        "serving_input_path": "serving_input_example.json",
    }


# 3 checks: success with pip requirements, fail with pip_requirements and conda_env, success with no conda_env
def test_modelify_with_pip_requirements(monkeypatch, kp_for_modelify):
    monkeypatch.chdir(kp_for_modelify)

    bootstrap_project(Path().cwd())
    with KedroSession.create(project_path=Path().cwd()) as session:
        context = session.load_context()
        catalog = context.catalog
        catalog.save("trained_model", 2)

    runs_list_before_cmd = context.mlflow.server._mlflow_client.search_runs(
        context.mlflow.tracking.experiment._experiment.experiment_id
    )
    print(runs_list_before_cmd)
    cli_runner = CliRunner()

    result = cli_runner.invoke(
        cli_modelify,
        [
            "--pipeline",
            "inference",
            "--input-name",
            "my_input_data",
            "--pip-requirements",
            "./requirements.txt",
        ],
        catch_exceptions=True,
    )

    runs_list_after_cmd = context.mlflow.server._mlflow_client.search_runs(
        context.mlflow.tracking.experiment._experiment.experiment_id
    )

    assert result.exit_code == 0

    # check if there is a single new run
    run_as_set = set(runs_list_after_cmd) - set(runs_list_before_cmd)
    assert len(run_as_set) == 1
    model_run_id = list(run_as_set)[0].info.run_id

    # retrieve the requirements from the run
    requirements_filepath = mlflow.pyfunc.get_model_dependencies(
        f"runs:/{model_run_id}/model", format="pip"
    )
    assert Path(requirements_filepath).parts[-4:] == (
        model_run_id,
        "artifacts",
        "model",
        "requirements.txt",
    )

    with open(requirements_filepath) as fhandler:
        assert r"kedro" in fhandler.read()


def test_modelify_with_default_conda_env(monkeypatch, kp_for_modelify):
    monkeypatch.chdir(kp_for_modelify)

    bootstrap_project(Path().cwd())
    with KedroSession.create(project_path=Path().cwd()) as session:
        context = session.load_context()
        catalog = context.catalog
        catalog.save("trained_model", 2)

    runs_list_before_cmd = context.mlflow.server._mlflow_client.search_runs(
        context.mlflow.tracking.experiment._experiment.experiment_id
    )
    cli_runner = CliRunner()

    result = cli_runner.invoke(
        cli_modelify,
        [
            "--pipeline",
            "inference",
            "--input-name",
            "my_input_data",
        ],
        catch_exceptions=True,
    )

    runs_list_after_cmd = context.mlflow.server._mlflow_client.search_runs(
        context.mlflow.tracking.experiment._experiment.experiment_id
    )

    assert result.exit_code == 0

    # check if there is a single new run
    run_as_set = set(runs_list_after_cmd) - set(runs_list_before_cmd)
    assert len(run_as_set) == 1
    model_run_id = list(run_as_set)[0].info.run_id

    # retrieve the requirements from the run
    conda_filepath = mlflow.pyfunc.get_model_dependencies(
        f"runs:/{model_run_id}/model", format="conda"
    )

    assert Path(conda_filepath).parts[-4:] == (
        model_run_id,
        "artifacts",
        "model",
        "conda.yaml",
    )

    with open(conda_filepath) as fhandler:
        conda_env = fhandler.read()
        assert f"kedro=={kedro_version}" in conda_env
        assert f"python: {python_version()}" in conda_env


@pytest.mark.parametrize(
    "dependencies_args",
    [
        ["--conda-env", "xxx", "--pip-requirements", "xxx"],
        ["--conda-env", "xxx", "--extra-pip-requirements", "xxx"],
        ["--pip-requirements", "xxx", "--extra-pip-requirements", "xxx"],
        [
            "--conda-env",
            "xxx",
            "--pip-requirements",
            "xxx",
            "--extra-pip-requirements",
            "xxx",
        ],
    ],
)
def test_modelify_fail_with_multiple_requirements(
    monkeypatch, kp_for_modelify, dependencies_args
):
    monkeypatch.chdir(kp_for_modelify)

    bootstrap_project(Path().cwd())
    with KedroSession.create(project_path=Path().cwd()) as session:
        context = session.load_context()
        catalog = context.catalog
        catalog.save("trained_model", 2)

    cli_runner = CliRunner()

    cli_args = [
        "--pipeline",
        "inference",
        "--input-name",
        "my_input_data",
    ] + dependencies_args

    result = cli_runner.invoke(
        cli_modelify,
        cli_args,
        catch_exceptions=True,
    )

    assert result.exit_code == 1
    assert (
        "Only one of `conda_env`, `pip_requirements`, and `extra_pip_requirements` can be specified"
        in str(result.exception)
    )


@pytest.mark.parametrize(
    "arg_run_name,actual_run_name",
    [
        (None, "modelify"),
        ("abcd", "abcd"),
    ],
)
def test_modelify_with_run_name(
    monkeypatch, kp_for_modelify, arg_run_name, actual_run_name
):
    monkeypatch.chdir(kp_for_modelify)

    bootstrap_project(Path().cwd())
    with KedroSession.create(project_path=Path().cwd()) as session:
        context = session.load_context()
        catalog = context.catalog
        catalog.save("trained_model", 2)

    cli_runner = CliRunner()

    cli_args = [
        "--pipeline",
        "inference",
        "--input-name",
        "my_input_data",
    ]

    if arg_run_name is not None:
        cli_args = cli_args + ["--run-name", arg_run_name]

    runs_list_before_cmd = context.mlflow.server._mlflow_client.search_runs(
        context.mlflow.tracking.experiment._experiment.experiment_id
    )

    result = cli_runner.invoke(
        cli_modelify,
        cli_args,
        catch_exceptions=True,
    )

    runs_list_after_cmd = context.mlflow.server._mlflow_client.search_runs(
        context.mlflow.tracking.experiment._experiment.experiment_id
    )

    assert result.exit_code == 0

    # check if there is a single new run
    run_as_set = set(runs_list_after_cmd) - set(runs_list_before_cmd)
    assert len(run_as_set) == 1
    assert list(run_as_set)[0].info.run_name == actual_run_name
