from pathlib import PurePath
from copy import deepcopy
from typing import Union, Dict, Any
import mlflow
from kedro.io import AbstractVersionedDataSet
from kedro.io.core import parse_dataset_definition


class MlflowDataSet(AbstractVersionedDataSet):
    """This class is a wrapper for any kedro AbstractDataSet. 
    It decorates their ``save`` method to log the dataset in mlflow when ``save`` is called.
    
    """
    def __new__(cls,
                data_set: Union[str, Dict],
                run_id: str = None,
                artifact_path: str = None,
                credentials: Dict[str, Any] = None
                ):

        data_set, data_set_args = parse_dataset_definition(config=data_set)

        # fake inheritance : this mlfow class should be a mother class which wraps
        # all dataset (i.e. it should replace AbstractVersionedDataSet)
        # instead and since we can't modify the core package,
        # we create a subclass which inherits dynamically from the data_set class
        class MlflowDataSetChildren(data_set):
            def __init__(self, run_id, artifact_path):
                super().__init__(**data_set_args)
                self.run_id = run_id
                self.artifact_path = artifact_path

            def _save(self, data: Any):
                super()._save(data)
                if self.run_id:
                    # if a run id is specified,
                    # we have to open and close it for logging
                    # this forces management of active run
                    current_run_id = None
                    if mlflow.active_run():
                        current_run_id = mlflow.active_run().run_id
                        mlflow.end_run()
                    with mlflow.start_run(run_id=self.run_id):
                        mlflow.log_artifact(self._filepath, self.artifact_path)
                    if current_run_id:
                        mlflow.start_run(current_run_id)
                else:
                    mlflow.log_artifact(self._filepath, self.artifact_path)
        mlflow_dataset_instance = MlflowDataSetChildren(run_id=run_id,
                                                        artifact_path=artifact_path)
        return mlflow_dataset_instance
