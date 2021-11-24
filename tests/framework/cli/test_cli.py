import re
import subprocess  # noqa: F401

import pytest
import yaml
from click.testing import CliRunner
from kedro.framework.cli.cli import info
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

from kedro_mlflow.config import get_mlflow_config
from kedro_mlflow.framework.cli.cli import init as cli_init
from kedro_mlflow.framework.cli.cli import mlflow_commands as cli_mlflow
from kedro_mlflow.framework.cli.cli import ui as cli_ui


def extract_cmd_from_help(msg):
    # [\s\S] is used instead of "." to match any character including new lines
    cmd_txt = re.search((r"(?<=Commands:)([\s\S]+)$"), msg).group(1)
    cmd_list_detailed = cmd_txt.split("\n")

    cmd_list = []
    for cmd_detailed in cmd_list_detailed:
        cmd_match = re.search(r"\w+(?=  )", string=cmd_detailed)
        if cmd_match is not None:
            cmd_list.append(cmd_match.group(0))
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


## This command is temporarlily deactivated beacuse of a bug in kedro==0.17.3, see: https://github.com/Galileo-Galilei/kedro-mlflow/issues/193
# def test_mlflow_commands_outside_kedro_project(monkeypatch, tmp_path):
#     monkeypatch.chdir(tmp_path)
#     cli_runner = CliRunner()
#     result = cli_runner.invoke(cli_mlflow)
#     assert {"new"} == set(extract_cmd_from_help(result.output))


def test_mlflow_commands_inside_kedro_project(monkeypatch, kedro_project):
    monkeypatch.chdir(kedro_project)
    # launch the command to initialize the project
    cli_runner = CliRunner()
    result = cli_runner.invoke(cli_mlflow)
    assert {"init", "ui", "modelify"} == set(extract_cmd_from_help(result.output))
    assert "You have not updated your template yet" not in result.output


def test_cli_init(monkeypatch, kedro_project):
    # "kedro_project" is a pytest.fixture declared in conftest
    monkeypatch.chdir(kedro_project)
    cli_runner = CliRunner()
    result = cli_runner.invoke(cli_init)

    # FIRST TEST:
    # the command should have executed propery
    assert result.exit_code == 0

    # check mlflow.yml file
    assert "'conf/local/mlflow.yml' successfully updated." in result.output
    assert (kedro_project / "conf" / "local" / "mlflow.yml").is_file()


def test_cli_init_existing_config(monkeypatch, kedro_project_with_mlflow_conf):
    # "kedro_project" is a pytest.fixture declared in conftest
    cli_runner = CliRunner()
    monkeypatch.chdir(kedro_project_with_mlflow_conf)
    bootstrap_project(kedro_project_with_mlflow_conf)

    with KedroSession.create(
        "fake_project", project_path=kedro_project_with_mlflow_conf
    ) as session:
        context = session.load_context()
        # emulate first call by writing a mlflow.yml file
        yaml_str = yaml.dump(dict(server=dict(mlflow_tracking_uri="toto")))
        (
            kedro_project_with_mlflow_conf / context.CONF_ROOT / "local" / "mlflow.yml"
        ).write_text(yaml_str)

        result = cli_runner.invoke(cli_init)

        # check an error message is raised
        assert "A 'mlflow.yml' already exists" in result.output

        # check the file remains unmodified
        assert get_mlflow_config().server.mlflow_tracking_uri.endswith("toto")


def test_cli_init_existing_config_force_option(monkeypatch, kedro_project):
    # "kedro_project" is a pytest.fixture declared in conftest
    monkeypatch.chdir(kedro_project)
    cli_runner = CliRunner()

    bootstrap_project(kedro_project)
    with KedroSession.create(project_path=kedro_project) as session:
        context = session.load_context()

        # emulate first call by writing a mlflow.yml file
        yaml_str = yaml.dump(dict(mlflow_tracking_uri="toto"))
        (kedro_project / context.CONF_ROOT / "local" / "mlflow.yml").write_text(
            yaml_str
        )

        result = cli_runner.invoke(cli_init, args="--force")

        # check an error message is raised
        assert "successfully updated" in result.output

        # check the file remains unmodified
        assert get_mlflow_config().server.mlflow_tracking_uri.endswith("mlruns")


@pytest.mark.parametrize(
    "env",
    ["base", "local"],
)
def test_cli_init_with_env(monkeypatch, kedro_project, env):
    # "kedro_project" is a pytest.fixture declared in conftest
    monkeypatch.chdir(kedro_project)
    cli_runner = CliRunner()
    result = cli_runner.invoke(cli_init, f"--env {env}")

    # FIRST TEST:
    # the command should have executed propery
    assert result.exit_code == 0

    # check mlflow.yml file
    assert f"'conf/{env}/mlflow.yml' successfully updated." in result.output
    assert (kedro_project / "conf" / env / "mlflow.yml").is_file()


@pytest.mark.parametrize(
    "env",
    ["debug"],
)
def test_cli_init_with_wrong_env(monkeypatch, kedro_project, env):
    # "kedro_project" is a pytest.fixture declared in conftest
    monkeypatch.chdir(kedro_project)
    cli_runner = CliRunner()
    result = cli_runner.invoke(cli_init, f"--env {env}")

    # A warning message should appear
    assert f"No env '{env}' found" in result.output


# TODO : This is a fake test. add a test to see if ui is properly up
# I tried mimicking mlflow_cli with mock but did not achieve desired result
# other solution is to use pytest-xprocess
# TODO: create an initlaized_kedro_project fixture with a global scope
def test_ui_is_up(monkeypatch, mocker, kedro_project_with_mlflow_conf):

    monkeypatch.chdir(kedro_project_with_mlflow_conf)
    cli_runner = CliRunner()

    # This does not test anything : the goal is to check whether it raises an error
    ui_mocker = mocker.patch(
        "subprocess.call"
    )  # make the test succeed, but no a real test
    cli_runner.invoke(cli_ui)
    ui_mocker.assert_called_once_with(
        [
            "mlflow",
            "ui",
            "--backend-store-uri",
            (kedro_project_with_mlflow_conf / "mlruns").as_uri(),
            "--host",
            "127.0.0.1",
            "--port",
            "5000",
        ]
    )

    # OTHER ATTEMPT:
    # try:
    #     import threading
    #     thread = threading.Thread(target=subprocess.call, args=(["kedro", "mlflow", "sqf"],))
    #     thread.start()
    # except Exception as err:
    #     raise err
    # print(thread)
    # assert thread.is_alive()


def test_ui_overwrite_conf_at_runtime(
    monkeypatch, mocker, kedro_project_with_mlflow_conf
):

    monkeypatch.chdir(kedro_project_with_mlflow_conf)
    cli_runner = CliRunner()

    # This does not test anything : the goal is to check whether it raises an error
    ui_mocker = mocker.patch(
        "subprocess.call"
    )  # make the test succeed, but no a real test
    cli_runner.invoke(cli_ui, ["--host", "0.0.0.0", "--port", "5001"])
    ui_mocker.assert_called_once_with(
        [
            "mlflow",
            "ui",
            "--backend-store-uri",
            (kedro_project_with_mlflow_conf / "mlruns").as_uri(),
            "--host",
            "0.0.0.0",
            "--port",
            "5001",
        ]
    )
