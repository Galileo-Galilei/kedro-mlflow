import re
import shutil
import subprocess  # noqa: F401

import pytest
import yaml
from click.testing import CliRunner
from cookiecutter.main import cookiecutter
from kedro import __version__ as kedro_version
from kedro.framework.cli.cli import info
from kedro.framework.cli.starters import TEMPLATE_PATH
from kedro.framework.project import _ProjectSettings
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

from kedro_mlflow.config.kedro_mlflow_config import KedroMlflowConfig
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


@pytest.fixture(autouse=True)
def mock_validate_settings(mocker):
    # KedroSession eagerly validates that a project's settings.py is correct by
    # importing it. settings.py does not actually exists as part of this test suite
    # since we are testing session in isolation, so the validation is patched.
    mocker.patch("kedro.framework.session.session.validate_settings")


def _mock_imported_settings_paths(mocker, mock_settings):
    for path in [
        "kedro.framework.project.settings",
        "kedro.framework.session.session.settings",
    ]:
        mocker.patch(path, mock_settings)
    return mock_settings


@pytest.fixture
def mock_settings_fake_project(mocker):
    return _mock_imported_settings_paths(mocker, _ProjectSettings())


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


def test_cli_init_existing_config(
    monkeypatch, kedro_project_with_mlflow_conf, mock_settings_fake_project
):
    # "kedro_project" is a pytest.fixture declared in conftest
    cli_runner = CliRunner()
    monkeypatch.chdir(kedro_project_with_mlflow_conf)
    bootstrap_project(kedro_project_with_mlflow_conf)

    with KedroSession.create(
        "fake_project", project_path=kedro_project_with_mlflow_conf
    ) as session:
        # emulate first call by writing a mlflow.yml file
        yaml_str = yaml.dump(dict(server=dict(mlflow_tracking_uri="toto")))
        (
            kedro_project_with_mlflow_conf
            / mock_settings_fake_project.CONF_SOURCE
            / "local"
            / "mlflow.yml"
        ).write_text(yaml_str)

        result = cli_runner.invoke(cli_init)

        # check an error message is raised
        assert "A 'mlflow.yml' already exists" in result.output

        context = session.load_context()
        # check the file remains unmodified
        assert context.mlflow.server.mlflow_tracking_uri.endswith("toto")


def test_cli_init_existing_config_force_option(
    monkeypatch, kedro_project, mock_settings_fake_project
):
    # "kedro_project" is a pytest.fixture declared in conftest
    monkeypatch.chdir(kedro_project)
    cli_runner = CliRunner()

    bootstrap_project(kedro_project)
    with KedroSession.create(project_path=kedro_project) as session:

        # emulate first call by writing a mlflow.yml file
        yaml_str = yaml.dump(dict(server=dict(mlflow_tracking_uri="toto")))
        (
            kedro_project
            / mock_settings_fake_project.CONF_SOURCE
            / "local"
            / "mlflow.yml"
        ).write_text(yaml_str)

        result = cli_runner.invoke(cli_init, args="--force")

        # check an error message is raised
        assert "successfully updated" in result.output

        # check the file remains unmodified
        context = session.load_context()
        assert context.mlflow.server.mlflow_tracking_uri.endswith("mlruns")


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


def test_ui_open_http_uri(monkeypatch, mocker, tmp_path):

    config = {
        "output_dir": tmp_path,
        "kedro_version": kedro_version,
        "project_name": "This is a fake project",
        "repo_name": "fake-project-with-http-uri",
        "python_package": "fake_project_with_http_uri",
        "include_example": True,
    }

    cookiecutter(
        str(TEMPLATE_PATH),
        output_dir=config["output_dir"],
        no_input=True,
        extra_context=config,
    )

    project_path = tmp_path / config["repo_name"]
    shutil.rmtree(project_path / "src" / "tests")  # avoid conflicts with pytest

    mlflow_config = KedroMlflowConfig(
        server=dict(mlflow_tracking_uri="http://google.com")
    )

    with open(
        (project_path / "conf" / "local" / "mlflow.yml").as_posix(), "w"
    ) as fhandler:
        yaml.dump(
            mlflow_config.dict(),
            fhandler,
            default_flow_style=False,
        )

    monkeypatch.chdir(project_path.as_posix())
    cli_runner = CliRunner()

    # This does not test anything : the goal is to check whether it raises an error
    # context_mocker = mocker.patch(
    #     "kedro.framework.session.session.KedroSession.load_context"
    # )
    mocker.patch("kedro_mlflow.config.kedro_mlflow_config.KedroMlflowConfig.setup")
    open_mocker = mocker.patch(
        "webbrowser.open"
    )  # make the test succeed, but no a real test
    cli_runner.invoke(
        cli_ui
    )  # result=cli_runner.invoke(cli_ui); print(result.exception) to debug

    open_mocker.assert_called_once()
