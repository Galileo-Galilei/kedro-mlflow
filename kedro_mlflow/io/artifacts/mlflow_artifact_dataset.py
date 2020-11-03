from typing import Any, Dict, Union

import mlflow
from kedro.io import AbstractVersionedDataSet
from kedro.io.core import parse_dataset_definition
from mlflow.tracking import MlflowClient


class MlflowArtifactDataSet(AbstractVersionedDataSet):
    """This class is a wrapper for any kedro AbstractDataSet.
    It decorates their ``save`` method to log the dataset in mlflow when ``save`` is called.

    """

    def __new__(
        cls,
        data_set: Union[str, Dict],
        run_id: str = None,
        artifact_path: str = None,
        credentials: Dict[str, Any] = None,
    ):

        data_set, data_set_args = parse_dataset_definition(config=data_set)

        # fake inheritance : this mlflow class should be a mother class which wraps
        # all dataset (i.e. it should replace AbstractVersionedDataSet)
        # instead and since we can't modify the core package,
        # we create a subclass which inherits dynamically from the data_set class
        class MlflowArtifactDataSetChildren(data_set):
            def __init__(self, run_id, artifact_path):
                super().__init__(**data_set_args)
                self.run_id = run_id
                self.artifact_path = artifact_path

            def _save(self, data: Any):
                # _get_save_path needs to be called before super, otherwise
                # it will throw exception that file under path already exist.
                local_path = (
                    self._get_save_path()
                    if hasattr(self, "_version")
                    else self._filepath
                )
                # it must be converted to a string with as_posix()
                # for logging on remote storage like Azure S3
                local_path = local_path.as_posix()

                super()._save(data)
                if self.run_id:
                    # if a run id is specified, we have to use mlflow client
                    # to avoid potential conflicts with an already active run
                    mlflow_client = MlflowClient()
                    mlflow_client.log_artifact(
                        run_id=self.run_id,
                        local_path=local_path,
                        artifact_path=self.artifact_path,
                    )
                else:
                    mlflow.log_artifact(local_path, self.artifact_path)

        # rename the class
        parent_name = data_set.__name__
        MlflowArtifactDataSetChildren.__name__ = f"Mlflow{parent_name}"
        MlflowArtifactDataSetChildren.__qualname__ = (
            f"{parent_name}.Mlflow{parent_name}"
        )

        mlflow_dataset_instance = MlflowArtifactDataSetChildren(
            run_id=run_id, artifact_path=artifact_path
        )
        return mlflow_dataset_instance

    def _load(self) -> Any:  # pragma: no cover
        """
        MlflowArtifactDataSet is a factory for DataSet
        and consequently does not implements abtracts methods
        """
        pass

    def _save(self, data: Any) -> None:  # pragma: no cover
        """
        MlflowArtifactDataSet is a factory for DataSet
        and consequently does not implements abtracts methods
        """
        pass

    def _describe(self) -> Dict[str, Any]:  # pragma: no cover
        """
        MlflowArtifactDataSet is a factory for DataSet
        and consequently does not implements abtracts methods
        """
        pass
