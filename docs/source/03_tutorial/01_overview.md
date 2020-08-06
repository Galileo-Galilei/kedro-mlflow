# Scope
## In the scope of the tutorial
This tutorial adresses the following items:
1. How to include ``kedro-mlflow`` capabilities in a Kedro project:
    1. [create a new kedro project](./02_setup.md) with updated template
    2. [update an existing kedro project](./02_setup.md)
2. [Configure mlflow](./03_configuration.md) inside a "mlflow initialised" Kedro project
3. Version and track objects during execution with mlflow:
    1. [Version parameters](./04_version_parameters.md) inside a Kedro project
    2. [Version data](./05_version_datasets.md) inside a Kedro project
    3. **(COMING in 0.3.0)** [Version machine learning models](./06_version_models.md) inside a Kedro project
    4. **(COMING in 0.3.0)** [Version metrics](./07_version_metrics.md) inside a Kedro project
    5. [Open mlflow ui](./08_mlflow_ui.md) with project configuration
    6. [Package and serve a Kedro pipeline](./09_pipeline_packaging.md)

This is a step by step tutorial and it is recommended to read the different chapters above order, but not mandatory.

## Out of scope of the tutorial
Some advanced capabilities are adressed in the [advanced use section](../04_advanced_use/01_run_with_mlproject.md):
- **(COMING in 0.3.0)** launching a Kedro project directly with mlflow through the ``MLProject`` file.
