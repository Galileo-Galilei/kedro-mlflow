from typing import Optional

from deprecation import deprecated
from kedro.config import MissingConfigException
from kedro.framework.session import KedroSession, get_current_session

from kedro_mlflow import __version__
from kedro_mlflow.framework.context.config import (
    KedroMlflowConfig,
    KedroMlflowConfigError,
)


# this could be a read-only property in the context
# with a @property decorator
# but for consistency with hook system, it is an external function
@deprecated(
    deprecated_in="0.7.5",
    removed_in="0.8.0",
    current_version=__version__,
    details="This function was moved to 'kedro_mlflow.config' folder. Use 'from kedro_mlflow.config import get_mlflow_config' instead of 'from kedro_mlflow.framework.context import get_mlflow_config'",
)
def get_mlflow_config(session: Optional[KedroSession] = None):
    session = session or get_current_session()
    context = session.load_context()
    try:
        conf_mlflow_yml = context.config_loader.get("mlflow*", "mlflow*/**")
    except MissingConfigException:
        raise KedroMlflowConfigError(
            "No 'mlflow.yml' config file found in environment. Use ``kedro mlflow init`` command in CLI to create a default config file."
        )
    conf_mlflow = KedroMlflowConfig(context.project_path)
    conf_mlflow.from_dict(conf_mlflow_yml)
    return conf_mlflow
