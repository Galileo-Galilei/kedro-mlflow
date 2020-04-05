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