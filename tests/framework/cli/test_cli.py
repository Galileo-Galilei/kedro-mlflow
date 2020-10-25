import re
import subprocess

import pytest
from click.testing import CliRunner
from cookiecutter.main import cookiecutter
from kedro import __version__ as kedro_version
from kedro.framework.cli.cli import TEMPLATE_PATH, info

from kedro_mlflow.framework.cli.cli import init as cli_init
from kedro_mlflow.framework.cli.cli import mlflow_commands as cli_mlflow
from kedro_mlflow.framework.cli.cli import ui as cli_ui


@pytest.fixture
def kedro_project(tmp_path):
    # TODO : this is also an integration test since this depends from the kedro version
    config = {
        "output_dir": tmp_path,
        "kedro_version": kedro_version,
        "project_name": "This is a fake project",
        "repo_name": "fake-project",
        "python_package": "fake_project",
        "include_example": True,
    }

    cookiecutter(
        str(TEMPLATE_PATH),
        output_dir=config["output_dir"],
        no_input=True,
        extra_context=config,
    )


def extract_cmd_from_help(msg):
    # [\s\S] is used instead of "." to match any character including new lines
    cmd_txt = re.search((r"(?<=Commands:)([\s\S]+)$"), msg).group(1)
    cmd_list_detailed = cmd_txt.split("\n")
    cmd_list = [
        cmd.strip().split(" ")[0] for cmd in cmd_list_detailed if cmd.strip() != ""
    ]
    return cmd_list


def test_cli_global_discovered(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    cli_runner = CliRunner()
    result = cli_runner.invoke(info)

    assert result.exit_code == 0
    assert "kedro_mlflow" in result.output


# TODO: add a test to check if "kedro mlflow" commmand is discovered
# I can't make it work with cli.invoke
# because discovery mechanisme is linked to setup.py


def test_mlflow_commands_outside_kedro_project(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    cli_runner = CliRunner()
    result = cli_runner.invoke(cli_mlflow)
    assert {"new"} == set(extract_cmd_from_help(result.output))


def test_mlflow_commands_inside_non_initialized_kedro_project(
    mocker, monkeypatch, tmp_path, kedro_project
):
    monkeypatch.chdir(tmp_path / "fake-project")
    cli_runner = CliRunner()
    result = cli_runner.invoke(cli_mlflow)
    assert {"init"} == set(extract_cmd_from_help(result.output))
    assert "You have not updated your template yet" in result.output


def test_mlflow_commands_inside_initialized_kedro_project(
    mocker, monkeypatch, tmp_path, kedro_project
):
    monkeypatch.chdir(tmp_path / "fake-project")
    # launch the command to initialize the project
    subprocess.call(["kedro", "mlflow", "init"])
    cli_runner = CliRunner()
    result = cli_runner.invoke(cli_mlflow)
    assert {"init", "ui"} == set(extract_cmd_from_help(result.output))
    assert "You have not updated your template yet" not in result.output


def test_cli_init(monkeypatch, tmp_path, kedro_project):
    # "kedro_project" is a pytest.fixture declared in conftest
    project_path = tmp_path / "fake-project"
    monkeypatch.chdir(project_path)
    cli_runner = CliRunner()
    result = cli_runner.invoke(cli_init)

    # FIRST TEST:
    # the command should have executed propery
    assert result.exit_code == 0

    # check mlflow.yml file
    assert "'conf/base/mlflow.yml' successfully updated." in result.output
    assert (project_path / "conf" / "base" / "mlflow.yml").is_file()


# TODO : This is a fake test. add a test to see if ui is properly up
# I tried mimicking mlflow_cli with mock but did not achieve desired result
# other solution is to use pytest-xprocess
def test_ui_is_up(monkeypatch, mocker, tmp_path, kedro_project):
    project_path = tmp_path / "fake-project"
    monkeypatch.chdir(project_path)
    cli_runner = CliRunner()
    cli_runner.invoke(cli_init)  # intialize project

    # This does not test anything : the goal is to check whether it raises an error
    ui_mocker = mocker.patch(
        "subprocess.call"
    )  # make the test succeed, but no a real test
    cli_runner.invoke(cli_ui)
    ui_mocker.assert_called_once()

    # OTHER ATTEMPT:
    # try:
    #     import threading
    #     thread = threading.Thread(target=subprocess.call, args=(["kedro", "mlflow", "sqf"],))
    #     thread.start()
    # except Exception as err:
    #     raise err
    # print(thread)
    # assert thread.is_alive()
