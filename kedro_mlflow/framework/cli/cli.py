import subprocess
from logging import getLogger
from pathlib import Path
from typing import Dict, Optional, Union

import click
import mlflow
from kedro.framework.project import pipelines
from kedro.framework.session import KedroSession
from kedro.framework.startup import _is_project, bootstrap_project
from mlflow.models import infer_signature
from packaging import version

from kedro_mlflow.config import get_mlflow_config
from kedro_mlflow.framework.cli.cli_utils import write_jinja_template
from kedro_mlflow.mlflow import KedroPipelineModel

LOGGER = getLogger(__name__)
TEMPLATE_FOLDER_PATH = Path(__file__).parent.parent.parent / "template" / "project"


class KedroClickGroup(click.Group):
    def reset_commands(self):
        self.commands = {}

        # add commands on the fly based on conditions
        if _is_project(Path.cwd()):
            self.add_command(init)
            self.add_command(ui)
            self.add_command(modelify)
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
def init(env: str, force: bool, silent: bool):
    """Updates the template of a kedro project.
    Running this command is mandatory to use kedro-mlflow.
    This adds "conf/base/mlflow.yml": This is a configuration file
    used for run parametrization when calling "kedro run" command.
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
def ui(env: str, port: str, host: str):
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
                mlflow_conf.server.mlflow_tracking_uri,
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
@click.option(
    "--pipeline",
    "-p",
    "pipeline_name",  # the name in the function, see # https://github.com/pallets/click/issues/725
    type=str,
    required=True,
    help="A valid kedro pipeline name registered in pipeline_registry.py. Available pipelines can be listed with in 'kedro registry list'",
)
@click.option(
    "--input-name",
    "-i",
    type=str,
    required=True,
    help="The name of kedro dataset which contains the data to predict on",
)
@click.option(
    "--infer-signature",
    "flag_infer_signature",  # the name in the function, see # https://github.com/pallets/click/issues/725
    is_flag=True,
    required=False,
    default=False,
    help="Should the signature of the input data be inferred for mlflow?",
)
@click.option(
    "--infer-input-example",
    "flag_infer_input_example",  # the name in the function, see # https://github.com/pallets/click/issues/725
    is_flag=True,
    required=False,
    default=False,
    help="Should the input_example of the input data be inferred for mlflow?",
)
@click.option(
    "--run-id",
    "-r",
    required=False,
    default=None,
    help="The id of the mlflow run where the model will be logged. If unspecified, the command creates a new run.",
)
@click.option(
    "--copy-mode",
    required=False,
    default="deepcopy",
    help="The copy mode to use when replacing each dataset by a MemoryDataSet. Either a string (applied all datasets) or a dict mapping each dataset to a copy_mode.",
)
@click.option(
    "--artifact-path",
    default="model",
    required=False,
    help="The artifact path of mlflow.pyfunc.log_model, see https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model",
)
@click.option(
    "--code-path",
    default=None,
    required=False,
    help="The code path of mlflow.pyfunc.log_model, see https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model",
)
@click.option(
    "--conda-env",
    default=None,
    required=False,
    help="The conda environment of mlflow.pyfunc.log_model, see https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model",
)
@click.option(
    "--registered-model-name",
    default=None,
    required=False,
    help="The registered_model_name of mlflow.pyfunc.log_model, see https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model",
)
@click.option(
    "--await-registration-for",
    default=None,
    required=False,
    help="The await_registration_for of mlflow.pyfunc.log_model, see https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model",
)
@click.option(
    "--pip-requirements",
    default=None,
    required=False,
    help="The pip_requirements of mlflow.pyfunc.log_model, see https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model",
)
@click.option(
    "--extra-pip-requirements",
    default=None,
    required=False,
    help="The extra_pip_requirements of mlflow.pyfunc.log_model, see https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model",
)
def modelify(
    # ctx,
    pipeline_name: str,
    input_name: str,
    flag_infer_signature: Optional[bool],
    flag_infer_input_example: Optional[bool],
    run_id: Optional[str],
    copy_mode: Optional[Union[str, Dict[str, str]]],
    artifact_path: str,
    code_path: str,
    conda_env: str,
    registered_model_name: str,
    await_registration_for: int,
    pip_requirements: str,
    extra_pip_requirements: str,
):
    """Export a kedro pipeline as a mlflow model for serving"""
    # if the command is available, we are necessarily at the root of a kedro project

    project_path = Path.cwd()
    bootstrap_project(project_path)
    with KedroSession.create(project_path=project_path) as session:
        config = get_mlflow_config()
        config.setup()
        # "pipeline" is the Pipeline object you want to convert to a mlflow model
        pipeline = pipelines[pipeline_name]
        context = session.load_context()
        catalog = context.catalog
        input_name = input_name

        if input_name not in pipeline.inputs():
            valid_inputs = "\n - ".join(pipeline.inputs())
            raise ValueError(
                f"'{input_name}' is not a valid 'input_name', it must be an input of 'pipeline', i.e. one of: \n - {valid_inputs}"
            )
        # artifacts are all the inputs of the inference pipelines that are persisted in the catalog

        # (optional) get the schema of the input dataset
        model_signature = None
        if flag_infer_signature:
            input_data = catalog.load(input_name)
            model_signature = infer_signature(model_input=input_data)

        input_example = None
        if flag_infer_input_example:
            if flag_infer_signature is False:
                # else we have already loaded the data
                input_data = catalog.load(input_name)
            input_example = input_data.iloc[
                0:1, :
            ]  # 0:1 forces a dataframe, iloc returns a Series which raises a mlflow error

        # you can optionnally pass other arguments, like the "copy_mode" to be used for each dataset
        kedro_pipeline_model = KedroPipelineModel(
            pipeline=pipeline,
            catalog=catalog,
            input_name=input_name,
            copy_mode=copy_mode,
            # add runner option
        )

        artifacts = kedro_pipeline_model.extract_pipeline_artifacts()

        if conda_env is None:
            conda_env = {"python": "3.7.0", "dependencies": ["kedro==0.16.5"]}

        log_model_kwargs = dict(
            artifact_path=artifact_path,
            python_model=kedro_pipeline_model,
            artifacts=artifacts,
            code_path=code_path,
            conda_env=conda_env,
            signature=model_signature,
            input_example=input_example,
            registered_model_name=registered_model_name,
            await_registration_for=await_registration_for,
        )
        if version.parse(f"{mlflow.__version__}") >= version.parse("1.20.0"):
            log_model_kwargs["pip_requirements"] = pip_requirements
            log_model_kwargs["extra_pip_requirements"] = extra_pip_requirements

        with mlflow.start_run(run_id=run_id):
            mlflow.pyfunc.log_model(**log_model_kwargs)
            run_id = mlflow.active_run().info.run_id
            LOGGER.info(f"Model successfully logged in run '{run_id}'")


class KedroMlflowCliError(Exception):
    """kedro-mlflow cli specific error"""

    pass
