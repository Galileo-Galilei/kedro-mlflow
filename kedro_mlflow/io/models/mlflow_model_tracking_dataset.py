from typing import Any, Optional

import mlflow
from kedro.io.core import DatasetError

from kedro_mlflow.io.models.mlflow_abstract_model_dataset import (
    MlflowAbstractModelDataSet,
)


# TODO: rename as MlflowLoggedModelDataset ? check out implications and relevance
class MlflowModelTrackingDataset(MlflowAbstractModelDataSet):
    """Wrapper for saving, logging and loading for all MLflow model flavor."""

    def __init__(
        self,
        flavor: str,
        pyfunc_workflow: Optional[str] = None,
        load_args: Optional[dict[str, Any]] = None,
        save_args: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Initialize the Kedro MlflowModelDataSet.

        Parameters are passed from the Data Catalog.

        During save, the model is first logged to MLflow.
        During load, the model is pulled from MLflow through its model_id.

        Args:
            flavor (str): Built-in or custom MLflow model flavor module.
                Must be Python-importable. ex: "mlflow.sklearn", "mlflow.pyfunc..."
            pyfunc_workflow (str, optional): Either `python_model` or `loader_module`.
                See https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#workflows.
            load_args (dict[str, Any], optional): Arguments to `load_model`
                function from specified `flavor`. Defaults to None.
            save_args (dict[str, Any], optional): Arguments to `log_model`
                function from specified `flavor`. Default to None, it is recommended to specify 'name'.
            metadata: Any arbitrary metadata.
                This is ignored by Kedro, but may be consumed by users or external plugins.

        Raises:
            DatasetError: When passed `flavor` does not exist.
        """
        super().__init__(
            filepath="",  # filepath is the model uri, but this is set dynamically by mlflow
            flavor=flavor,
            pyfunc_workflow=pyfunc_workflow,
            load_args=load_args,
            save_args=save_args,
            version=None,
            metadata=metadata,
        )

        if self._save_args.get("name") is None:
            self._logger.warning(
                "It is highly recommended to specify 'name' in 'save_args' to log the model. Since you did not specify it, a default name will be used by mlflow when saving the model."
            )
        # we will dynamically retrieve the model uri to use for loading the model based on the last one which was saved
        # but if the user specified a model_uri when instantiating the class we should not override it
        # we keep track of both to choose the right one when loading
        self._user_defined_model_uri = self._load_args.pop("model_uri", None)
        self._last_saved_model_uri = None
        self.model_info = None

    def _load(self) -> mlflow.entities.logged_model.LoggedModel:
        """Loads an MLflow model from local path or from MLflow run.

        Returns:
            LoggedModel: Deserialized model.
        """

        if self._user_defined_model_uri is not None:
            load_model_uri = self._user_defined_model_uri
        elif self._last_saved_model_uri is not None:
            load_model_uri = self._last_saved_model_uri
        else:
            raise DatasetError(
                "To load form a given model_uri, you must either: "
                "\n - specify 'model_uri' in 'load_args' when creating the class instance with one of these formats: https://mlflow.org/docs/latest/api_reference/python_api/mlflow.pyfunc.html#mlflow.pyfunc.load_pyfunc"
                "\n - have saved a model before to access the last saved model uri."
            )

        return self._mlflow_model_module.load_model(
            model_uri=load_model_uri, **self._load_args
        )

    def _save(self, model: Any) -> None:
        """Save a model to local path and then logs it to MLflow.

        Args:
            model (Any): A model object supported by the given MLflow flavor.
        """
        if self._logging_activated:
            if self._user_defined_model_uri:
                raise DatasetError(
                    "It is impossible to save a model when 'model_uri' is specified."
                    "Because mlflow does not let you override an existing model."
                    "You should specify 'model_uri' only for loading an existing model."
                )
            if self._flavor == "mlflow.pyfunc":
                # PyFunc models uses either `python_model` or `loader_module`
                # workflow. We assign the passed `model` object to one of those keys
                # depending on the chosen `pyfunc_workflow`.
                self._save_args[self._pyfunc_workflow] = model

                # we store the Modelinfo object in model_info attribute for later loading
                self.model_info = self._mlflow_model_module.log_model(**self._save_args)
            else:
                # Otherwise we save using the common workflow where first argument is the
                # model object and second is the path.
                # e.g., mlflow.sklearn.log_model(sklearn_model, name, ...)

                self.model_info = self._mlflow_model_module.log_model(
                    model, **self._save_args
                )

            # keep track of the last saved model uri for later loading
            self._last_saved_model_uri = self.model_info.model_uri

    def _describe(self) -> dict[str, Any]:
        return dict(
            flavor=self._flavor,
            pyfunc_workflow=self._pyfunc_workflow,
            load_args=self._load_args,
            save_args=self._save_args,
            name=self._save_args.get("name") or self.model_info.name
            if self.model_info
            else None,
            model_uri=self._user_defined_model_uri or self._last_saved_model_uri,
            model_id=self.model_info._model_uuid if self.model_info else None,
            run_id=self.model_info._run_id if self.model_info else None,
        )
