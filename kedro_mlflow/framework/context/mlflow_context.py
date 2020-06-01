from pathlib import Path

from kedro.config import ConfigLoader

from kedro_mlflow.framework.context.config import KedroMlflowConfig


# this could be a read-only property in the context
# with a @property decorator
# but for consistency with hook system, it is an external function
def get_mlflow_config(project_path=None, env="local"):
    if project_path is None:
        project_path = Path.cwd()
    project_path = Path(project_path)
    conf_paths = [
        str(project_path / "conf" / "base"),
        str(project_path / "conf" / env),
    ]
    config_loader = ConfigLoader(conf_paths=conf_paths)
    conf_mlflow_yml = config_loader.get("mlflow*", "mlflow*/**")
    conf_mlflow = KedroMlflowConfig(project_path=project_path)
    conf_mlflow.from_dict(conf_mlflow_yml)
    return conf_mlflow
