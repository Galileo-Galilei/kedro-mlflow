import math

import mlflow
import pytest
from kedro.io import DatasetError

from kedro_mlflow.io.metrics import MlflowMetricsHistoryDataset

MODULE = "kedro_mlflow.io.metrics.mlflow_metrics_history_dataset"


@pytest.mark.parametrize("size", [0, -1, 1001, True, 1.5, "10"])
def test_invalid_batch_size(size):
    with pytest.raises(ValueError, match="batch_size"):
        MlflowMetricsHistoryDataset(batch_size=size)


def test_bounded_ordered_synchronous_batches(mocker):
    client = mocker.patch(f"{MODULE}.MlflowClient").return_value
    mocker.patch(f"{MODULE}.time", side_effect=[1, 2, 3, 4, 5])
    data = {"score": [{"step": i, "value": i / 10} for i in range(5)]}
    MlflowMetricsHistoryDataset(run_id="run", prefix="cv", batch_size=2).save(data)
    batches = [call.kwargs["metrics"] for call in client.log_batch.call_args_list]
    assert [len(batch) for batch in batches] == [2, 2, 1]
    metrics = [metric for batch in batches for metric in batch]
    assert [(m.key, m.value, m.step) for m in metrics] == [
        ("cv.score", i / 10, i) for i in range(5)
    ]
    assert [m.timestamp for m in metrics] == [1000, 2000, 3000, 4000, 5000]
    assert all(call.args == ("run",) for call in client.log_batch.call_args_list)
    assert all(call.kwargs["synchronous"] for call in client.log_batch.call_args_list)
    client.log_metric.assert_not_called()


def test_default_remains_individual(mocker):
    client = mocker.patch(f"{MODULE}.MlflowClient").return_value
    dataset = MlflowMetricsHistoryDataset(run_id="run")
    dataset.save({"score": [{"step": i, "value": i} for i in range(3)]})
    assert client.log_metric.call_count == 3
    client.log_batch.assert_not_called()
    assert "batch_size" not in dataset._describe()


def test_maximum_batch_boundary(mocker):
    client = mocker.patch(f"{MODULE}.MlflowClient").return_value
    dataset = MlflowMetricsHistoryDataset(run_id="run", batch_size=1000)
    dataset.save({"score": [{"step": i, "value": i} for i in range(1001)]})
    assert [
        len(call.kwargs["metrics"]) for call in client.log_batch.call_args_list
    ] == [1000, 1]


def test_invalid_metric_does_not_create_implicit_run(mocker):
    mocker.patch(f"{MODULE}.MlflowClient")
    mocker.patch(f"{MODULE}.mlflow.active_run", return_value=None)
    start = mocker.patch(f"{MODULE}.mlflow.start_run")
    with pytest.raises(DatasetError, match="Unexpected metric value"):
        MlflowMetricsHistoryDataset(batch_size=100).save({"score": 1})
    start.assert_not_called()


def test_disabled_and_empty_do_not_create_run(mocker):
    client = mocker.patch(f"{MODULE}.MlflowClient").return_value
    mocker.patch(f"{MODULE}.mlflow.active_run", return_value=None)
    start = mocker.patch(f"{MODULE}.mlflow.start_run")
    dataset = MlflowMetricsHistoryDataset(batch_size=2)
    dataset.save({})
    dataset._logging_activated = False
    dataset.save({"score": {"step": 1, "value": 2}})
    start.assert_not_called()
    client.log_batch.assert_not_called()


def test_partial_failure_is_propagated_without_retry(mocker):
    client = mocker.patch(f"{MODULE}.MlflowClient").return_value
    client.log_batch.side_effect = [None, RuntimeError("store failed")]
    dataset = MlflowMetricsHistoryDataset(run_id="run", batch_size=2)
    with pytest.raises(DatasetError, match="store failed"):
        dataset.save({"score": [{"step": i, "value": i} for i in range(6)]})
    assert client.log_batch.call_count == 2


@pytest.mark.parametrize("explicit_run", [False, True])
def test_offline_store_preserves_history(mlflow_client, explicit_run):
    if explicit_run:
        run_id = mlflow.start_run().info.run_id
        mlflow.end_run()
    else:
        run_id = None
    dataset = MlflowMetricsHistoryDataset(run_id=run_id, prefix="cv", batch_size=2)
    data = {
        "score": [
            {"step": 4, "value": 0.25},
            {"step": 2, "value": float("nan")},
            {"step": 4, "value": float("inf")},
            {"step": 5, "value": -float("inf")},
        ]
    }
    dataset.save(data)
    history = mlflow_client.get_metric_history(dataset.run_id, "cv.score")
    assert [metric.step for metric in history] == [4, 2, 4, 5]
    assert history[0].value == 0.25
    assert math.isnan(history[1].value)
    assert math.isinf(history[2].value) and history[2].value > 0
    assert math.isinf(history[3].value) and history[3].value < 0
    assert all(metric.timestamp > 0 for metric in history)


def test_implicit_run_is_created_once(mocker):
    client = mocker.patch(f"{MODULE}.MlflowClient").return_value
    mocker.patch(f"{MODULE}.mlflow.active_run", return_value=None)
    start = mocker.patch(f"{MODULE}.mlflow.start_run")
    start.return_value.info.run_id = "new_run"
    MlflowMetricsHistoryDataset(batch_size=1).save(
        {"score": [{"step": i, "value": i} for i in range(3)]}
    )
    start.assert_called_once_with()
    assert all(call.args == ("new_run",) for call in client.log_batch.call_args_list)
