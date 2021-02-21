import subprocess
from pathlib import Path

import click
from kedro.framework.context import load_context

from kedro_mlflow.framework.cli.cli_utils import write_jinja_template
from kedro_mlflow.framework.context import get_mlflow_config
from kedro_mlflow.utils import _is_kedro_project

try:
    from kedro.framework.context import get_static_project_data
except ImportError:  # pragma: no cover
    from kedro_mlflow.utils import (
        _get_project_globals as get_static_project_data,  # pragma: no cover
    )


TEMPLATE_FOLDER_PATH = Path(__file__).parent.parent.parent / "template" / "project"


class KedroClickGroup(click.Group):
    def reset_commands(self):
        self.commands = {}

        # add commands on the fly based on conditions
        if _is_kedro_project():
            self.add_command(init)
            self.add_command(ui)
            # self.add_command(run) # TODO : IMPLEMENT THIS FUNCTION
        else:
            self.add_command(new)

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
    help="Update the template without any checks. If a 'mlflow.yml' already eists, it will be overridden.",
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
    Running this command is mandatory to use kedro-mlflow. This
    adds a configuration file used for run parametrization when
    calling "kedro run" command.
    """

    # get constants
    mlflow_yml = "mlflow.yml"
    project_path = Path().cwd()
    project_globals = get_static_project_data(project_path)
    context = load_context(project_path)
    mlflow_yml_path = project_path / context.CONF_ROOT / env / mlflow_yml

    # mlflow.yml is just a static file
    if mlflow_yml_path.is_file() and not force:
        click.secho(
            click.style(
                f"A 'mlflow.yml' already exists at '{mlflow_yml_path}' You can use the ``--force`` option to override it.",
                fg="red",
            )
        )
        return 1
    else:
        try:
            write_jinja_template(
                src=TEMPLATE_FOLDER_PATH / mlflow_yml,
                is_cookiecutter=False,
                dst=mlflow_yml_path,
                python_package=project_globals["package_name"],
            )
        except FileNotFoundError:
            click.secho(
                click.style(
                    f"No env '{env}' found. Please check this folder exists inside '{context.CONF_ROOT}' folder.",
                    fg="red",
                )
            )
            return 1
        if not silent:
            click.secho(
                click.style(
                    f"'{context.CONF_ROOT}/{env}/{mlflow_yml}' successfully updated.",
                    fg="green",
                )
            )
        return 0


@mlflow_commands.command()
@click.option(
    "--env",
    "-e",
    required=False,
    default="local",
    help="The environment within conf folder we want to retrieve.",
)
def ui(env):
    """Opens the mlflow user interface with the
    project-specific settings of mlflow.yml. This interface
    enables to browse and compares runs.

    """

    project_path = Path().cwd()
    context = load_context(project_path=project_path, env=env)
    # the context must contains the self.mlflow attribues with mlflow configuration
    mlflow_conf = get_mlflow_config(context)

    # call mlflow ui with specific options
    # TODO : add more options for ui
    subprocess.call(
        ["mlflow", "ui", "--backend-store-uri", mlflow_conf.mlflow_tracking_uri]
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
