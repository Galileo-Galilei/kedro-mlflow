import click
import pathlib
import subprocess
import kedro_mlflow.utils as utils
import kedro_mlflow.cli.cli_utils as cli_utils
from kedro.cli import get_project_context
from kedro.context import load_context
# from importlib import reload
# reload(utils)
# reload(cli_utils)

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
def template():
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
    # project_path=pathlib.Path(r"C:\Users\Yolan\Documents\PACKAGES\pk")
    project_path = pathlib.Path().cwd()
    if not utils._is_kedro_project(project_path):
        raise KedroMlflowCliError(
            "This command can only be called from the root of a kedro project.")
    project_globals = utils._get_project_globals(project_path)
    template_folder_path = pathlib.Path(__file__).parent.parent / "template"
        
    # mlflow.yml is just a static file, 
    # but the name of the experiment is set to be the same as the project
    mlflow_yml = "mlflow.yml"
    cli_utils.write_jinja_template(src=template_folder_path / mlflow_yml,
                                    dst=project_path / "conf" / "base" / mlflow_yml, 
                                    python_package=project_globals["python_package"])

    # TODO make a check whether run.py is strictly identical to the template
    # if yes, replace the script
    # if not raise an error and send a mesage to INSERT_DOC_URL

    # try to compare the project "run.py" and the kedro template
    kedro_path = pathlib.Path(kedro.__file__).parent
    runpy_template_path = (kedro_path / r"template\{{ cookiecutter.repo_name }}\src\{{ cookiecutter.python_package }}\run.py")
    kedro_runpy_template = cli_utils.render_jinja_template(src= runpy_template_path,
                                                           python_package=project_globals["python_package"],
                                                           project_name = project_globals["project_name"],
                                                           kedro_version = project_globals["kedro_version"])
    cli_utils.write_jinja_template(src=template_folder_path / "run.py",
                                    dst=project_path / project_globals["context_path"],
                                    python_package=project_globals["python_package"])


@click.command()
def ui():
    """Opens the mlflow user interface with the 
        project-specific settings of mlflow.yml. This interface 
        enables to browse and compares runs. 

    """
    # TODO load mlflow_tracking_uri for mlflow.yml and ensure consistency
    cwd = pathlib.Path().cwd().as_posix()
    if not utils._is_kedro_project(cwd):
        raise KedroMlflowCliError(
            "This command can only be called from the root of a kedro project.")
    print(cwd)
    project_context = load_context(project_path=cwd)
    #TODO  call mlflow ui with specific --backend-store-uri option
    subprocess.call(["mlflow", "ui", "--backend-store-uri", project_context.mlflow.mlflow_tracking_uri])
    pass

@click.command()
def run():
    """Re-run an old run with mlflow-logged info. 
    """
    
    # TODO (HARD) : define general assumptions to check whether a run
    #  is reproductible or not

    #TODO retrieve command
    #TODO retrieve parameters
    #TODO perform checks on data
    #TODO launch run 
    pass

@click.command()
def new():
    """Create a new kedro project with updated template.
    """
    pass

class KedroMlflowCliError(Exception):
    """ kedro-mlflow cli specific error
    """
    pass

# logic to deal with the import of the different commands
# we want to give restrictive access depending on conditions
if utils._is_kedro_project():
    mlflow_commands.add_command(template)
    if utils._already_updated():
        mlflow_commands.add_command(ui)
        mlflow_commands.add_command(run)
    else:
        click.secho(click.style("You have not updated your template yet. "
                                "This is mandatory to use 'kedro-mlflow' plugin.\n" +
                                "Please run the following command before you can access to other commands :\n" +
                                '$ kedro mlflow template',
                                fg="yellow"))
else:
    mlflow_commands.add_command(new)
