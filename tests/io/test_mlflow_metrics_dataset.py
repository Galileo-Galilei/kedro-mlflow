from typing import Dict, List, Optional, Union

import mlflow
import pytest
from mlflow.tracking import MlflowClient
from pytest_lazyfixture import lazy_fixture

from kedro_mlflow.io import MlflowMetricsDataSet


def assert_are_metrics_logged(
    data: Dict[str, Union[float, List[float]]],
    client: MlflowClient,
    run_id: str,
    prefix: Optional[str] = None,
) -> bool:
    """Helper function which checks if given metrics where logged.

    Args:
        data: (Dict[str, Union[float, List[float]]]): Logged metrics.
        client: (MlflowClient): MLflow client instance.
        run_id: (str): id of run where data was logged.
        prefix: (Optional[str])
    """
    for key in data.keys():
        metric_key = f"{prefix}.{key}" if prefix else key
        metric = client.get_metric_history(run_id, metric_key)
        data_len = len(data[key]) if isinstance(data[key], list) else 1
        assert len(metric) == data_len
        for idx, item in enumerate(metric):
            data_value = (
                data[key][idx]["value"]
                if isinstance(data[key], list)
                else data[key]["value"]
            )
            assert item.value == data_value and item.key == metric_key
    assert True


@pytest.fixture
def tracking_uri(tmp_path):
    return tmp_path / "mlruns"


@pytest.fixture
def metrics():
    return {
        "metric1": {"step": 0, "value": 1.1},
        "metric2": {"step": 0, "value": 1.2},
    }


@pytest.fixture
def metrics2():
    return {
        "metric1": [
            {"step": 0, "value": 1.1},
            {"step": 1, "value": 1.2},
            {"step": 2, "value": 1.3},
        ],
        "metric2": {"step": 0, "value": 1.2},
        "metric3": {"step": 0, "value": 1.4},
    }


@pytest.fixture
def metrics3():
    return {"metric1": {"step": 0, "value": 1.1}}


@pytest.mark.parametrize(
    "data, prefix",
    [
        (lazy_fixture("metrics"), None),
        (lazy_fixture("metrics"), "test"),
        (lazy_fixture("metrics2"), None),
        (lazy_fixture("metrics2"), "test"),
        (lazy_fixture("metrics3"), None),
        (lazy_fixture("metrics3"), "test"),
    ],
)
def test_mlflow_metrics_dataset_saved_and_logged(tmp_path, tracking_uri, data, prefix):
    """Check if MlflowMetricsDataSet can be saved in catalog when filepath is given,
    and if logged in mlflow.
    """
    mlflow.set_tracking_uri(tracking_uri.as_uri())
    mlflow_client = MlflowClient(tracking_uri=tracking_uri.as_uri())
    mlflow_metrics_dataset = MlflowMetricsDataSet(prefix=prefix)

    with mlflow.start_run():
        run_id = mlflow.active_run().info.run_id
        mlflow_metrics_dataset.save(data)

        # Check if metrics where logged corectly in MLflow.
        assert_are_metrics_logged(data, mlflow_client, run_id, prefix)

    # Check if metrics are stored in catalog.
    catalog_metrics = MlflowMetricsDataSet(
        prefix=prefix,
        # Run id needs to be provided as there is no active run.
        run_id=run_id,
    ).load()

    assert len(catalog_metrics) == len(data)
    for k in catalog_metrics.keys():
        data_key = k.split(".")[-1] if prefix is not None else k
        assert data[data_key] == catalog_metrics[k]
