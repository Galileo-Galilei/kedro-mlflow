from functools import partial
from itertools import chain
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

import mlflow
from kedro.io import AbstractDataset, DatasetError
from mlflow.tracking import MlflowClient

MetricItem = Union[Dict[str, float], List[Dict[str, float]]]
MetricTuple = Tuple[str, float, int]
MetricsDict = Dict[str, MetricItem]


class MlflowMetricsHistoryDataset(AbstractDataset):
    """This class represent MLflow metrics dataset."""

    def __init__(
        self,
        run_id: str = None,
        prefix: Optional[str] = None,
    ):
        """Initialise MlflowMetricsHistoryDataset.

        Args:
            prefix (Optional[str]): Prefix for metrics logged in MLflow.
            run_id (str): ID of MLflow run.
        """
        self._prefix = prefix
        self.run_id = run_id
        self._logging_activated = True  # by default, logging is activated!

    @property
    def run_id(self):
        """Get run id.

        If active run is not found, tries to find last experiment.

        Raise `DatasetError` exception if run id can't be found.

        Returns:
            str: String contains run_id.
        """
        if self._run_id is not None:
            return self._run_id
        run = mlflow.active_run()
        if run:
            return run.info.run_id
        raise DatasetError("Cannot find run id.")

    @run_id.setter
    def run_id(self, run_id):
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

    def _load(self) -> MetricsDict:
        """Load MlflowMetricDataSet.

        Returns:
            Dict[str, Union[int, float]]: Dictionary with MLflow metrics dataset.
        """
        client = MlflowClient()

        all_metrics_keys = list(client.get_run(self.run_id).data.metrics.keys())

        dataset_metrics_keys = [
            key for key in all_metrics_keys if self._is_dataset_metric(key)
        ]

        dataset_metrics = {
            key: self._convert_metric_history_to_list_or_dict(
                client.get_metric_history(self.run_id, key)
            )
            for key in dataset_metrics_keys
        }

        return dataset_metrics

    def _save(self, data: MetricsDict) -> None:
        """Save given MLflow metrics dataset and log it in MLflow as metrics.

        Args:
            data (MetricsDict): MLflow metrics dataset.
        """
        client = MlflowClient()
        try:
            run_id = self.run_id
        except DatasetError:
            # If run_id can't be found log_metric would create new run.
            run_id = None

        log_metric = (
            partial(client.log_metric, run_id)
            if run_id is not None
            else mlflow.log_metric
        )
        metrics = (
            self._build_args_list_from_metric_item(k, v) for k, v in data.items()
        )

        if self._logging_activated:
            for k, v, i in chain.from_iterable(metrics):
                log_metric(k, v, step=i)

    def _exists(self) -> bool:
        """Check if MLflow metrics dataset exists.

        Returns:
            bool: Is MLflow metrics dataset exists?
        """
        client = MlflowClient()
        all_metrics_keys = client.get_run(self.run_id).data.metrics.keys()
        # all_metrics = client._tracking_client.store.get_all_metrics(
        #     run_uuid=self.run_id
        # )
        return any(self._is_dataset_metric(x) for x in all_metrics_keys)

    def _describe(self) -> Dict[str, Any]:
        """Describe MLflow metrics dataset.

        Returns:
            Dict[str, Any]: Dictionary with MLflow metrics dataset description.
        """
        return {
            "run_id": self._run_id,
            "prefix": self._prefix,
        }

    def _is_dataset_metric(self, key: str) -> bool:
        """Check if given metric belongs to dataset.

        Args:
            key str: The name of a mlflow metric registered in the run
        """
        return self._prefix is None or (self._prefix and key.startswith(self._prefix))

    # @staticmethod
    # def _update_metric(
    #     metrics: List[mlflow.entities.Metric], dataset: MetricsDict = {}
    # ) -> MetricsDict:
    #     """Update metric in given dataset.

    #     Args:
    #         metrics (List[mlflow.entities.Metric]): List with MLflow metric objects.
    #         dataset (MetricsDict): Dictionary contains MLflow metrics dataset.

    #     Returns:
    #         MetricsDict: Dictionary with MLflow metrics dataset.
    #     """
    #     for metric in metrics:
    #         metric_dict = {"step": metric.step, "value": metric.value}
    #         if metric.key in dataset:
    #             if isinstance(dataset[metric.key], list):
    #                 dataset[metric.key].append(metric_dict)
    #             else:
    #                 dataset[metric.key] = [dataset[metric.key], metric_dict]
    #         else:
    #             dataset[metric.key] = metric_dict
    #     return dataset

    @staticmethod
    def _convert_metric_history_to_list_or_dict(
        metrics: List[mlflow.entities.Metric],
    ) -> Dict[str, Dict[str, Union[float, List[float]]]]:
        """Convert Mlflow metrics objects from MlflowClient().get_metric_history(run_id, key)
        to a list [{'step': x, 'value': y}, {'step': ..., 'value': ...}]

        Args:
            metrics (List[mlflow.entities.Metric]): A list of MLflow Metrics retrieved from the run history
        """
        metrics_as_list = [
            {"step": metric.step, "value": metric.value} for metric in metrics
        ]
        metrics_result = (
            metrics_as_list[0] if len(metrics_as_list) == 1 else metrics_as_list
        )
        return metrics_result

    def _build_args_list_from_metric_item(
        self, key: str, value: MetricItem
    ) -> Generator[MetricTuple, None, None]:
        """Build list of tuples with metrics.

        First element of a tuple is key, second metric value, third step.

        If MLflow metrics dataset has prefix, it will be attached to key.

        Args:
            key (str): Metric key.
            value (MetricItem): Metric value

        Returns:
            List[MetricTuple]: List with metrics as tuples.
        """
        if self._prefix:
            key = f"{self._prefix}.{key}"
        if isinstance(value, dict):
            return (i for i in [(key, value["value"], value["step"])])
        if isinstance(value, list) and len(value) > 0:
            return ((key, x["value"], x["step"]) for x in value)
        raise DatasetError(
            f"Unexpected metric value. Should be of type `{MetricItem}`, got {type(value)}"
        )
