from logging import Logger, getLogger
from typing import Any, Optional, Union

from kedro.io.core import DatasetError

from kedro_mlflow.io.models.mlflow_abstract_model_dataset import (
    MlflowAbstractModelDataSet,
)


class MlflowModelRegistryDataset(MlflowAbstractModelDataSet):
    """Wrapper for saving, logging and loading for all MLflow model flavor."""

    def __init__(
        self,
        model_name: str,
        stage_or_version: Union[str, int, None] = None,
        alias: Optional[str] = None,
        flavor: Optional[str] = "mlflow.pyfunc",
        pyfunc_workflow: Optional[str] = "python_model",
        load_args: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize the Kedro MlflowModelRegistryDataset.

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
            load_args (dict[str, Any], optional): Arguments to `load_model`
                function from specified `flavor`. Defaults to None.
            metadata: Any arbitrary metadata.
                This is ignored by Kedro, but may be consumed by users or external plugins.

        Raises:
            DatasetError: When passed `flavor` does not exist.
        """
        super().__init__(
            filepath="",
            flavor=flavor,
            pyfunc_workflow=pyfunc_workflow,
            load_args=load_args,
            save_args={},
            version=None,
            metadata=metadata,
        )

        if alias is None and stage_or_version is None:
            # reassign stage_or_version to "latest"
            stage_or_version = "latest"

        if alias and stage_or_version:
            raise DatasetError(
                f"You cannot specify 'alias' and 'stage_or_version' simultaneously ({alias=} and {stage_or_version=})"
            )

        self.model_name = model_name
        self.stage_or_version = stage_or_version
        self.alias = alias
        self.model_uri = (
            f"models:/{model_name}@{alias}"
            if alias
            else f"models:/{model_name}/{stage_or_version}"
        )

    @property
    def _logger(self) -> Logger:
        return getLogger(__name__)

    def _load(self) -> Any:
        """Loads an MLflow model from local path or from MLflow run.

        Returns:
            Any: Deserialized model.
        """

        # If `run_id` is specified, pull the model from MLflow.
        # TODO: enable loading from another mlflow conf (with a client with another tracking uri)
        # Alternatively, use local path to load the model.
        model = self._mlflow_model_module.load_model(
            model_uri=self.model_uri, **self._load_args
        )

        # log some info because "latest" model is not very informative
        # the model itself does not have information about its registry
        # because the same run can be registered under several different names
        #  in the registry. See https://github.com/Galileo-Galilei/kedro-mlflow/issues/552

        self._logger.info(f"Loading model from run_id='{model.metadata.run_id}'")
        return model

    def _save(self, model: Any) -> None:
        raise NotImplementedError(
            "The 'save' method is not implemented for MlflowModelRegistryDataset. You can pass 'registered_model_name' argument in 'MLflowModelTrackingDataset(..., save_args={registered_model_name='my_model'}' to save and register a model in the same step. "
        )

    def _describe(self) -> dict[str, Any]:
        return dict(
            model_uri=self.model_uri,
            model_name=self.model_name,
            stage_or_version=self.stage_or_version,
            alias=self.alias,
            flavor=self._flavor,
            pyfunc_workflow=self._pyfunc_workflow,
            # load_args=self._load_args,
        )
