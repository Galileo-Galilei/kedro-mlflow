import os
import subprocess
from pathlib import Path

import click
from kedro import __file__ as KEDRO_PATH

from kedro_mlflow.framework.cli.cli_utils import (
    render_jinja_template,
    write_jinja_template,
)
from kedro_mlflow.framework.context import get_mlflow_config
from kedro_mlflow.utils import _already_updated, _get_project_globals, _is_kedro_project

TEMPLATE_FOLDER_PATH = Path(__file__).parent.parent.parent / "template" / "project"


class KedroClickGroup(click.Group):
    def reset_commands(self):
        self.commands = {}

        # add commands on the fly based on conditions
        if _is_kedro_project():
            self.add_command(init)
            if _already_updated():
                self.add_command(ui)
                # self.add_command(run) # TODO : IMPLEMENT THIS FUNCTION
        else:
            self.add_command(new)

    def list_commands(self, ctx):
        self.reset_commands()
        commands_list = sorted(self.commands)
        if commands_list == ["init"]:
            click.secho(
                """\n\nYou have not updated your template yet.\nThis is mandatory to use 'kedro-mlflow' plugin.\nPlease run the following command before you can access to other commands :\n\n$ kedro mlflow init""",
                fg="yellow",
            )
        return commands_list

    def get_command(self, ctx, cmd_name):
        self.reset_commands()
        return self.commands.get(cmd_name)


@click.group(name="Mlflow")
def commands():
    """Kedro plugin for interactions with mlflow.
    """
    pass  # pragma: no cover


@commands.command(name="mlflow", cls=KedroClickGroup)
def mlflow_commands():
    """Use mlflow-specific commands inside kedro project.
    """
    pass


@mlflow_commands.command()
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="Update the template without any checks. The modifications you made in 'run.py' will be lost.",
)
@click.option(
    "--silent",
    "-s",
    is_flag=True,
    default=False,
    help="Should message be logged when files are modified?",
)
def init(force, silent):
    """Updates the template of a kedro project.
    Running this command is mandatory to use kedro-mlflow.
    2 actions are performed :
        1. Add "conf/base/mlflow.yml": This is a configuration file
         used for run parametrization when calling "kedro run" command.
         See INSERT_DOC_URL for further details.
        2. Modify "src/YOUR_PACKAGE_NAME/run.py" to add mlflow hooks
         to the ProjectContext. This will erase your current "run.py"
         script and all your modifications will be lost.
         If you do not want to erase "run.py", insert the hooks manually
    """

    # get constants
    project_path = Path().cwd()
    project_globals = _get_project_globals()

    # mlflow.yml is just a static file,
    # but the name of the experiment is set to be the same as the project
    mlflow_yml = "mlflow.yml"
    write_jinja_template(
        src=TEMPLATE_FOLDER_PATH / mlflow_yml,
        is_cookiecutter=False,
        dst=project_path / "conf" / "base" / mlflow_yml,
        python_package=project_globals["python_package"],
    )
    if not silent:
        click.secho(
            click.style("'conf/base/mlflow.yml' successfully updated.", fg="green")
        )
    # make a check whether the project run.py is strictly identical to the template
    # if yes, replace the script by the template silently
    # if no, raise a warning and send a message to INSERT_DOC_URL
    flag_erase_runpy = force
    runpy_project_path = (
        project_path
        / "src"
        / (Path(project_globals["context_path"]).parent.as_posix() + ".py")
    )
    if not force:
        kedro_path = Path(KEDRO_PATH).parent
        runpy_template_path = (
            kedro_path
            / "templates"
            / "project"
            / "{{ cookiecutter.repo_name }}"
            / "src"
            / "{{ cookiecutter.python_package }}"
            / "run.py"
        )
        kedro_runpy_template = render_jinja_template(
            src=runpy_template_path,
            is_cookiecutter=True,
            python_package=project_globals["python_package"],
            project_name=project_globals["project_name"],
            kedro_version=project_globals["kedro_version"],
        )

        with open(runpy_project_path, mode="r") as file_handler:
            kedro_runpy_project = file_handler.read()

        # beware : black formatting could change slightly this test which is very strict
        if kedro_runpy_project == kedro_runpy_template:
            flag_erase_runpy = True

    if flag_erase_runpy:
        os.remove(runpy_project_path)
        write_jinja_template(
            src=TEMPLATE_FOLDER_PATH / "run.py",
            dst=runpy_project_path,
            is_cookiecutter=True,
            python_package=project_globals["python_package"],
            project_name=project_globals["project_name"],
            kedro_version=project_globals["kedro_version"],
        )
        if not silent:
            click.secho(click.style("'run.py' successfully updated", fg="green"))
    else:
        click.secho(
            click.style(
                "You have modified your 'run.py' since project creation.\n"
                + "In order to use kedro-mlflow, you must either:\n"
                + "    -  set up your run.py with the following instructions :\n"
                + "INSERT_DOC_URL\n"
                + "    - call the following command:\n"
                + "$ kedro mlflow init --force",
                fg="yellow",
            )
        )


@mlflow_commands.command()
@click.option(
    "--project-path",
    "-p",
    required=False,
    help="The environment within conf folder we want to retrieve.",
)
@click.option(
    "--env",
    "-e",
    required=False,
    default="local",
    help="The environment within conf folder we want to retrieve.",
)
def ui(project_path, env):
    """Opens the mlflow user interface with the
        project-specific settings of mlflow.yml. This interface
        enables to browse and compares runs.

    """

    # the context must contains the self.mlflow attribues with mlflow configuration
    mlflow_conf = get_mlflow_config(project_path=project_path, env=env)

    # call mlflow ui with specific options
    # TODO : add more options for ui
    subprocess.call(
        ["mlflow", "ui", "--backend-store-uri", mlflow_conf.mlflow_tracking_uri]
    )


@mlflow_commands.command()
def run():
    """Re-run an old run with mlflow-logged info.
    """

    # TODO (HARD) : define general assumptions to check whether a run
    #  is reproductible or not

    # TODO retrieve command
    # TODO retrieve parameters
    # TODO perform checks on data
    # TODO launch run
    raise NotImplementedError  # pragma: no cover


@mlflow_commands.command()
def new():
    """Create a new kedro project with updated template.
    """
    raise NotImplementedError  # pragma: no cover


class KedroMlflowCliError(Exception):
    """ kedro-mlflow cli specific error
    """

    pass
