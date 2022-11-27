from typing import Any, Dict, Optional, Union

from kedro_mlflow.io.models.mlflow_abstract_model_dataset import (
    MlflowAbstractModelDataSet,
)


class MlflowModelRegistryDataSet(MlflowAbstractModelDataSet):
    """Wrapper for saving, logging and loading for all MLflow model flavor."""

    def __init__(
        self,
        model_name: str,
        stage_or_version: Union[str, int] = "latest",
        flavor: Optional[str] = "mlflow.pyfunc",
        pyfunc_workflow: Optional[str] = "python_model",
        load_args: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the Kedro MlflowModelRegistryDataSet.

        Parameters are passed from the Data Catalog.

        During "load", the model is pulled from MLflow model registry by its name.
        "save" is not supported.

        Args:
            model_name (str): The name of the registered model is the mlflow registry
            stage_or_version (str): A valid stage (either "staging" or "production") or version number for the registred model.
                Default to "latest" which fetch the last version and the higher "stage" available.
            flavor (str): Built-in or custom MLflow model flavor module.
                Must be Python-importable.
            pyfunc_workflow (str, optional): Either `python_model` or `loader_module`.
                See https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#workflows.
            load_args (Dict[str, Any], optional): Arguments to `load_model`
                function from specified `flavor`. Defaults to None.

        Raises:
            DataSetError: When passed `flavor` does not exist.
        """
        super().__init__(
            filepath="",
            flavor=flavor,
            pyfunc_workflow=pyfunc_workflow,
            load_args=load_args,
            save_args={},
            version=None,
        )

        self.model_name = model_name
        self.stage_or_version = stage_or_version
        self.model_uri = f"models:/{model_name}/{stage_or_version}"

    def _load(self) -> Any:
        """Loads an MLflow model from local path or from MLflow run.

        Returns:
            Any: Deserialized model.
        """

        # If `run_id` is specified, pull the model from MLflow.
        # TODO: enable loading from another mlflow conf (with a client with another tracking uri)
        # Alternatively, use local path to load the model.
        return self._mlflow_model_module.load_model(
            model_uri=self.model_uri, **self._load_args
        )

    def _save(self, model: Any) -> None:
        raise NotImplementedError(
            "The 'save' method is not implemented for MlflowModelRegistryDataSet. You can pass 'registered_model_name' argument in 'MLflowModelLoggerDataSet(..., save_args={registered_model_name='my_model'}' to save and register a model in the same step. "
        )

    def _describe(self) -> Dict[str, Any]:
        return dict(
            model_uri=self.model_uri,
            model_name=self.model_name,
            stage_or_version=self.stage_or_version,
            flavor=self._flavor,
            pyfunc_workflow=self._pyfunc_workflow,
            load_args=self._load_args,
        )
