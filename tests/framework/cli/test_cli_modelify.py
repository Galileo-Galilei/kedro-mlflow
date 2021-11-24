import shutil
from pathlib import Path

import mlflow
import pandas as pd
import pytest
from click.testing import CliRunner
from cookiecutter.main import cookiecutter
from kedro import __version__ as kedro_version
from kedro.framework.cli.starters import TEMPLATE_PATH
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

from kedro_mlflow.config import get_mlflow_config
from kedro_mlflow.framework.cli.cli import (
    modelify as cli_modelify,  # import after changing the path to avoid registering the project, else import pippeliens does not work!
)


def _write_file(filepath, txt):
    filepath.write_text(txt)


@pytest.fixture
def kp_for_modelify(tmp_path):
    # TODO: find a better way to inject dynamically
    # the templated config loader without modifying the template

    config = {
        "output_dir": tmp_path,
        "kedro_version": kedro_version,
        "project_name": "A kedro project with a pipeline for modelify command",
        "repo_name": "kp-for-modelify",  # "kp" for "kedro_project"
        "python_package": "kp_for_modelify",
    }

    cookiecutter(
        str(TEMPLATE_PATH),
        output_dir=config["output_dir"],
        no_input=True,
        extra_context=config,
    )

    shutil.rmtree(
        tmp_path / config["repo_name"] / "src" / "tests"
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
        config["output_dir"] / config["repo_name"] / "data" / "my_model.pkl"
    ).as_posix()

    catalog_yml = f"""
    trained_model:
        type: pickle.PickleDataSet
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
        type: pickle.PickleDataSet
        filepath: {model_filepath}
    my_input_data:
        type: pickle.PickleDataSet
        filepath: {data_filepath}
    """

    _write_file(
        kp_for_modelify / "conf" / "base" / "catalog.yml",
        catalog_yml,
    )
    return kp_for_modelify


def test_modelify_logs_in_mlflow(monkeypatch, kp_for_modelify):
    monkeypatch.chdir(kp_for_modelify)

    bootstrap_project(Path().cwd())
    with KedroSession.create(project_path=Path().cwd()) as session:
        mlflow_config = get_mlflow_config()
        mlflow_config.setup()
        context = session.load_context()
        catalog = context.catalog
        catalog.save("trained_model", 2)

    runs_list_before_cmd = mlflow_config.server._mlflow_client.list_run_infos(
        mlflow_config.tracking.experiment._experiment.experiment_id
    )
    cli_runner = CliRunner()

    result = cli_runner.invoke(
        cli_modelify,
        ["--pipeline", "inference", "--input-name", "my_input_data"],
        catch_exceptions=True,
    )

    runs_list_after_cmd = mlflow_config.server._mlflow_client.list_run_infos(
        mlflow_config.tracking.experiment._experiment.experiment_id
    )

    assert result.exit_code == 0
    assert (
        "The data_set 'trained_model' is added to the Pipeline catalog" in result.output
    )
    assert "Model successfully logged" in result.output
    assert len(runs_list_after_cmd) - len(runs_list_before_cmd) == 1
    # TODO: check a new mlflow run was created


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
        mlflow_config = get_mlflow_config()
        mlflow_config.setup()
        context = session.load_context()
        catalog = context.catalog
        catalog.save("trained_model", 2)

    runs_id_set_before_cmd = set(
        [
            run_info.run_id
            for run_info in mlflow_config.server._mlflow_client.list_run_infos(
                mlflow_config.tracking.experiment._experiment.experiment_id
            )
        ]
    )

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
    runs_id_set_after_cmd = set(
        [
            run_info.run_id
            for run_info in mlflow_config.server._mlflow_client.list_run_infos(
                mlflow_config.tracking.experiment._experiment.experiment_id
            )
        ]
    )

    new_run_id = runs_id_set_after_cmd - runs_id_set_before_cmd

    assert result.exit_code == 0
    assert "my_new_model" in [
        file.path
        for file in mlflow_config.server._mlflow_client.list_artifacts(
            list(new_run_id)[0]
        )
    ]


def test_modelify_with_infer_signature_arg(
    monkeypatch, kp_for_modelify_persistent_input
):

    monkeypatch.chdir(kp_for_modelify_persistent_input)

    cli_runner = CliRunner()

    bootstrap_project(Path().cwd())
    my_input_data = pd.DataFrame({"col_int": [1, 2, 3], "col_str": ["a", "b", "c"]})
    with KedroSession.create() as session:
        mlflow_config = get_mlflow_config()
        mlflow_config.setup()
        context = session.load_context()
        catalog = context.catalog
        catalog.save("trained_model", 2)
        catalog.save("my_input_data", my_input_data)

    runs_id_set_before_cmd = set(
        [
            run_info.run_id
            for run_info in mlflow_config.server._mlflow_client.list_run_infos(
                mlflow_config.tracking.experiment._experiment.experiment_id
            )
        ]
    )

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

    runs_id_set_after_cmd = set(
        [
            run_info.run_id
            for run_info in mlflow_config.server._mlflow_client.list_run_infos(
                mlflow_config.tracking.experiment._experiment.experiment_id
            )
        ]
    )

    new_run_id = list(runs_id_set_after_cmd - runs_id_set_before_cmd)[0]

    loaded_model = mlflow.pyfunc.load_model(f"runs:/{new_run_id}/model")

    assert loaded_model.metadata.get_input_schema().to_dict() == [
        {"name": "col_int", "type": "long"},
        {"name": "col_str", "type": "string"},
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
        mlflow_config = get_mlflow_config()
        mlflow_config.setup()
        context = session.load_context()
        catalog = context.catalog
        catalog.save("trained_model", 2)
        catalog.save("my_input_data", my_input_data)

    runs_id_set_before_cmd = set(
        [
            run_info.run_id
            for run_info in mlflow_config.server._mlflow_client.list_run_infos(
                mlflow_config.tracking.experiment._experiment.experiment_id
            )
        ]
    )

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

    runs_id_set_after_cmd = set(
        [
            run_info.run_id
            for run_info in mlflow_config.server._mlflow_client.list_run_infos(
                mlflow_config.tracking.experiment._experiment.experiment_id
            )
        ]
    )

    new_run_id = list(runs_id_set_after_cmd - runs_id_set_before_cmd)[0]

    loaded_model = mlflow.pyfunc.load_model(f"runs:/{new_run_id}/model")

    assert loaded_model.metadata.saved_input_example_info == {
        "artifact_path": "input_example.json",
        "pandas_orient": "split",
        "type": "dataframe",
    }
