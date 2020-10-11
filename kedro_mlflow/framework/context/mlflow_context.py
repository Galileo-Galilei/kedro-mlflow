from kedro.framework.context import KedroContext

from kedro_mlflow.framework.context.config import KedroMlflowConfig


# this could be a read-only property in the context
# with a @property decorator
# but for consistency with hook system, it is an external function
def get_mlflow_config(context: KedroContext):

    conf_mlflow_yml = context.config_loader.get("mlflow*", "mlflow*/**")
    conf_mlflow = KedroMlflowConfig(context.project_path)
    conf_mlflow.from_dict(conf_mlflow_yml)
    return conf_mlflow
