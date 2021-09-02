import subprocess
from pathlib import Path

import click
from kedro.framework.session import KedroSession
from kedro.framework.startup import _is_project, bootstrap_project

from kedro_mlflow.config import get_mlflow_config
from kedro_mlflow.framework.cli.cli_utils import write_jinja_template

TEMPLATE_FOLDER_PATH = Path(__file__).parent.parent.parent / "template" / "project"


class KedroClickGroup(click.Group):
    def reset_commands(self):
        self.commands = {}

        # add commands on the fly based on conditions
        if _is_project(Path.cwd()):
            self.add_command(init)
            self.add_command(ui)
            # self.add_command(run) # TODO : IMPLEMENT THIS FUNCTION
        # else:
        #     self.add_command(new) # TODO : IMPLEMENT THIS FUNCTION

    def list_commands(self, ctx):
        self.reset_commands()
        commands_list = sorted(self.commands)
        return commands_list

    def get_command(self, ctx, cmd_name):
        self.reset_commands()
        return self.commands.get(cmd_name)


@click.group(name="Mlflow")
def commands():
    """Kedro plugin for interactions with mlflow."""
    pass  # pragma: no cover


@commands.command(name="mlflow", cls=KedroClickGroup)
def mlflow_commands():
    """Use mlflow-specific commands inside kedro project."""
    pass  # pragma: no cover


@mlflow_commands.command()
@click.option(
    "--env",
    "-e",
    default="local",
    help="The name of the kedro environment where the 'mlflow.yml' should be created. Default to 'local'",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="Update the template without any checks.",
)
@click.option(
    "--silent",
    "-s",
    is_flag=True,
    default=False,
    help="Should message be logged when files are modified?",
)
def init(env, force, silent):
    """Updates the template of a kedro project.
    Running this command is mandatory to use kedro-mlflow.
    This adds "conf/base/mlflow.yml": This is a configuration file
    used for run parametrization when calling "kedro run" command.
    See INSERT_DOC_URL for further details.
    """

    # get constants
    mlflow_yml = "mlflow.yml"
    project_path = Path().cwd()
    project_metadata = bootstrap_project(project_path)
    session = KedroSession.create(project_path=project_path)
    context = session.load_context()
    mlflow_yml_path = project_path / context.CONF_ROOT / env / mlflow_yml

    # mlflow.yml is just a static file,
    # but the name of the experiment is set to be the same as the project
    if mlflow_yml_path.is_file() and not force:
        click.secho(
            click.style(
                f"A 'mlflow.yml' already exists at '{mlflow_yml_path}' You can use the ``--force`` option to override it.",
                fg="red",
            )
        )
    else:
        try:
            write_jinja_template(
                src=TEMPLATE_FOLDER_PATH / mlflow_yml,
                is_cookiecutter=False,
                dst=mlflow_yml_path,
                python_package=project_metadata.package_name,
            )
        except FileNotFoundError:
            click.secho(
                click.style(
                    f"No env '{env}' found. Please check this folder exists inside '{context.CONF_ROOT}' folder.",
                    fg="red",
                )
            )
        if not silent:
            click.secho(
                click.style(
                    f"'{context.CONF_ROOT}/{env}/{mlflow_yml}' successfully updated.",
                    fg="green",
                )
            )


@mlflow_commands.command()
@click.option(
    "--env",
    "-e",
    required=False,
    default="local",
    help="The environment within conf folder we want to retrieve.",
)
@click.option(
    "--port",
    "-p",
    required=False,
    help="The port to listen on",
)
@click.option(
    "--host",
    "-h",
    required=False,
    help="The network address to listen on (default: 127.0.0.1). Use 0.0.0.0 to bind to all addresses if you want to access the tracking server from other machines.",
)
def ui(env, port, host):
    """Opens the mlflow user interface with the
    project-specific settings of mlflow.yml. This interface
    enables to browse and compares runs.
    """

    project_path = Path().cwd()
    bootstrap_project(project_path)
    with KedroSession.create(
        project_path=project_path,
        env=env,
    ):

        mlflow_conf = get_mlflow_config()
        host = host or mlflow_conf.ui.host
        port = port or mlflow_conf.ui.port

        # call mlflow ui with specific options
        # TODO : add more options for ui
        subprocess.call(
            [
                "mlflow",
                "ui",
                "--backend-store-uri",
                mlflow_conf.mlflow_tracking_uri,
                "--host",
                host,
                "--port",
                port,
            ]
        )


@mlflow_commands.command()
def run():
    """Re-run an old run with mlflow-logged info."""

    # TODO (HARD) : define general assumptions to check whether a run
    #  is reproductible or not

    # TODO retrieve command
    # TODO retrieve parameters
    # TODO perform checks on data
    # TODO launch run
    raise NotImplementedError  # pragma: no cover


@mlflow_commands.command()
def new():
    """Create a new kedro project with updated template."""
    raise NotImplementedError  # pragma: no cover


class KedroMlflowCliError(Exception):
    """kedro-mlflow cli specific error"""

    pass
