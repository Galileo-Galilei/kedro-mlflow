# ``Hooks``

This package provides 1 new hook.

## ``MlflowHook``

This hook :

  1. manages mlflow settings at the beginning and the end of the run (run start / end).
  2. autolog nodes parameters each time the pipeline is run (with ``kedro run`` or programatically).
  3. log useful informations for reproducibility as ``mlflow tags`` (including kedro ``Journal`` information for old kedro versions and the commands used to launch the run).
  4. register the pipeline as a valid ``mlflow model`` if [it is a ``PipelineML`` instance](./03_Pipelines.md)
