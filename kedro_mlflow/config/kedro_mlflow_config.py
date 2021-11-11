import os
from pathlib import Path, PurePath
from typing import Dict, List, Optional
from urllib.parse import urlparse

import mlflow
from kedro.config import MissingConfigException
from kedro.framework.session import KedroSession, get_current_session
from kedro.framework.startup import _is_project
from mlflow.entities import Experiment
from mlflow.tracking.client import MlflowClient
from pydantic import BaseModel, PrivateAttr, StrictBool, validator
from typing_extensions import Literal


class MlflowServerOptions(BaseModel):
    # mutable default is ok for pydantic : https://stackoverflow.com/questions/63793662/how-to-give-a-pydantic-list-field-a-default-value
    mlflow_tracking_uri: str = "mlruns"
    stores_environment_variables: Dict[str, str] = {}
    credentials: Optional[str] = None
    _mlflow_client: MlflowClient = PrivateAttr()

    class Config:
        extra = "forbid"


class DisableTrackingOptions(BaseModel):
    # mutable default is ok for pydantic : https://stackoverflow.com/questions/63793662/how-to-give-a-pydantic-list-field-a-default-value
    pipelines: List[str] = []

    class Config:
        extra = "forbid"


class ExperimentOptions(BaseModel):
    name: str = "Default"
    restore_if_deleted: StrictBool = True
    _experiment: Experiment = PrivateAttr()
    # do not create _experiment immediately to avoid creating
    # a database connection when creating the object
    # it will be instantiated on setup() call

    class Config:
        extra = "forbid"


class RunOptions(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    nested: StrictBool = True

    class Config:
        extra = "forbid"


class DictParamsOptions(BaseModel):
    flatten: StrictBool = False
    recursive: StrictBool = True
    sep: str = "."

    class Config:
        extra = "forbid"


class MlflowParamsOptions(BaseModel):
    dict_params: DictParamsOptions = DictParamsOptions()
    long_params_strategy: Literal["fail", "truncate", "tag"] = "fail"

    class Config:
        extra = "forbid"


class MlflowTrackingOptions(BaseModel):
    # mutable default is ok for pydantic : https://stackoverflow.com/questions/63793662/how-to-give-a-pydantic-list-field-a-default-value
    disable_tracking: DisableTrackingOptions = DisableTrackingOptions()
    experiment: ExperimentOptions = ExperimentOptions()
    run: RunOptions = RunOptions()
    params: MlflowParamsOptions = MlflowParamsOptions()

    class Config:
        extra = "forbid"


class UiOptions(BaseModel):

    port: str = "5000"
    host: str = "127.0.0.1"

    class Config:
        extra = "forbid"


class KedroMlflowConfig(BaseModel):
    project_path: Path  # if str, will be converted
    server: MlflowServerOptions = MlflowServerOptions()
    tracking: MlflowTrackingOptions = MlflowTrackingOptions()
    ui: UiOptions = UiOptions()

    class Config:
        # force triggering type control when setting value instead of init
        validate_assignment = True
        # raise an error if an unknown key is passed to the constructor
        extra = "forbid"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server.mlflow_tracking_uri = self._validate_uri(
            self.server.mlflow_tracking_uri
        )
        # init after validating the uri, else mlflow creates a mlruns folder at the root
        self.server._mlflow_client = MlflowClient(
            tracking_uri=self.server.mlflow_tracking_uri
        )

    def setup(self, session: KedroSession = None):
        """Setup all the mlflow configuration"""

        self._export_credentials(session)

        # we set the configuration now: it takes priority
        # if it has already be set in export_credentials
        mlflow.set_tracking_uri(self.server.mlflow_tracking_uri)

        self._set_experiment()

    def _export_credentials(self, session: KedroSession = None):
        session = session or get_current_session()
        context = session.load_context()
        conf_creds = context._get_config_credentials()
        mlflow_creds = conf_creds.get(self.server.credentials, {})
        for key, value in mlflow_creds.items():
            os.environ[key] = value

    def _set_experiment(self):
        """Best effort to get the experiment associated
        to the configuration

        Returns:
            mlflow.entities.Experiment -- [description]
        """

        # we retrieve the experiment manually to check if it exsits
        mlflow_experiment = self.server._mlflow_client.get_experiment_by_name(
            name=self.tracking.experiment.name
        )
        # Deal with two side case when retrieving the experiment
        if mlflow_experiment is not None:
            if (
                self.tracking.experiment.restore_if_deleted
                and mlflow_experiment.lifecycle_stage == "deleted"
            ):
                # the experiment was created, then deleted : we have to restore it manually before setting it as the active one
                self.server._mlflow_client.restore_experiment(
                    mlflow_experiment.experiment_id
                )

        # this creates the experiment if it does not exists
        # and creates a global variable with the experiment
        # but returns nothing
        mlflow.set_experiment(experiment_name=self.tracking.experiment.name)

        # we do not use "experiment" variable directly but we fetch again from the database
        # because if it did not exists at all, it was created by previous command
        self.tracking.experiment._experiment = (
            self.server._mlflow_client.get_experiment_by_name(
                name=self.tracking.experiment.name
            )
        )

    def _validate_uri(self, uri):
        """Format the uri provided to match mlflow expectations.

        Arguments:
            uri {Union[None, str]} -- A valid filepath for mlflow uri

        Returns:
            str -- A valid mlflow_tracking_uri
        """

        # this is a special reserved keyword for mlflow which should not be converted to a path
        # se: https://mlflow.org/docs/latest/tracking.html#where-runs-are-recorded
        if uri == "databricks":
            return uri

        # if no tracking uri is provided, we register the runs locally at the root of the project
        pathlib_uri = PurePath(uri)

        if pathlib_uri.is_absolute():
            valid_uri = pathlib_uri.as_uri()
        else:
            parsed = urlparse(uri)
            if parsed.scheme == "":
                # if it is a local relative path, make it absolute
                # .resolve() does not work well on windows
                # .absolute is undocumented and have known bugs
                # Path.cwd() / uri is the recommend way by core developpers.
                # See : https://discuss.python.org/t/pathlib-absolute-vs-resolve/2573/6
                valid_uri = (self.project_path / uri).as_uri()
            else:
                # else assume it is an uri
                valid_uri = uri

        return valid_uri

    @validator("project_path")
    def _is_kedro_project(cls, folder_path):
        if not _is_project(folder_path):
            raise KedroMlflowConfigError(
                f"'project_path' = '{folder_path}' is not the root of kedro project"
            )
        return folder_path


class KedroMlflowConfigError(Exception):
    """Error occurred when loading the configuration"""


def get_mlflow_config(session: Optional[KedroSession] = None):
    session = session or get_current_session()
    context = session.load_context()
    try:
        conf_mlflow_yml = context.config_loader.get("mlflow*", "mlflow*/**")
    except MissingConfigException:
        raise KedroMlflowConfigError(
            "No 'mlflow.yml' config file found in environment. Use ``kedro mlflow init`` command in CLI to create a default config file."
        )
    conf_mlflow_yml["project_path"] = context.project_path
    mlflow_config = KedroMlflowConfig.parse_obj(conf_mlflow_yml)
    return mlflow_config
