from typing import Dict, List, Optional, Union

import mlflow
import pytest
from kedro.io.core import DataSetError
from mlflow.tracking import MlflowClient
from pytest_lazyfixture import lazy_fixture

from kedro_mlflow.io import MlflowMetricsDataSet


def are_metrics_logged(
    data: Dict[str, Union[float, List[float]]],
    mlflow_client: MlflowClient,
    run_id: str,
    prefix: Optional[str] = None,
) -> bool:
    """Helper function which checks if given metrics where logged.

    Args:
        data: (Dict[str, Union[float, List[float]]]): Logged metrics.
        mlflow_client: (MlflowClient): MLflow client instance.
        run_id: (str): id of run where data was logged.
        prefix: (Optional[str])

    Returns:
        bool: Was data logged in MLflow?
    """
    for key in data.keys():
        metric_key = f"{prefix}.{key}" if prefix else key
        metric = mlflow_client.get_metric_history(run_id, metric_key)
        if not len(metric) == (len(data[key]) if isinstance(data[key], list) else 1):
            return False
        for idx, item in enumerate(metric):
            if not (
                (
                    item.value
                    == (data[key][idx] if isinstance(data[key], list) else data[key])
                )
                and item.key == metric_key
            ):
                return False
    return True


@pytest.fixture
def tracking_uri(tmp_path):
    return tmp_path / "mlruns"


@pytest.fixture
def metrics():
    return {"metric1": 1.1, "metric2": 1.2}


@pytest.fixture
def metric_with_multiple_values():
    return {"metric1": [1.1, 1.2, 1.3]}


@pytest.fixture
def metrics_with_one_and_multiple_values():
    return {"metric1": [1.1, 1.2, 1.3], "metric2": 1.2}


@pytest.mark.parametrize(
    "data, prefix, format",
    [
        (lazy_fixture("metrics"), None, None),
        (lazy_fixture("metrics"), None, "csv"),
        (lazy_fixture("metrics"), "test", "json"),
        (lazy_fixture("metric_with_multiple_values"), None, "json"),
        (lazy_fixture("metric_with_multiple_values"), None, "csv"),
        (lazy_fixture("metrics_with_one_and_multiple_values"), None, "json"),
        (lazy_fixture("metrics_with_one_and_multiple_values"), "test", "json"),
        (lazy_fixture("metrics_with_one_and_multiple_values"), "test", "csv"),
    ],
)
def test_mlflow_metrics_dataset_saved_and_logged(
    tmp_path, tracking_uri, data, prefix, format
):
    """Check if MlflowMetricsDataSet can be saved in catalog when filepath is given,
    and if logged in mlflow.
    """
    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_client = MlflowClient(tracking_uri=tracking_uri.as_uri())
    filepath = tmp_path / "data.json"
    if format:
        mlflow_metrics_dataset = MlflowMetricsDataSet(
            filepath=filepath, prefix=prefix, format=format
        )
    else:
        mlflow_metrics_dataset = MlflowMetricsDataSet(filepath=filepath, prefix=prefix)

    with mlflow.start_run():
        mlflow_metrics_dataset.save(data)
        run_id = mlflow.active_run().info.run_id

    # Check if metrics where logged corectly in MLflow.
    assert are_metrics_logged(data, mlflow_client, run_id, prefix)

    # Check if metrics are stored in catalog.

    catalog_metrics = mlflow_metrics_dataset.load()

    assert len(catalog_metrics) == len(data)

    for k in catalog_metrics.keys():
        assert data[k] == catalog_metrics[k]


@pytest.mark.parametrize(
    "data",
    [
        lazy_fixture("metrics"),
        lazy_fixture("metric_with_multiple_values"),
        lazy_fixture("metrics_with_one_and_multiple_values"),
    ],
)
def test_mlflow_metrics_dataset_without_filepath(tmp_path, tracking_uri, data):
    """Check if saved mlflow metrics dataset is logged in mlflow and cannot be
    load with catalog.
    """
    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_client = MlflowClient(tracking_uri=tracking_uri.as_uri())

    mlflow_metrics_dataset = MlflowMetricsDataSet()

    with mlflow.start_run():
        mlflow_metrics_dataset.save(data)
        run_id = mlflow.active_run().info.run_id

    # Check if metrics where logged corectly in MLflow.
    assert are_metrics_logged(data, mlflow_client, run_id)

    # Check if metrics are stored in catalog.
    with pytest.raises(DataSetError):
        mlflow_metrics_dataset.load()
