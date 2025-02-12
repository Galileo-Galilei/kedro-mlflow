from kedro_mlflow.io.artifacts.mlflow_artifact_dataset import (
    _is_instance_mlflow_artifact_dataset,
)


def add_run_id_to_artifact_datasets(catalog, run_id: str):
    for name, dataset in catalog._datasets.items():
        if (_is_instance_mlflow_artifact_dataset(dataset)) and (dataset.run_id is None):
            catalog._datasets[name].run_id = run_id
