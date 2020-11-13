import shutil
from os.path import exists
from typing import Any, Dict, Optional

from kedro.io import Version

from kedro_mlflow.io.models.mlflow_abstract_model_dataset import (
    MlflowAbstractModelDataSet,
)


class MlflowModelSaverDataSet(MlflowAbstractModelDataSet):
    """Wrapper for saving, logging and loading for all MLflow model flavor."""

    def __init__(
        self,
        filepath: str,
        flavor: str,
        pyfunc_workflow: Optional[str] = None,
        load_args: Dict[str, Any] = None,
        save_args: Dict[str, Any] = None,
        log_args: Dict[str, Any] = None,
        version: Version = None,
    ) -> None:

        """Initialize the Kedro MlflowModelDataSet.

        Parameters are passed from the Data Catalog.

        During save, the model is saved locally at `filepath`
        During load, the model is loaded from the local `filepath`.

        Args:
            flavor (str): Built-in or custom MLflow model flavor module.
                Must be Python-importable.
            filepath (str): Path to store the dataset locally.
            pyfunc_workflow (str, optional): Either `python_model` or `loader_module`.
                See https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#workflows.
            load_args (Dict[str, Any], optional): Arguments to `load_model`
                function from specified `flavor`. Defaults to None.
            save_args (Dict[str, Any], optional): Arguments to `save_model`
                function from specified `flavor`. Defaults to None.
            version (Version, optional): Kedro version to use. Defaults to None.
        Raises:
            DataSetError: When passed `flavor` does not exist.
        """
        super().__init__(
            filepath=filepath,
            flavor=flavor,
            pyfunc_workflow=pyfunc_workflow,
            load_args=load_args,
            save_args=save_args,
            version=version,
        )

    def _load(self) -> Any:
        """Loads an MLflow model from local path or from MLflow run.

        Returns:
            Any: Deserialized model.
        """
        return self._mlflow_model_module.load_model(
            model_uri=self._get_load_path().as_uri(), **self._load_args
        )

    def _save(self, model: Any) -> None:
        """Save a model to local path and then logs it to MLflow.

        Args:
            model (Any): A model object supported by the given MLflow flavor.
        """
        save_path = self._get_save_path()
        # In case of an unversioned model we need to remove the save path
        # because MLflow cannot overwrite the target directory.
        if exists(save_path):
            shutil.rmtree(save_path)

        if self._flavor == "mlflow.pyfunc":
            # PyFunc models utilise either `python_model` or `loader_module`
            # workflow. We we assign the passed `model` object to one of those keys
            # depending on the chosen `pyfunc_workflow`.
            self._save_args[self._pyfunc_workflow] = model
            self._mlflow_model_module.save_model(save_path, **self._save_args)
        else:
            # Otherwise we save using the common workflow where first argument is the
            # model object and second is the path.
            self._mlflow_model_module.save_model(model, save_path, **self._save_args)

    def _describe(self) -> Dict[str, Any]:
        return dict(
            filepath=self._filepath,
            flavor=self._flavor,
            pyfunc_workflow=self._pyfunc_workflow,
            load_args=self._load_args,
            save_args=self._save_args,
            version=self._version,
        )
