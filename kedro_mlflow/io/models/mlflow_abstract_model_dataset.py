from importlib import import_module
from importlib.util import find_spec
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
        self._logging_activated = True  # by default, it should be True!

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

        try:
            self._mlflow_model_module
        except ImportError as err:
            raise DataSetError(err)

    # we want to be able to turn logging off for an entire pipeline run
    # To avoid that a single call to a dataset in the catalog creates a new run automatically
    # we want to be able to turn everything off
    @property
    def _logging_activated(self):
        return self.__logging_activated

    @_logging_activated.setter
    def _logging_activated(self, flag):
        if not isinstance(flag, bool):
            raise ValueError(f"_logging_activated must be a boolean, got {type(flag)}")
        self.__logging_activated = flag

    # IMPORTANT:  _mlflow_model_module is a property to avoid STORING
    # the module as an attribute but rather store a string and load on the fly
    # The goal is to make this DataSet deepcopiable for compatibility with
    # KedroPipelineModel, e.g we can't just do :
    # self._mlflow_model_module = self._import_module(self._flavor)

    @property
    def _mlflow_model_module(self):  # pragma: no cover
        pass

    @_mlflow_model_module.getter
    def _mlflow_model_module(self):
        return self._import_module(self._flavor)

    # TODO: check with Kajetan what was originally intended here
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
        exists = find_spec(import_path)

        if not exists:
            raise ImportError(
                f"'{import_path}' module not found. Check valid flavor in mlflow documentation: https://www.mlflow.org/docs/latest/python_api/index.html"
            )

        return import_module(import_path)
