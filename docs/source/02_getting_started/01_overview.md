# Scope
## In the scope of the tutorial
This tutorial adresses the following items:
1. How to include ``kedro-mlflow`` capabilities in a Kedro project:
    1. [create a new kedro project](./02_setup.md) with updated template
    2. [update an existing kedro project](./02_setup.md)
2. [Configure mlflow](./03_configuration.md) inside a Kedro project
3. Version and track objects during execution with mlflow:
    1. [Version parameters](./04_versioning_parameters.md) inside a Kedro project
    2. [Version data](./05_artifacts_tracking.md) inside a Kedro project
    3. **(COMING in 0.3.0)** [Version machine learning models](./06_models_tracking.md) inside a Kedro project
    4. **(COMING in 0.3.0)** [Version metrics](./07_metrics_tracking.md) inside a Kedro project
    5. [Open mlflow ui](./08_mlflow_ui.md) with project configuratio

This is a step by step tutorial and it is recommended to read the different chapters above order, but not mandatory.

## Out of scope of the tutorial
Some advanced capabilities are adressed in the [advanced use section](../03_advanced_use/01_pipeline_serving.md):
- saving a kedro pipeline as a mlflow model and serve it
- **(COMING in 0.3.0)** launching a Kedro project directly with mlflow trhough the ``MLProject`` file.
