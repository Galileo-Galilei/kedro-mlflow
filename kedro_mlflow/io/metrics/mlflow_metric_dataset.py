from copy import deepcopy
from typing import Any, Dict

from mlflow.tracking import MlflowClient

from kedro_mlflow.io.metrics.mlflow_abstract_metric_dataset import (
    MlflowAbstractMetricDataSet,
)


class MlflowMetricDataSet(MlflowAbstractMetricDataSet):
    SUPPORTED_SAVE_MODES = {"overwrite", "append"}
    DEFAULT_SAVE_MODE = "overwrite"

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

        # We add an extra argument mode="overwrite" / "append" to enable logging update an existing metric
        # this is not an offical mlflow argument for log_metric, so we separate it from the others
        # "overwrite" corresponds to the default mlflow behaviour
        self.mode = self._save_args.pop("mode", self.DEFAULT_SAVE_MODE)

    def _load(self):
        self._validate_run_id()
        mlflow_client = MlflowClient()
        metric_history = mlflow_client.get_metric_history(
            run_id=self.run_id, key=self.key
        )  # gets active run if no run_id was given

        # the metric history is always a list of mlflow.entities.metric.Metric
        # we want the value of the last one stored because this dataset only deal with one single metric
        step = self._load_args.get("step")

        if step is None:
            # we take the last value recorded
            metric_value = metric_history[-1].value
        else:
            # we should take the last historical value with the given step
            # (it is possible to have several values with the same step)
            metric_value = next(
                metric.value
                for metric in reversed(metric_history)
                if metric.step == step
            )

        return metric_value

    def _save(self, data: float):
        if self._logging_activated:
            self._validate_run_id()
            run_id = (
                self.run_id
            )  # we access it once instead of calling self.run_id everywhere to avoid looking or an active run each time

            mlflow_client = MlflowClient()

            # get the metric history if it has been saved previously to ensure
            #  to retrieve the right data
            # reminder: this is True even if no run_id was originally specified but a run is active
            metric_history = (
                mlflow_client.get_metric_history(run_id=run_id, key=self.key)
                if self._exists()
                else []
            )

            save_args = deepcopy(self._save_args)
            step = save_args.pop("step", None)
            if step is None:
                if self.mode == "overwrite":
                    step = max([metric.step for metric in metric_history], default=0)
                elif self.mode == "append":
                    # I put a max([]) default to -1 so that default "step" equals 0
                    step = (
                        max([metric.step for metric in metric_history], default=-1) + 1
                    )
                else:
                    raise ValueError(
                        f"save_args['mode'] must be one of {self.SUPPORTED_SAVE_MODES}, got '{self.mode}' instead."
                    )

            mlflow_client.log_metric(
                run_id=run_id,
                key=self.key,
                value=data,
                step=step,
                **save_args,
            )
