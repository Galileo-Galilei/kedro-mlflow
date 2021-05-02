import logging
import os
from pathlib import Path, PurePath
from typing import Any, Dict, Optional, Union

import mlflow
from kedro.framework.session.session import KedroSession, get_current_session
from kedro.framework.startup import _is_project

LOGGER = logging.getLogger(__name__)


class KedroMlflowConfig:

    DISABLE_TRACKING_OPTS = {"pipelines": []}

    EXPERIMENT_OPTS = {"name": "Default", "create": True}

    RUN_OPTS = {"id": None, "name": None, "nested": True}

    UI_OPTS = {"port": "5000", "host": "127.0.0.1"}

    NODE_HOOK_OPTS = {
        "flatten_dict_params": False,
        "recursive": True,
        "sep": ".",
        "long_parameters_strategy": "fail",
    }

    AVAILABLE_LONG_PARAMETERS_STRATEGY = ["fail", "truncate", "tag"]

    def __init__(
        self,
        project_path: Union[str, Path],
        mlflow_tracking_uri: str = "mlruns",
        credentials: Optional[Dict[str, str]] = None,
        disable_tracking_opts: Optional[Dict[str, str]] = None,
        experiment_opts: Union[Dict[str, Any], None] = None,
        run_opts: Union[Dict[str, Any], None] = None,
        ui_opts: Union[Dict[str, Any], None] = None,
        node_hook_opts: Union[Dict[str, Any], None] = None,
    ):

        # declare attributes in __init__.py to avoid pylint complaining
        if not _is_project(project_path):
            raise KedroMlflowConfigError(
                (
                    f"'project_path' = '{project_path}' is not a valid path to a kedro project"
                )
            )
        self.project_path = Path(project_path)
        # TODO we may add mlflow_registry_uri future release
        self.mlflow_tracking_uri = "mlruns"
        self.credentials = (
            credentials or {}
        )  # replace None by {} but o not default to empty dict which is mutable
        self.disable_tracking_opts = None
        self.experiment_opts = None
        self.run_opts = None
        self.ui_opts = None
        self.node_hook_opts = None
        self.mlflow_client = None  # the client to interact with the mlflow database
        self.experiment = (
            None  # the mlflow experiment object to interact directly with it
        )

        # load attributes with the from_dict method
        # which is the method which will almost always be used
        # for loading the configuration
        configuration = dict(
            mlflow_tracking_uri=mlflow_tracking_uri,
            credentials=credentials,
            disable_tracking=disable_tracking_opts,
            experiment=experiment_opts,
            run=run_opts,
            ui=ui_opts,
            hooks=dict(node=node_hook_opts),
        )
        self.from_dict(configuration)

    def setup(self, session: KedroSession = None):
        """Setup all the mlflow configuration"""

        self._export_credentials(session)

        # we set the configuration now: it takes priority
        # if it has already be set in export_credentials
        mlflow.set_tracking_uri(self.mlflow_tracking_uri)

        self._get_or_create_experiment()

    def from_dict(self, configuration: Dict[str, str]):
        """This functions populates all the attributes of the class through a dictionary.
        This is the preferred method because the configuration is intended
        to be read from a 'mlflow.yml' file.


        Arguments:
            configuration {Dict[str, str]} -- A dict with the following format :
            {
                mlflow_tracking_uri: a valid string for mlflow tracking storage,
                credentials: a valid string which exists in credentials.yml,
                tracking:
                    {
                        pipelines {List[str]}: the name of pipeline which do not trigger tracking
                    },
                experiments:
                    {
                        name {str}: the name of the experiment
                        create {bool} : should the experiment be created if it does not exists?
                    },
                run:
                    {
                        nested {bool}: should we allow nested run within the context?
                    },
                ui:
                    {
                        port {int} : the port where the ui must be served
                        host {str} : the host for the ui
                    }
                hooks:
                    {
                        node:
                            {
                             flatten_dict_params {bool}: When the parameter is a dict, should we crete several parameters i the dict, one for each entry? This may be necessary beacuase mlflow has a liit size for parameters. Default to False.
                             recursive {bool}: In we flatten dict parameters, should we apply the strategy recusrively in case of nested dicts? Default to True.
                             sep {str}: The separator in case of nested dict flattening {level1:{p1:1, p2:2}} will be logged as level1.p1, level.p2. Default to "."
                            }
                    }
            }

        """

        mlflow_tracking_uri = configuration.get("mlflow_tracking_uri")
        credentials = configuration.get("credentials")
        disable_tracking_opts = configuration.get("disable_tracking")
        experiment_opts = configuration.get("experiment")
        run_opts = configuration.get("run")
        ui_opts = configuration.get("ui")
        node_hook_opts = configuration.get("hooks", {}).get("node")

        self.mlflow_tracking_uri = self._validate_uri(uri=mlflow_tracking_uri)
        self.credentials = credentials  # do not replace by value here for safety
        self.disable_tracking_opts = _validate_opts(
            opts=disable_tracking_opts, default=self.DISABLE_TRACKING_OPTS
        )
        self.experiment_opts = _validate_opts(
            opts=experiment_opts, default=self.EXPERIMENT_OPTS
        )
        self.run_opts = _validate_opts(opts=run_opts, default=self.RUN_OPTS)
        self.ui_opts = _validate_opts(opts=ui_opts, default=self.UI_OPTS)
        self.node_hook_opts = _validate_opts(
            opts=node_hook_opts, default=self.NODE_HOOK_OPTS
        )

        # this parameter validation should likely be elsewhere
        # when refactoring KedroMlflowConfig, we shoudl use an object
        # to validate data with a @property
        if (
            self.node_hook_opts["long_parameters_strategy"]
            not in self.AVAILABLE_LONG_PARAMETERS_STRATEGY
        ):
            strategy_list = ", ".join(self.AVAILABLE_LONG_PARAMETERS_STRATEGY)
            raise KedroMlflowConfigError(
                f"'long_parameters_strategy' must be one of [{strategy_list}], "
                f"got '{self.node_hook_opts['long_parameters_strategy']}'"
            )

        # instantiate mlflow objects to interact with the database
        # the client must not be created before carefully checking the uri,
        # otherwise mlflow creates a mlruns folder to the current location
        self.mlflow_client = mlflow.tracking.MlflowClient(
            tracking_uri=self.mlflow_tracking_uri
        )

    def to_dict(self):
        """Retrieve all the attributes needed to setup the config

        Returns:
            Dict[str, Any] -- All attributes with the following format:
            {
                mlflow_tracking_uri: a valid string for mlflow tracking storage,
                credentials: a valid string which exists in credentials.yml,
                experiments_opts:
                    {
                        name {str}: the name of the experiment
                        create {bool} : should the experiment be created if it does not exists?
                    },
                run_opts:
                    {
                        nested {bool}: should we allow nested run within the context?
                    }
            }
        """
        info = {
            "mlflow_tracking_uri": self.mlflow_tracking_uri,
            "credentials": self.credentials,
            "disable_tracking": self.disable_tracking_opts,
            "experiments": self.experiment_opts,
            "run": self.run_opts,
            "ui": self.ui_opts,
            "hooks": {"node": self.node_hook_opts},
        }
        return info

    def _get_or_create_experiment(self) -> mlflow.entities.Experiment:
        """Best effort to get the experiment associated
        to the configuration

        Returns:
            mlflow.entities.Experiment -- [description]
        """
        name = self.experiment_opts["name"]
        flag_create = self.experiment_opts["create"]

        # retrieve the experiment
        self.experiment = self.mlflow_client.get_experiment_by_name(name=name)

        # Deal with two side case when retrieving the experiment
        if flag_create:
            if self.experiment is None:
                # case 1 : the experiment does not exist, it must be created manually
                experiment_id = self.mlflow_client.create_experiment(
                    name=self.experiment_opts["name"]
                )
                self.experiment = self.mlflow_client.get_experiment(
                    experiment_id=experiment_id
                )
            elif self.experiment.lifecycle_stage == "deleted":
                # case 2: the experiment was created, then deleted : we have to restore it manually
                self.mlflow_client.restore_experiment(self.experiment.experiment_id)

    def _validate_uri(self, uri: Union[str, None]) -> str:
        """Format the uri provided to match mlflow expectations.

        Arguments:
            uri {Union[None, str]} -- A valid filepath for mlflow uri

        Returns:
            str -- A valid mlflow_tracking_uri
        """

        # if no tracking uri is provided, we register the runs locally at the root of the project
        uri = uri or "mlruns"
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
                valid_uri = (self.project_path / uri).as_uri()
            else:
                # else assume it is an uri
                valid_uri = uri

        return valid_uri

    def _export_credentials(self, session: KedroSession = None):
        session = session or get_current_session()
        context = session.load_context()
        conf_creds = context._get_config_credentials()
        mlflow_creds = conf_creds.get(self.credentials, {})
        for key, value in mlflow_creds.items():
            os.environ[key] = value


def _validate_opts(opts: Dict[str, Any], default: Dict[str, Any]) -> Dict:
    """This functions creates a valid dictionary containing options
        for different mlflow setup.
        Only the keys provided in the default dictionary are allowed.
        If provided, value of the opts dictionary are kept, otherwise
        default values are retrieved.


    Arguments:
        opts {Dict[str, Any]} -- A dictionary containing the configuration.
        default_opts {Dict[str, Any]} -- A default dictionary that enforces valid keys and provides default values

    Raises:
        KedroMlflowConfigError: If a key in the opt dictionary does not exist in the default, it is not a valid key.

    Returns:
        Dict -- A dictionary with all the keys of 'default' and the values of 'opts' if provided.
    """
    # makes a deepcopy to avoid modifying class constants
    default_copy = default.copy()
    opts_copy = {} if opts is None else opts.copy()

    for k in opts_copy.keys():
        if k not in default_copy.keys():
            raise KedroMlflowConfigError(
                """Provided option '{k}' is not valid.
            Possible keys are :\n- {keys}""".format(
                    k=k, keys="\n- ".join(default_copy.keys())
                )
            )

    default_copy.update(opts_copy)

    return default_copy


class KedroMlflowConfigError(Exception):
    """Error occurred when loading the configuration"""
