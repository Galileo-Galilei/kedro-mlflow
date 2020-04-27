import os
import subprocess
from pathlib import Path

import click
from kedro import __file__ as KEDRO_PATH

from kedro_mlflow.cli.cli_utils import render_jinja_template, write_jinja_template
from kedro_mlflow.context import get_mlflow_conf
from kedro_mlflow.utils import _already_updated, _get_project_globals, _is_kedro_project


@click.group(name="Mlflow")
def commands():
    """Kedro plugin for interactions with mlflow.
    """
    pass


@commands.group(name="mlflow")
def mlflow_commands():
    """Use mlflow-specific commands inside kedro project.
    """
    pass


@click.command()
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
    if not _is_kedro_project(project_path):
        raise KedroMlflowCliError(
            "This command can only be called from the root of a kedro project."
        )
    project_globals = _get_project_globals(project_path)
    template_folder_path = Path(__file__).parent.parent / "template" / "project"

    # mlflow.yml is just a static file,
    # but the name of the experiment is set to be the same as the project
    mlflow_yml = "mlflow.yml"
    write_jinja_template(
        src=template_folder_path / mlflow_yml,
        is_cookiecutter=False,
        dst=project_path / "conf" / "base" / mlflow_yml,
        python_package=project_globals["python_package"],
    )
    if not silent:
        click.secho(
            click.style("'conf/base/mlflow.yml' sucessfully updated.", fg="green")
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
            / "template/{{ cookiecutter.repo_name }}/src/{{ cookiecutter.python_package }}/run.py"
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

        # strip() is necessary because cookiecutter render python files
        # with an extra line jump "\n" (to match autopep8 convention)
        if kedro_runpy_project.strip() == kedro_runpy_template:
            flag_erase_runpy = True

    if flag_erase_runpy:
        os.remove(runpy_project_path)
        write_jinja_template(
            src=template_folder_path / "run.py",
            dst=runpy_project_path,
            is_cookiecutter=True,
            python_package=project_globals["python_package"],
            project_name=project_globals["project_name"],
            kedro_version=project_globals["kedro_version"],
        )
        if not silent:
            click.secho(click.style("'run.py' sucessfully updated", fg="green"))
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


@click.command()
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
    if project_path is None:
        project_path = Path().cwd().as_posix()
    else:
        project_path = Path(project_path)
    if not _is_kedro_project(project_path):
        raise KedroMlflowCliError("'project_path' must be the root of a kedro project.")

    # the context must contains the self.mlflow attribues with mlflow configuration
    mlflow_conf = get_mlflow_conf(project_path=project_path, env=env)

    # call mlflow ui with specific options
    # TODO : add more options for ui
    subprocess.call(
        ["mlflow", "ui", "--backend-store-uri", mlflow_conf.mlflow_tracking_uri]
    )


@click.command()
def run():
    """Re-run an old run with mlflow-logged info.
    """

    # TODO (HARD) : define general assumptions to check whether a run
    #  is reproductible or not

    # TODO retrieve command
    # TODO retrieve parameters
    # TODO perform checks on data
    # TODO launch run
    pass


@click.command()
def new():
    """Create a new kedro project with updated template.
    """
    click.secho("Not implemented yet")


class KedroMlflowCliError(Exception):
    """ kedro-mlflow cli specific error
    """

    pass


# logic to deal with the import of the different commands
# we want to give restrictive access depending on conditions
if _is_kedro_project():
    mlflow_commands.add_command(init)
    if _already_updated():
        mlflow_commands.add_command(ui)
        mlflow_commands.add_command(run)
    else:
        click.secho(
            click.style(
                "You have not updated your template yet. "
                "This is mandatory to use 'kedro-mlflow' plugin.\n"
                + "Please run the following command before you can access to other commands :\n"
                + "$ kedro mlflow init",
                fg="yellow",
            )
        )
else:
    mlflow_commands.add_command(new)
