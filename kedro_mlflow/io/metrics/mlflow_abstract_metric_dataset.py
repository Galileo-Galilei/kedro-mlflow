from typing import Any, Dict, Union

import mlflow
from kedro.io import AbstractDataSet
from mlflow.tracking import MlflowClient


class MlflowAbstractMetricDataSet(AbstractDataSet):
    def __init__(
        self,
        key: str = None,
        run_id: str = None,
        load_args: Dict[str, Any] = None,
        save_args: Dict[str, Any] = None,
    ):
        """Initialise MlflowMetricsDataSet.

        Args:
            run_id (str): The ID of the mlflow run where the metric should be logged
        """

        self.key = key
        self.run_id = run_id
        self._load_args = load_args or {}
        self._save_args = save_args or {}
        self._logging_activated = True  # by default, logging is activated!

    @property
    def run_id(self) -> Union[str, None]:
        """Get run id."""

        run = mlflow.active_run()
        if (self._run_id is None) and (run is not None):
            # if no run_id is specified, we try to retrieve the current run
            # this is useful because during a kedro run, we want to be able to retrieve
            # the metric from the active run to be able to reload a metric
            # without specifying the (unknown) run id
            return run.info.run_id

        # else we return the _run_id which can eventually be None.
        # In this case, saving will work (a new run will be created)
        # but loading will fail,
        # according to mlflow's behaviour
        return self._run_id

    @run_id.setter
    def run_id(self, run_id: str):
        self._run_id = run_id

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

    def _validate_run_id(self):
        if self.run_id is None:
            raise ValueError(
                "You must either specify a run_id or have a mlflow active run opened. Use mlflow.start_run() if necessary."
            )

    def _exists(self) -> bool:
        """Check if the metric exists in remote mlflow storage exists.

        Returns:
            bool: Does the metric name exist in the given run_id?
        """
        mlflow_client = MlflowClient()
        run_id = self.run_id  # will get the active run if nothing is specified
        run = mlflow_client.get_run(run_id) if run_id else mlflow.active_run()

        flag_exist = self.key in run.data.metrics.keys() if run else False
        return flag_exist

    def _describe(self) -> Dict[str, Any]:
        """Describe MLflow metrics dataset.

        Returns:
            Dict[str, Any]: Dictionary with MLflow metrics dataset description.
        """
        return {
            "key": self.key,
            "run_id": self.run_id,
        }
