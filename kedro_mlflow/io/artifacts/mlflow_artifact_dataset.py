import shutil
from pathlib import Path
from typing import Any, Dict, Union

import mlflow
from kedro.io import AbstractVersionedDataset
from kedro.io.core import parse_dataset_definition
from mlflow.tracking import MlflowClient


class MlflowArtifactDataset(AbstractVersionedDataset):
    """This class is a wrapper for any kedro AbstractDataset.
    It decorates their ``save`` method to log the dataset in mlflow when ``save`` is called.
    """

    def __new__(
        cls,
        dataset: Union[str, Dict],
        run_id: str = None,
        artifact_path: str = None,
        credentials: Dict[str, Any] = None,
    ):
        dataset_obj, dataset_args = parse_dataset_definition(config=dataset)

        # fake inheritance : this mlflow class should be a mother class which wraps
        # all dataset (i.e. it should replace AbstractVersionedDataset)
        # instead and since we can't modify the core package,
        # we create a subclass which inherits dynamically from the dataset class
        class MlflowArtifactDatasetChildren(dataset_obj):
            def __init__(self, run_id, artifact_path):
                super().__init__(**dataset_args)
                self.run_id = run_id
                self.artifact_path = artifact_path
                self._logging_activated = True

            @property
            def _logging_activated(self):
                return self.__logging_activated

            @_logging_activated.setter
            def _logging_activated(self, flag):
                if not isinstance(flag, bool):
                    raise ValueError(
                        f"_logging_activated must be a boolean, got {type(flag)}"
                    )
                self.__logging_activated = flag

            def _save(self, data: Any):
                # _get_save_path needs to be called before super, otherwise
                # it will throw exception that file under path already exist.
                if hasattr(self, "_version"):
                    # all kedro datasets inherits from AbstractVersionedDataset
                    local_path = self._get_save_path()
                elif hasattr(self, "_filepath"):
                    # in case custom datasets inherits from AbstractDataset without versioning
                    local_path = self._filepath  # pragma: no cover
                elif hasattr(self, "_path"):
                    # special datasets with a folder instead of a specific files like PartitionedDataset
                    local_path = Path(self._path)

                # it must be converted to a string with as_posix()
                # for logging on remote storage like Azure S3
                local_path = local_path.as_posix()

                if hasattr(super().save, "__wrapped__"):  # modern dataset
                    super().save.__wrapped__(self, data)
                else:  # legacy dataset
                    super()._save(data)

                if self._logging_activated:
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

            def _load(self) -> Any:  # pragma: no cover
                if self.run_id:
                    # if no run_id is specified, we take the artifact from the local path rather that the active run:
                    # there are a lot of chances that it has not been saved yet!

                    if hasattr(self, "_version"):
                        # all kedro datasets inherits from AbstractVersionedDataset
                        local_path = self._get_load_path()
                    elif hasattr(self, "_filepath"):
                        # in case custom datasets inherits from AbstractDataset without versioning
                        local_path = self._filepath  # pragma: no cover
                    elif hasattr(self, "_path"):
                        # special datasets with a folder instead of a specific files like PartitionedDataset
                        local_path = Path(self._path)

                    # BEWARE: we must enforce Path(local_path) because it is a PurePosixPath which fails on windows
                    # this is very weird: if you assign the value, it is converted to a Pureposixpath again, e.g:
                    # this fails:
                    #      local_path = Path(local_path)
                    #      local_path.name # local_path has been converted back to PurePosixPath on windows on this 2nd row
                    # but this works as a one liner:
                    #      filename = Path(local_path).name

                    filename = Path(local_path).name
                    artifact_path = (
                        (self.artifact_path / Path(filename)).as_posix()
                        if self.artifact_path
                        else filename
                    )

                    mlflow_client = MlflowClient()
                    # specific trick to manage different behaviour between mlflow 1 and 2
                    if hasattr(mlflow_client, "download_artifacts"):
                        # download in mlflow 1
                        # we cannot use dst_path, because it downloads the file to "local_path / artifact_path /filename.pkl"
                        # the artifact_path suffix prevents from loading when we call super._load()
                        temp_download_filepath = mlflow_client.download_artifacts(
                            run_id=self.run_id,
                            path=artifact_path,
                            # dst_path=local_path.parent.as_posix(),
                        )
                    else:
                        # download in mlflow 2
                        from mlflow.artifacts import download_artifacts

                        temp_download_filepath = download_artifacts(
                            run_id=self.run_id,
                            artifact_path=artifact_path,
                            # dst_path=local_path.parent.as_posix(),
                        )

                    shutil.copy(src=temp_download_filepath, dst=local_path)

                # finally, read locally
                if hasattr(super().load, "__wrapped__"):  # modern dataset
                    return super().load.__wrapped__(self)
                else:  # legacy dataset
                    return super()._load()

        # rename the class
        parent_name = dataset_obj.__name__
        MlflowArtifactDatasetChildren.__name__ = f"Mlflow{parent_name}"
        MlflowArtifactDatasetChildren.__qualname__ = (
            f"{parent_name}.Mlflow{parent_name}"
        )

        mlflow_dataset_instance = MlflowArtifactDatasetChildren(
            run_id=run_id, artifact_path=artifact_path
        )
        return mlflow_dataset_instance

    def _load(self) -> Any:  # pragma: no cover
        """
        MlflowArtifactDataset is a factory for DataSet
        and consequently does not implements abtracts methods
        """
        pass

    def _save(self, data: Any) -> None:  # pragma: no cover
        """
        MlflowArtifactDataset is a factory for DataSet
        and consequently does not implements abtracts methods
        """
        pass

    def _describe(self) -> Dict[str, Any]:  # pragma: no cover
        """
        MlflowArtifactDataset is a factory for DataSet
        and consequently does not implements abtracts methods
        """
        pass
