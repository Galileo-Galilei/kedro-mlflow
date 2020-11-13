import importlib
from pathlib import Path
from typing import Any, Dict, Optional

from kedro.io import AbstractVersionedDataSet, Version
from kedro.io.core import DataSetError


class MlflowAbstractModelDataSet(AbstractVersionedDataSet):
    """
    Absract mother class for model datasets.
    """

    def __init__(
        self,
        filepath: str,
        flavor: str,
        pyfunc_workflow: Optional[str] = None,
        load_args: Dict[str, Any] = None,
        save_args: Dict[str, Any] = None,
        version: Version = None,
    ) -> None:
        """Initialize the Kedro MlflowModelDataSet.

        Parameters are passed from the Data Catalog.

        During save, the model is first logged to MLflow.
        During load, the model is pulled from MLflow run with `run_id`.

        Args:
            filepath (str): Path to store the dataset locally.
            flavor (str): Built-in or custom MLflow model flavor module.
                Must be Python-importable.
            pyfunc_workflow (str, optional): Either `python_model` or `loader_module`.
                See https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#workflows.
            load_args (Dict[str, Any], optional): Arguments to `load_model`
                function from specified `flavor`. Defaults to {}.
            save_args (Dict[str, Any], optional): Arguments to `log_model`
                function from specified `flavor`. Defaults to {}.
            version (Version, optional): Specific version to load.

        Raises:
            DataSetError: When passed `flavor` does not exist.
        """

        super().__init__(Path(filepath), version)

        self._flavor = flavor
        self._pyfunc_workflow = pyfunc_workflow

        if flavor == "mlflow.pyfunc" and pyfunc_workflow not in (
            "python_model",
            "loader_module",
        ):
            raise DataSetError(
                "PyFunc models require specifying `pyfunc_workflow` "
                "(set to either `python_model` or `loader_module`)"
            )

        self._load_args = load_args or {}
        self._save_args = save_args or {}

        self._mlflow_model_module = self._import_module(self._flavor)

    # TODO: check with Kajetan what was orignally intended here
    # @classmethod
    # def _parse_args(cls, kwargs_dict: Dict[str, Any]) -> Dict[str, Any]:
    #     parsed_kargs = {}
    #     for key, value in kwargs_dict.items():
    #         if key.endswith("_args"):
    #             continue
    #         if f"{key}_args" in kwargs_dict:
    #             new_value = cls._import_module(value)(
    #                 MlflowModelDataSet._parse_args(kwargs_dict[f"{key}_args"])
    #             )
    #             parsed_kargs[key] = new_value
    #         else:
    #             parsed_kargs[key] = value
    #     return parsed_kargs

    @staticmethod
    def _import_module(import_path: str) -> Any:
        exists = importlib.util.find_spec(import_path)

        if not exists:
            raise ImportError(f"{import_path} module not found")

        return importlib.import_module(import_path)
