from pathlib import Path

from kedro.config import ConfigLoader
from kedro.context import KedroContext

from kedro_mlflow.context.config import KedroMlflowConfig


class KedroMlflowContext(KedroContext):
    @property
    def mlflow(self):
        """Read only property for the mlflow configuration based on yml
        """
        return self._get_mlflow_properties()

    def _get_mlflow_properties(self):
        conf_mlflow = self.config_loader.get("mlflow*", "mlflow*/**")
        mlflow_properties = KedroMlflowConfig(project_path=self.project_path)
        mlflow_properties.from_dict(conf_mlflow)
        return mlflow_properties


# this could be a read-only property in the context
# with a @property decorator
# but for consistency with hook system, it is an external function
def get_mlflow_conf(project_path, env):
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
