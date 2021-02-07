from kedro.config import MissingConfigException
from kedro.framework.context import KedroContext

from kedro_mlflow.framework.context.config import (
    KedroMlflowConfig,
    KedroMlflowConfigError,
)


# this could be a read-only property in the context
# with a @property decorator
# but for consistency with hook system, it is an external function
def get_mlflow_config(context: KedroContext):
    try:
        conf_mlflow_yml = context.config_loader.get("mlflow*", "mlflow*/**")
    except MissingConfigException:
        raise KedroMlflowConfigError(
            "No 'mlflow.yml' config file found in environment. Use ``kedro mlflow init`` command in CLI to create a default config file."
        )
    conf_mlflow = KedroMlflowConfig(context.project_path)
    conf_mlflow.from_dict(conf_mlflow_yml)
    return conf_mlflow
