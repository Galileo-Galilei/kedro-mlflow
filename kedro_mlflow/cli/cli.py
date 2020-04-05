import click
from kedro.cli import get_project_context

@click.group(name="Mlflow")
def commands():
    """Kedro plugin for interactions with mlflow.
    """
    pass

@commands.group(name="mlflow")
def mlflow_commands:
    """Use mlflow-specific commands inside kedro project.
    """
    pass

@mlflow_commands.command()
def update_template():
    """This command updates the template of a kedro project. 
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
    # TODO render mlflow.yml with jinja

    # TODO make a check whether run.py is strictly identical to the template
    # if yes, replace the script
    # if not raise an error and send a mesage to INSERT_DOC_URL
    pass

@mlflow_commands.command()
def ui():
    """This command opens the mlflow user interface with the 
        project-specific settings of mlflow.yml. This interface 
        enables to browse and compares runs. 

    """
    # TODO load mlflow_tracking_uri for mlflow.yml and ensure consistency

    #TODO  call mlflow ui with specific --backend-store-uri option
    pass

@mlflow_commands.command()
def run():
    """This command opens the mlflow ui with the 
        project-specific settings of mlflow.yml. 
    """
    
    # TODO (HARD) : define general assumptions to check whether a run
    #  is reporductible or not

    #TODO retrieve command
    #TODO retrieve parameters
    #TODO perform checks on data
    #TODO launch run 
    pass