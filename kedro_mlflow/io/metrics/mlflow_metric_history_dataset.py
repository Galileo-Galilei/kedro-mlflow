from typing import Any, Dict, List, Union

from mlflow.tracking import MlflowClient

from kedro_mlflow.io.metrics.mlflow_abstract_metric_dataset import (
    MlflowAbstractMetricDataSet,
)


class MlflowMetricHistoryDataSet(MlflowAbstractMetricDataSet):
    def __init__(
        self,
        key: str = None,
        run_id: str = None,
        load_args: Dict[str, Any] = None,
        save_args: Dict[str, Any] = None,
    ):
        """Initialise MlflowMetricDataSet.
        Args:
            run_id (str): The ID of the mlflow run where the metric should be logged
        """

        super().__init__(key, run_id, load_args, save_args)

    def _load(self):
        self._validate_run_id()
        mode = self._load_args.get("mode", "list")
        mlflow_client = MlflowClient()

        metric_history = mlflow_client.get_metric_history(self.run_id, key=self.key)

        if mode == "list":
            simplified_history = [metric.value for metric in metric_history]
        elif mode == "dict":
            simplified_history = {
                metric.step: metric.value for metric in metric_history
            }
        elif mode == "history":
            # history is a list of dict whom keys are "log_metric" arguments. The following is equivalent to dict mode:
            # [{"step": 0, "value": 0.1}, {"step": 1, "value": 0.2}, {"step": 2, "value": 0.3}]
            simplified_history = [
                {
                    "step": metric.step,
                    "value": metric.value,
                    "timestamp": metric.timestamp,
                }
                for metric in metric_history
            ]
        return simplified_history

    def _save(
        self,
        data: Union[List[int], Dict[int, float], List[Dict[str, Union[float, str]]]],
    ):
        if self._logging_activated:
            self._validate_run_id()
            run_id = self.run_id

            mode = self._save_args.get("mode", "list")
            mlflow_client = MlflowClient()
            if mode == "list":
                # list is a list of value in sequential order:
                # [0.1,0.2,0.3]
                for i, value in enumerate(data):
                    mlflow_client.log_metric(
                        run_id=run_id, key=self.key, step=i, value=value
                    )
            elif mode == "dict":
                # dict is a {step: value} mapping:
                # [{0: 0.1}, {1: 0.2}, {2: 0.3}]
                for step, value in data.items():
                    mlflow_client.log_metric(
                        run_id=run_id, key=self.key, step=step, value=value
                    )
            elif mode == "history":
                # history is a list of dict whom keys are "log_metric" arguments. The following is equivalent to dict mode:
                # [{"step": 0, "value": 0.1}, {"step": 1, "value": 0.2}, {"step": 2, "value": 0.3}]
                for log_kwargs in data:
                    mlflow_client.log_metric(run_id=run_id, key=self.key, **log_kwargs)
