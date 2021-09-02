import os
from pathlib import Path, PurePath
from typing import List, Optional

import mlflow
from kedro.config import MissingConfigException
from kedro.framework.session import KedroSession, get_current_session
from kedro.framework.startup import _is_project
from mlflow.entities import Experiment
from mlflow.tracking.client import MlflowClient
from pydantic import BaseModel, PrivateAttr, StrictBool, validator
from typing_extensions import Literal


class DisableTrackingOptions(BaseModel):
    # mutable default is ok for pydantic : https://stackoverflow.com/questions/63793662/how-to-give-a-pydantic-list-field-a-default-value
    pipelines: List[str] = []

    class Config:
        extra = "forbid"


class ExperimentOptions(BaseModel):
    name: str = "Default"
    create: StrictBool = True

    class Config:
        extra = "forbid"


class RunOptions(BaseModel):
    id: Optional[str]
    name: Optional[str]
    nested: StrictBool = True

    class Config:
        extra = "forbid"


class UiOptions(BaseModel):
    port: str = "5000"
    host: str = "127.0.0.1"

    class Config:
        extra = "forbid"


class NodeHookOptions(BaseModel):
    flatten_dict_params: StrictBool = False
    recursive: StrictBool = True
    sep: str = "."
    long_parameters_strategy: Literal["fail", "truncate", "tag"] = "fail"

    class Config:
        extra = "forbid"


class HookOptions(BaseModel):
    node: NodeHookOptions = NodeHookOptions()

    class Config:
        extra = "forbid"


class KedroMlflowConfig(BaseModel):
    project_path: Path  # if str, will be converted
    mlflow_tracking_uri: str = "mlruns"
    credentials: Optional[str]
    disable_tracking: DisableTrackingOptions = DisableTrackingOptions()
    experiment: ExperimentOptions = ExperimentOptions()
    run: RunOptions = RunOptions()
    ui: UiOptions = UiOptions()
    hooks: HookOptions = HookOptions()
    _mlflow_client: MlflowClient = PrivateAttr()
    _experiment: Experiment = PrivateAttr()
    # do not create _experiment immediately to avoid creating
    # a database connection when creating the object
    # it will be instantiated on setup() call

    class Config:
        # force triggering type control when setting value instead of init
        validate_assignment = True
        # raise an error if an unknown key is passed to the constructor
        extra = "forbid"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # init after validating the uri, else mlflow creates a mlruns folder at the root
        self._mlflow_client = MlflowClient(tracking_uri=self.mlflow_tracking_uri)

    def setup(self, session: KedroSession = None):
        """Setup all the mlflow configuration"""

        self._export_credentials(session)

        # we set the configuration now: it takes priority
        # if it has already be set in export_credentials
        mlflow.set_tracking_uri(self.mlflow_tracking_uri)

        self._get_or_create_experiment()

    def _export_credentials(self, session: KedroSession = None):
        session = session or get_current_session()
        context = session.load_context()
        conf_creds = context._get_config_credentials()
        mlflow_creds = conf_creds.get(self.credentials, {})
        for key, value in mlflow_creds.items():
            os.environ[key] = value

    def _get_or_create_experiment(self):
        """Best effort to get the experiment associated
        to the configuration

        Returns:
            mlflow.entities.Experiment -- [description]
        """

        # retrieve the experiment
        self._experiment = self._mlflow_client.get_experiment_by_name(
            name=self.experiment.name
        )

        # Deal with two side case when retrieving the experiment
        if self.experiment.create:
            if self._experiment is None:
                # case 1 : the experiment does not exist, it must be created manually
                experiment_id = self._mlflow_client.create_experiment(
                    name=self.experiment.name
                )
                self._experiment = self._mlflow_client.get_experiment(
                    experiment_id=experiment_id
                )
            elif self._experiment.lifecycle_stage == "deleted":
                # case 2: the experiment was created, then deleted : we have to restore it manually
                self._mlflow_client.restore_experiment(self._experiment.experiment_id)

    @validator("project_path")
    def _is_kedro_project(cls, folder_path):
        if not _is_project(folder_path):
            raise KedroMlflowConfigError(
                f"'project_path' = '{folder_path}' is not the root of kedro project"
            )
        return folder_path

    # pre=make a conversion before it is set
    # always=even for default value
    # values enable access to the other field, see https://pydantic-docs.helpmanual.io/usage/validators/
    @validator("mlflow_tracking_uri", pre=True, always=True)
    def _validate_uri(cls, uri, values):
        """Format the uri provided to match mlflow expectations.

        Arguments:
            uri {Union[None, str]} -- A valid filepath for mlflow uri

        Returns:
            str -- A valid mlflow_tracking_uri
        """

        # if no tracking uri is provided, we register the runs locally at the root of the project
        pathlib_uri = PurePath(uri)

        from urllib.parse import urlparse

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
                valid_uri = (values["project_path"] / uri).as_uri()
            else:
                # else assume it is an uri
                valid_uri = uri

        return valid_uri


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
