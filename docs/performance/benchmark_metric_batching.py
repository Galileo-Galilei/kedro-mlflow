"""Synthetic offline benchmark; tracking artifacts stay in a temporary directory."""

import argparse
import json
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory
from time import perf_counter, sleep
from unittest.mock import patch

import mlflow
from mlflow.tracking import MlflowClient

from kedro_mlflow.io.metrics import MlflowMetricsHistoryDataset

MODULE = "kedro_mlflow.io.metrics.mlflow_metrics_history_dataset"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--observations", type=int, default=1000)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--latency-ms", type=float, default=1.0)
    args = parser.parse_args()
    data = {
        "synthetic_score": [
            {"step": i, "value": i / args.observations}
            for i in range(args.observations)
        ]
    }
    results = []
    for batch_size in [None, 100]:
        elapsed = []
        calls = []
        for _ in range(args.repeats):
            with patch(f"{MODULE}.MlflowClient") as factory:
                client = factory.return_value
                client.log_metric.side_effect = lambda *a, **k: sleep(
                    args.latency_ms / 1000
                )
                client.log_batch.side_effect = lambda *a, **k: sleep(
                    args.latency_ms / 1000
                )
                dataset = MlflowMetricsHistoryDataset(
                    run_id="synthetic", batch_size=batch_size
                )
                start = perf_counter()
                dataset.save(data)
                elapsed.append(perf_counter() - start)
                calls.append(client.log_metric.call_count + client.log_batch.call_count)
        results.append(
            {
                "store": "mock_latency",
                "batch_size": batch_size,
                "median_seconds": median(elapsed),
                "calls": calls,
            }
        )
    with TemporaryDirectory(prefix="kedro_mlflow_bench_") as temp:
        mlflow.set_tracking_uri((Path(temp) / "mlruns").as_uri())
        for batch_size in [None, 100]:
            elapsed = []
            for _ in range(args.repeats):
                with mlflow.start_run() as run:
                    dataset = MlflowMetricsHistoryDataset(
                        run_id=run.info.run_id, batch_size=batch_size
                    )
                    start = perf_counter()
                    dataset.save(data)
                    elapsed.append(perf_counter() - start)
                    history = MlflowClient().get_metric_history(
                        run.info.run_id, "synthetic_score"
                    )
                    assert [(m.step, m.value) for m in history] == [
                        (i, i / args.observations) for i in range(args.observations)
                    ]
            results.append(
                {
                    "store": "local_file",
                    "batch_size": batch_size,
                    "median_seconds": median(elapsed),
                    "seconds": elapsed,
                    "history_equivalent": True,
                }
            )
    print(
        json.dumps(
            {
                "observations": args.observations,
                "repeats": args.repeats,
                "latency_ms": args.latency_ms,
                "results": results,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
