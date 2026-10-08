# Opt-in synchronous metric history batching

`MlflowMetricsHistoryDataset` currently sends one `log_metric` call per history
observation. This change adds `batch_size` (integer 1–1000) to send bounded
`MlflowClient.log_batch(..., synchronous=True)` calls. `None`, the default, keeps
the existing individual logging path. No new dependencies are required.

```yaml
experiment_metrics:
  type: kedro_mlflow.io.metrics.MlflowMetricsHistoryDataset
  prefix: validation
  batch_size: 100
```

Keys, prefixes, values, steps and input traversal order are retained. Each
observation receives a millisecond timestamp when its Metric object is built;
batching changes the physical timing of transmission, so timestamps cannot be
identical to a separate individual-logging execution. The last partial batch
is flushed; empty input and disabled logging do not create a run. Implicit run
creation occurs only when a batch is ready and the run is reused.

Failures propagate without plugin retries, asynchronous submission or fallback.
Earlier batches may already be persisted when a later batch fails. Within-batch
partial persistence depends on the backend; this is not an all-history
transaction. MLflow's own backend/client retry policies are unchanged.

## Offline measurement (2026-10-08)

Source baseline: upstream commit `f4aa0a4d0aade5dc1824fa690f14877f3d2ed22d`
(2.0.3). Python 3.13.14, Kedro 1.7.0, MLflow 3.17.0, pytest 8.4.2,
scikit-learn 1.6.1. Workload: 1000 synthetic observations of one metric,
3 repetitions per configuration, batch size 100. Time covers dataset `save`
only; run creation and history readback are outside the timed interval.

| Backend | Individual median | Batch median | Ratio | Client logging calls |
| --- | ---: | ---: | ---: | --- |
| Local MLflow file store | 4.632277 s | 1.951734 s | 2.37× | 1000 → 10 |
| Artificial mock with requested 1 ms sleep/call | 2.014705 s | 0.019597 s | 102.80× | 1000 → 10 |

File-store individual repetitions: 4.126408, 4.769219, 4.632277 s; batched:
2.313984, 1.938590, 1.951734 s. All 1000 `(step, value)` pairs were compared
after each real-store repetition. The mock models artificial call overhead;
Windows sleep duration is not guaranteed to equal the requested duration.
The file store still writes individual points internally: 10 client calls do
not imply 10 physical writes or 10 measured HTTP requests.

Hardware inventory was obtained **after** these measurements: Intel Xeon Gold
6348 @ 2.60 GHz, virtual guest exposing 4 vCPUs; 16 GiB reported RAM
(17,178,677,248 bytes); Windows 11 Enterprise 10.0.26100 x64. The guest reports
a 200 GiB virtual SAS disk as SSD; its physical storage backend is unknown.
These are guest resources, not the full host capacity. No GPU workload was used.

66 metric tests passed, including 15 added cases covering bounds, final partial
batches, ordering, prefix/step/timestamps, NaN/±Inf, implicit/explicit runs,
empty/disabled input, invalid input and failure without retry. Ruff lint/format
and `git diff --check` passed. The full upstream matrix has not been run locally.
MLflow 3.17.0 disables file stores by default; the test process explicitly sets
`MLFLOW_ALLOW_FILE_STORE=true` to exercise the existing upstream fixtures.
The plugin does not change that setting.

## Reproduction

Use an isolated environment with the above versions to reproduce the recorded
configuration. From the repository root:

```powershell
$env:KEDRO_DISABLE_TELEMETRY = '1'
$env:DO_NOT_TRACK = '1'
$env:MLFLOW_ALLOW_FILE_STORE = 'true'
python -m pytest -o addopts='' tests/io/metrics
python docs/performance/benchmark_metric_batching.py --observations 1000 --repeats 3 --latency-ms 1
python -m ruff check kedro_mlflow/io/metrics/mlflow_metrics_history_dataset.py tests/io/metrics/test_metrics_history_batching.py docs/performance/benchmark_metric_batching.py
```

The benchmark uses only synthetic data and temporary local stores. No tracking
server, credentials, model training or publication is involved. This measures
tracking overhead, not model training speed. SQLite, HTTP, remote stores,
other MLflow versions and full-pipeline performance remain unmeasured. Pipelines
logging only a few final metrics should not expect the same improvement.
